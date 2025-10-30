"""
Upload service untuk mengelola upload file ke Perfect Corp API
"""
import requests
import logging
from io import BytesIO
from PIL import Image
from fastapi import HTTPException, UploadFile
from config.settings import UPLOAD_URL, ALLOWED_FILE_TYPES
from services.token_manager import token_manager

# Setup logging
logger = logging.getLogger(__name__)


def resize_image(image: Image.Image, mode: str) -> tuple[Image.Image, dict]:
    """
    Resize gambar otomatis agar sesuai spesifikasi SD/HD sambil menjaga aspect ratio.
    Gambar akan selalu diresize jika tidak memenuhi kriteria, tidak akan ditolak.
    
    Args:
        image: PIL Image object
        mode: 'sd' atau 'hd'
        
    Returns:
        Tuple berisi (resized_image, resize_info)
    """
    # Dapatkan dimensi gambar asli
    original_width, original_height = image.size
    
    logger.info(f"Dimensi asli: {original_width}x{original_height}")
    
    # Tentukan batas resize berdasarkan mode
    if mode == "sd":
        max_long_side = 1920  # Sisi terpanjang maksimal
        min_short_side = 480  # Sisi pendek minimal
        mode_name = "SD (Standard Definition)"
    else:  # mode == "hd"
        max_long_side = 2560  # Sisi terpanjang maksimal
        min_short_side = 1080  # Sisi pendek minimal
        mode_name = "HD (High Definition)"
    
    # Tentukan sisi panjang dan pendek saat ini
    current_long_side = max(original_width, original_height)
    current_short_side = min(original_width, original_height)
    
    # Flag untuk tracking apakah perlu resize
    needs_resize = False
    scale_factor = 1.0
    
    # Logika 1: Cek apakah sisi pendek terlalu kecil (kurang dari minimum)
    if current_short_side < min_short_side:
        # Skala gambar agar sisi pendek = batas minimal
        scale_factor = min_short_side / current_short_side
        needs_resize = True
        logger.info(f"Sisi pendek ({current_short_side}px) < minimum ({min_short_side}px). Scale factor: {scale_factor:.2f}")
    
    # Logika 2: Cek apakah sisi panjang terlalu besar (lebih dari maksimum)
    elif current_long_side > max_long_side:
        # Skala gambar agar sisi panjang = batas maksimal
        scale_factor = max_long_side / current_long_side
        needs_resize = True
        logger.info(f"Sisi panjang ({current_long_side}px) > maksimum ({max_long_side}px). Scale factor: {scale_factor:.2f}")
    
    # Logika 3: Jika sudah sesuai spesifikasi, tidak perlu resize
    else:
        logger.info(f"Gambar sudah sesuai spesifikasi {mode_name}")
        resize_info = {
            "resized": False,
            "original_size": f"{original_width}x{original_height}",
            "final_size": f"{original_width}x{original_height}",
            "mode": mode_name,
            "reason": "Gambar sudah sesuai spesifikasi"
        }
        return image, resize_info
    
    # Hitung dimensi baru berdasarkan scale_factor
    new_width = int(original_width * scale_factor)
    new_height = int(original_height * scale_factor)
    
    # Pastikan dimensi baru tidak melebihi batas
    # Double check untuk edge cases
    new_long_side = max(new_width, new_height)
    new_short_side = min(new_width, new_height)
    
    # Jika setelah scaling masih melebihi batas panjang, adjust lagi
    if new_long_side > max_long_side:
        adjustment_factor = max_long_side / new_long_side
        new_width = int(new_width * adjustment_factor)
        new_height = int(new_height * adjustment_factor)
        logger.info(f"Adjustment untuk memastikan long side <= {max_long_side}")
    
    # Jika setelah scaling sisi pendek masih kurang, adjust lagi
    if new_short_side < min_short_side:
        adjustment_factor = min_short_side / new_short_side
        new_width = int(new_width * adjustment_factor)
        new_height = int(new_height * adjustment_factor)
        logger.info(f"Adjustment untuk memastikan short side >= {min_short_side}")
    
    # Buat copy dari image asli dan resize
    resized_image = image.copy()
    
    # Gunakan LANCZOS resampling untuk kualitas terbaik
    resized_image = resized_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    logger.info(f"Gambar diresize dari {original_width}x{original_height} ke {new_width}x{new_height}")
    
    # Determine resize reason
    if current_short_side < min_short_side:
        reason = f"Sisi pendek diperbesar dari {current_short_side}px ke {min(new_width, new_height)}px (min: {min_short_side}px)"
    else:
        reason = f"Sisi panjang diperkecil dari {current_long_side}px ke {max(new_width, new_height)}px (max: {max_long_side}px)"
    
    resize_info = {
        "resized": True,
        "original_size": f"{original_width}x{original_height}",
        "final_size": f"{new_width}x{new_height}",
        "scale_factor": round(scale_factor, 3),
        "mode": mode_name,
        "reason": reason
    }
    
    return resized_image, resize_info


async def upload_file_to_perfect_corp(file: UploadFile, mode: str = "sd") -> dict:
    """
    Upload file gambar ke Perfect Corp API dengan resize otomatis.
    
    Alur:
    1. Validasi file type
    2. Baca file dan convert ke PIL Image
    3. Resize gambar sesuai mode (sd/hd) sambil menjaga aspect ratio
    4. Convert kembali ke bytes
    5. Pastikan token valid (otomatis refresh jika tidak ada)
    6. Request upload_url dan file_id dari Perfect Corp dengan metadata file
    7. Upload file ke upload_url menggunakan PUT
    8. Return file_id dan informasi upload ke client
    
    Args:
        file: File gambar yang akan diupload
        mode: Mode resize - 'sd' (max 1920px) atau 'hd' (max 2560px)
        
    Returns:
        Dict berisi file_id dan informasi upload
    """
    try:
        # Step 1: Validasi file type
        if file.content_type not in ALLOWED_FILE_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"File type tidak didukung. Gunakan: {', '.join(ALLOWED_FILE_TYPES)}"
            )
        
        # Step 2: Baca file content
        original_file_content = await file.read()
        
        # Step 3: Convert ke PIL Image untuk diproses
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
        
        # Step 4: Resize gambar sesuai mode
        resized_image, resize_info = resize_image(image, mode)
        
        # Step 5: Convert resized image kembali ke bytes
        output_buffer = BytesIO()
        
        # Tentukan format output berdasarkan content_type
        if file.content_type == "image/png":
            # Untuk PNG, gunakan format PNG
            resized_image.save(output_buffer, format="PNG", optimize=True)
            final_content_type = "image/png"
        else:
            # Untuk JPEG/JPG, convert ke RGB dan save sebagai JPEG
            if resized_image.mode == 'RGBA':
                # Convert RGBA ke RGB untuk JPEG
                rgb_image = Image.new('RGB', resized_image.size, (255, 255, 255))
                rgb_image.paste(resized_image, mask=resized_image.split()[3])
                resized_image = rgb_image
            
            resized_image.save(output_buffer, format="JPEG", quality=95, optimize=True)
            final_content_type = "image/jpeg"
        
        # Dapatkan bytes dari buffer
        file_content = output_buffer.getvalue()
        file_size = len(file_content)
        
        logger.info(f"File size setelah resize: {file_size} bytes ({file_size / 1024:.2f} KB)")
        
        # Step 6: Pastikan token valid
        access_token = await token_manager.ensure_valid_token()
        
        # Step 7: Request upload_url dan file_id dari Perfect Corp dengan metadata file
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Payload dengan informasi file sesuai dokumentasi API
        payload = {
            "files": [
                {
                    "content_type": final_content_type,
                    "file_name": file.filename,
                    "file_size": file_size
                }
            ]
        }
        
        # Request untuk mendapatkan upload URL
        upload_request_response = requests.post(
            UPLOAD_URL,
            headers=headers,
            json=payload
        )
        
        # Handle error response
        if upload_request_response.status_code == 401:
            # Token mungkin invalid, coba refresh dan retry
            token_manager.invalidate_token()
            access_token = await token_manager.ensure_valid_token()
            headers["Authorization"] = f"Bearer {access_token}"
            
            upload_request_response = requests.post(
                UPLOAD_URL,
                headers=headers,
                json=payload
            )
        
        if upload_request_response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Upload endpoint not found"
            )
        elif upload_request_response.status_code >= 500:
            raise HTTPException(
                status_code=500,
                detail=f"Perfect Corp API error: {upload_request_response.text}"
            )
        elif upload_request_response.status_code != 200:
            raise HTTPException(
                status_code=upload_request_response.status_code,
                detail=f"Error requesting upload URL: {upload_request_response.text}"
            )
        
        # Parse response untuk mendapatkan upload_url dan file_id
        upload_data = upload_request_response.json()
        
        # Perfect Corp API mengembalikan struktur: 
        # {"status": 200, "result": {"files": [{"file_id": "...", "requests": [{"method": "PUT", "url": "...", "headers": {...}}]}]}}
        result = upload_data.get("result", {})
        files = result.get("files", [])
        
        if not files or len(files) == 0:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Perfect Corp API: no files in response. Response: {upload_data}"
            )
        
        file_info = files[0]
        file_id = file_info.get("file_id")
        requests_info = file_info.get("requests", [])
        
        if not file_id:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Perfect Corp API: missing file_id. Response: {upload_data}"
            )
        
        if not requests_info or len(requests_info) == 0:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Perfect Corp API: no upload requests in response. Response: {upload_data}"
            )
        
        # Ambil URL dan headers dari requests[0]
        upload_request = requests_info[0]
        upload_url = upload_request.get("url")
        upload_request_headers = upload_request.get("headers", {})
        
        if not upload_url:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Perfect Corp API: missing upload URL. Response: {upload_data}"
            )
        
        # Step 4: Upload file ke upload_url menggunakan PUT
        # Gunakan headers yang disediakan oleh API (Content-Type dan Content-Length)
        upload_headers = upload_request_headers.copy() if upload_request_headers else {}
        
        # Pastikan Content-Type dan Content-Length sudah sesuai
        if "Content-Type" not in upload_headers:
            upload_headers["Content-Type"] = file.content_type
        if "Content-Length" not in upload_headers:
            upload_headers["Content-Length"] = str(file_size)
        
        upload_response = requests.put(
            upload_url,
            data=file_content,
            headers=upload_headers
        )
        
        # Handle error saat upload
        if upload_response.status_code >= 400:
            raise HTTPException(
                status_code=upload_response.status_code,
                detail=f"Error uploading file: {upload_response.text}"
            )
        
        # Step 5: Return file_id dan informasi sukses
        return {
            "file_id": file_id,
            "filename": file.filename,
            "content_type": final_content_type,
            "size": file_size,
            "resize_info": resize_info,
            "message": "File berhasil diupload",
            "upload_status": "success"
        }
    
    except HTTPException:
        raise
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Network error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during upload: {str(e)}"
        )
