"""
V2 routes untuk task/skin-analysis
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from services.analysis_service_v2 import create_analysis_task_v2, check_task_status_v2

router = APIRouter(prefix="/v2/task", tags=["V2 - Analysis"])


class AnalysisV2Request(BaseModel):
    src_file_url: Optional[str] = Field(None, description="URL gambar sumber (opsional)")
    src_file_id: Optional[str] = Field(None, description="File ID dari upload v2 (opsional)")
    dst_actions: Optional[list[str]] = Field(None, description="Daftar modul HD yang ingin dijalankan")
    miniserver_args: Optional[dict] = Field(None, description="Miniserver args untuk styling dan dark background")

    class Config:
        schema_extra = {
            "example": {
                "src_file_url": "https://example.com/selfie.jpg",
                "src_file_id": "pfNK5PuRe0MrwLHcGA3DOmB1ahwfXTbY=",
                "dst_actions": ["hd_wrinkle","hd_pore","hd_texture","hd_acne"],
                "miniserver_args": {
                    "enable_dark_background_hd_pore": True,
                    "color_dark_background_hd_pore": "3D3D3D",
                    "opacity_dark_background_hd_pore": 0.4
                }
            }
        }


@router.post("")
async def create_task(body: AnalysisV2Request):
    """
    Membuat analysis task v2.0 pada Perfect Corp.
    
    **Flow:**
    1. Client mengirim file URL atau file ID + dst_actions
    2. Server membuat task analysis di Perfect Corp v2.0
    3. Perfect Corp mengembalikan task_id
    4. Client menggunakan task_id untuk cek status
    
    **Parameters:**
    - **src_file_url**: URL gambar sumber (opsional, gunakan ini atau src_file_id)
    - **src_file_id**: File ID dari upload v2 (opsional, gunakan ini atau src_file_url)
    - **dst_actions**: List modul HD yang ingin dijalankan
    - **miniserver_args**: Konfigurasi miniserver (dark background, dll)
    
    **Returns:**
    - **status**: "success"
    - **task_id**: ID task untuk cek status
    
    **Example:**
    ```javascript
    const response = await fetch('/v2/task', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        src_file_url: 'https://example.com/selfie.jpg',
        dst_actions: ['hd_wrinkle', 'hd_pore', 'hd_texture', 'hd_acne'],
        miniserver_args: {
          enable_dark_background_hd_wrinkle: true,
          color_dark_background_hd_wrinkle: '3D3D3D',
          opacity_dark_background_hd_wrinkle: 0.4
        }
      })
    });
    const { task_id } = await response.json();
    ```
    """
    try:
        # Validate input: minimal salah satu src_file_url atau src_file_id harus ada
        if not body.src_file_url and not body.src_file_id:
            raise HTTPException(status_code=400, detail="src_file_url atau src_file_id harus disediakan")

        result = await create_analysis_task_v2(
            src_file_url=body.src_file_url,
            src_file_id=body.src_file_id,
            dst_actions=body.dst_actions,
            miniserver_args=body.miniserver_args
        )
        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}")
async def check_status(task_id: str):
    """
    Mengecek status task analysis v2.0.
    
    **Flow:**
    1. Client mengirim task_id yang didapat dari POST /v2/task
    2. Server melakukan GET request ke Perfect Corp v2.0
    3. Perfect Corp mengembalikan status task (running, success, atau error)
    
    **Parameters:**
    - **task_id**: ID task dari POST /v2/task
    
    **Returns:**
    - **task_id**: ID task
    - **task_status**: Status task (running/success/error)
    - **message**: Pesan informatif
    - **results**: Hasil analisis (jika success)
    - **result_url**: URL ZIP file hasil analisis (jika success)
    - **error_code**: Kode error (jika error)
    - **error_message**: Pesan error detail (jika error)
    
    **Task Status:**
    - **running**: Analisis masih dalam proses, client harus polling lagi
    - **success**: Analisis selesai, hasil tersedia di result_url
    - **error**: Analisis gagal, detail error di error_code dan error_message
    
    **Error Codes:**
    - **exceed_max_filesize**: File terlalu besar
    - **invalid_image**: Format gambar tidak valid
    - **no_face_detected**: Tidak ada wajah terdeteksi
    - **poor_image_quality**: Kualitas gambar kurang baik
    
    """
    try:
        result = await check_task_status_v2(task_id)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
