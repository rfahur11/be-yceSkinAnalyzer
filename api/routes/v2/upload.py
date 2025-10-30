"""
Route handlers untuk file upload - API v2.0
"""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from io import BytesIO
from PIL import Image
from services.upload_service_v2 import request_upload_url_v2, upload_to_presigned_url
from services.upload_service import resize_image
from config.settings import ALLOWED_FILE_TYPES, MAX_FILE_SIZE

# Setup logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v2/upload", tags=["V2 - File Upload"])


class UploadUrlRequest(BaseModel):
    """Request body untuk mendapatkan presigned upload URL"""
    file_name: str = Field(..., description="Nama file (contoh: my-selfie.jpg)")
    content_type: str = Field(..., description="MIME type (contoh: image/jpg, image/jpeg, image/png)")
    file_size: int = Field(..., description="Ukuran file dalam bytes", gt=0)
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_name": "my-selfie.jpg",
                "content_type": "image/jpg",
                "file_size": 50000
            }
        }


@router.post("/request-url")
async def get_upload_url(request: UploadUrlRequest):
    """
    Endpoint untuk mendapatkan presigned upload URL dari Perfect Corp API v2.0.
    
    **Flow v2.0:**
    1. Client request presigned URL dengan metadata file (name, type, size)
    2. Server request ke Perfect Corp dan mendapat presigned URL
    3. Client upload file langsung ke presigned URL (tidak melalui server)
    4. Client menggunakan file_id untuk analisis
    
    **Keuntungan v2.0:**
    - Upload lebih cepat (langsung ke storage)
    - Server tidak perlu handle file upload
    - Mengurangi bandwidth server
    
    **Parameters:**
    - **file_name**: Nama file yang akan diupload
    - **content_type**: MIME type (image/jpg, image/jpeg, image/png)
    - **file_size**: Ukuran file dalam bytes (max 10MB)
    
    **Returns:**
    - **file_id**: ID untuk digunakan dalam analisis
    - **upload_url**: Presigned URL untuk upload
    - **upload_method**: HTTP method (biasanya PUT)
    - **upload_headers**: Headers yang harus digunakan saat upload
    - **image_url**: URL gambar untuk digunakan di analysis v2 (src_file_url)
    
    **Example Frontend Usage:**
    ```javascript
    // Step 1: Request presigned URL
    const file = document.querySelector('input[type="file"]').files[0];
    
    const requestBody = {
      file_name: file.name,
      content_type: file.type,
      file_size: file.size
    };
    
    const response = await fetch('http://localhost:8000/v2/upload/request-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    });
    
    const data = await response.json();
    const { file_id, upload_url, upload_headers, image_url } = data;
    
    // Step 2: Upload file to presigned URL
    await fetch(upload_url, {
      method: 'PUT',
      headers: upload_headers,
      body: file
    });
    
    // Step 3: Create analysis task with file_id or image_url
    const analysisResp = await fetch('http://localhost:8000/v2/task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        src_file_id: file_id,  // or use src_file_url: image_url
        dst_actions: ['hd_wrinkle', 'hd_pore', 'hd_texture']
      })
    });
    
    const analysisData = await analysisResp.json();
    console.log('Analysis task created! Task ID:', analysisData.task_id);
    ```
    """
    try:
        # Validate content type
        if request.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Content type tidak didukung. Allowed: {', '.join(ALLOWED_FILE_TYPES)}"
            )
        
        # Validate file size
        if request.file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File terlalu besar. Max size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Request presigned URL
        result = await request_upload_url_v2(
            file_name=request.file_name,
            content_type=request.content_type,
            file_size=request.file_size
        )
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/direct")
async def upload_file_direct(
    file: UploadFile = File(...),
    mode: str = Query(default="sd", description="Mode resize: 'sd' (max 1920px) atau 'hd' (max 2560px)")
):
    """
    Endpoint alternatif untuk upload file langsung melalui server dengan preprocessing.
    
    **Flow:**
    1. Client upload file ke server ini
    2. Server melakukan preprocessing: resize gambar sesuai mode (SD/HD)
    3. Server request presigned URL dari Perfect Corp
    4. Server upload processed file ke presigned URL
    5. Server return file_id dan resize info ke client
    
    **Preprocessing:**
    - **SD Mode** (default): Max 1920px sisi panjang, min 480px sisi pendek
    - **HD Mode**: Max 2560px sisi panjang, min 1080px sisi pendek
    - Aspect ratio dijaga
    - Kualitas dioptimalkan (JPEG quality 95%, PNG optimized)
    
    **Note:** 
    - Endpoint ini kurang efisien dibanding /request-url karena file melewati server
    - Namun preprocessing dilakukan server-side untuk memastikan kualitas optimal
    
    **Parameters:**
    - **file**: File gambar (JPEG, JPG, atau PNG, max 10MB sebelum resize)
    - **mode**: Mode resize ('sd' atau 'hd')
    
    **Returns:**
    - **file_id**: ID untuk digunakan dalam analisis
    - **image_url**: URL gambar untuk analysis v2
    - **resize_info**: Informasi tentang preprocessing yang dilakukan
    - **message**: Status message
    """
    try:
        # Validate content type
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Tipe file tidak didukung. Allowed: {', '.join(ALLOWED_FILE_TYPES)}"
            )
        
        # Validate mode
        if mode not in ["sd", "hd"]:
            raise HTTPException(
                status_code=400,
                detail="Mode harus 'sd' atau 'hd'"
            )
        
        # Read file content
        original_file_content = await file.read()
        original_size = len(original_file_content)
        
        # Validate file size before processing
        if original_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File terlalu besar. Max size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )
        
        # Step 1: Preprocessing - Convert ke PIL Image
        try:
            image = Image.open(BytesIO(original_file_content))
            
            # Pastikan image dalam mode RGB untuk kompatibilitas
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
                
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"File bukan gambar yang valid atau corrupt: {str(e)}"
            )
        
        # Step 2: Resize gambar sesuai mode
        resized_image, resize_info = resize_image(image, mode)
        
        # Step 3: Convert resized image kembali ke bytes
        output_buffer = BytesIO()
        
        # Tentukan format output berdasarkan content_type
        if file.content_type == "image/png":
            resized_image.save(output_buffer, format="PNG", optimize=True)
            final_content_type = "image/png"
        else:
            # Untuk JPEG/JPG, convert ke RGB jika perlu
            if resized_image.mode == 'RGBA':
                rgb_image = Image.new('RGB', resized_image.size, (255, 255, 255))
                rgb_image.paste(resized_image, mask=resized_image.split()[3])
                resized_image = rgb_image
            
            resized_image.save(output_buffer, format="JPEG", quality=95, optimize=True)
            final_content_type = "image/jpeg"
        
        # Dapatkan bytes dari buffer
        processed_content = output_buffer.getvalue()
        processed_size = len(processed_content)
        
        logger.info(f"File size: original={original_size} bytes, processed={processed_size} bytes")
        
        # Step 4: Request presigned URL dengan ukuran file yang sudah diproses
        upload_data = await request_upload_url_v2(
            file_name=file.filename or "upload.jpg",
            content_type=final_content_type,
            file_size=processed_size
        )
        
        # Step 5: Upload processed file ke presigned URL
        await upload_to_presigned_url(
            presigned_url=upload_data["upload_url"],
            file_content=processed_content,
            headers=upload_data["upload_headers"]
        )
        
        # Step 6: Return file_id, image_url, dan resize info
        return {
            "success": True,
            "file_id": upload_data["file_id"],
            "file_name": upload_data["file_name"],
            "content_type": final_content_type,
            "original_size": original_size,
            "processed_size": processed_size,
            "resize_info": resize_info,
            "image_url": upload_data.get("image_url"),  # URL gambar untuk analysis
            "message": "File berhasil diupload dengan preprocessing"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )
