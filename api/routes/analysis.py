"""
Analysis routes untuk AI Skin Analysis
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from services.analysis_service import analyze_skin, check_task_status, poll_task_status

router = APIRouter(prefix="/analyze", tags=["analysis"])


class AnalysisRequest(BaseModel):
    """Request body untuk skin analysis"""
    file_id: str = Field(..., description="ID file yang sudah diupload sebelumnya")
    request_id: int = Field(
        default=0, 
        description="Incremental request number. Request dengan ID sama akan diabaikan untuk prevent duplicate."
    )
    submodules: Optional[list[str]] = Field(
        default=None,
        description="List submodule analisis (default: semua HD modules)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_id": "pfNK5PuRe0MrwLHcGA3DOmB1ahwfXTbYHjv+KoBIxbE=",
                "request_id": 0,
                "submodules": [
                    "hd_wrinkle",
                    "hd_pore",
                    "hd_texture",
                    "hd_acne",
                    "hd_age_spot",
                    "hd_redness",
                    "hd_oiliness",
                    "hd_firmness"
                ]
            }
        }


class PollTaskRequest(BaseModel):
    """Request body untuk polling task status"""
    task_id: str = Field(..., description="Task ID yang didapat dari endpoint /analyze")
    max_attempts: int = Field(
        default=30,
        description="Maksimal jumlah polling attempts (default: 30)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "SX9ALF1Z+KIiNa+GaFRp4bI5gijoc/ckI2teebLq35Bo1Nwc++3iXXdKqnU4/LID",
                "max_attempts": 30
            }
        }


@router.post("")
async def analyze_image(request: AnalysisRequest):
    """
    Endpoint untuk melakukan AI Skin Analysis menggunakan Perfect Corp API v1.0.
    
    **Flow:**
    1. Client mengirim file_id dari gambar yang sudah diupload
    2. Server membuat task analysis di Perfect Corp dengan parameter yang diminta
    3. Perfect Corp mengembalikan task_id
    4. Client menggunakan task_id untuk mendapatkan hasil analisis
    
    **Parameters:**
    - **file_id**: ID file yang didapat dari endpoint /upload
    - **request_id**: Nomor request incremental (default: 0)
      - Request dengan request_id sama akan diabaikan untuk prevent duplicate
      - Gunakan request_id yang sama jika retry karena connection issue
      - Increment request_id jika ingin hasil berbeda untuk file_id yang sama
    - **submodules**: List modul analisis (optional)
      - Default: Semua HD modules (wrinkle, pore, texture, acne, dll)
      - Available modules:

        HD Skincare:

            "hd_redness": Measures skin redness severity.
            "hd_oiliness": Determines skin oiliness level.
            "hd_age_spot": Detects age spots and pigmentation.
            "hd_radiance": Evaluates skin radiance.
            "hd_moisture": Assesses skin hydration levels.
            "hd_dark_circle": Analyzes the presence of dark circles under the eyes.
            "hd_eye_bag": Detects eye bags.
            "hd_droopy_upper_eyelid": Measures upper eyelid drooping severity.
            "hd_droopy_lower_eyelid": Measures lower eyelid drooping severity.
            "hd_firmness": Evaluates skin firmness and elasticity.
            "hd_texture": Subcategories[whole]; Analyzes overall skin texture.
            "hd_acne": Subcategories[whole]; Detects acne presence.
            "hd_pore": Subcategories[forehead, nose, cheek, whole]; Detects and evaluates pores in different facial regions.
            "hd_wrinkle": Subcategories[forehead, glabellar, crowfeet, periocular, nasolabial, marionette, whole]; Measures the severity of wrinkles in various facial areas.

        SD Skincare:

          "wrinkle": General wrinkle analysis.
          "droopy_upper_eyelid": Measures upper eyelid drooping severity.
          "droopy_lower_eyelid": Measures lower eyelid drooping severity.
          "firmness": Evaluates skin firmness and elasticity.
          "acne": Evaluates acne presence.
          "moisture": Measures skin hydration.
          "eye_bag": Detects eye bags.
          "dark_circle_v2": Analyzes dark circles using an alternative method.
          "age_spot": Detects age spots.
          "radiance": Evaluates skin brightness.
          "redness": Measures skin redness.
          "oiliness": Determines skin oiliness.
          "pore": Measures pore visibility.
          "texture": Analyzes overall skin texture.
    
    **Returns:**
    - **task_id**: ID task untuk mengambil hasil analisis
    - **status**: Status request (success/error)
    - **message**: Pesan informatif
    
    **Error Responses:**
    - 400: Invalid file_id atau parameter
    - 401: Token expired (akan otomatis retry)
    - 404: File_id tidak ditemukan atau expired
    - 500: Server atau Perfect Corp API error
    - 504: Request timeout
    """
    try:
        result = await analyze_skin(
            file_id=request.file_id,
            request_id=request.request_id,
            submodules=request.submodules
        )
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/check_task_status")
async def check_analysis_status(
    task_id: str = Query(..., description="Task ID yang didapat dari endpoint /analyze")
):
    """
    Endpoint untuk memeriksa status analisis kulit dari Perfect Corp API.
    
    **Flow:**
    1. Client mengirim task_id yang didapat dari endpoint /analyze
    2. Server melakukan GET request ke Perfect Corp API
    3. Perfect Corp mengembalikan status task (running, success, atau error)
    
    **Parameters:**
    - **task_id**: ID task yang dikembalikan dari endpoint /analyze
    
    **Returns:**
    - **status**: Status task (running/success/error)
    - **polling_interval**: Interval yang direkomendasikan untuk polling berikutnya (dalam ms)
    - **message**: Pesan informatif
    - **results**: Hasil analisis (jika status = success)
    - **result_url**: URL file hasil analisis (jika tersedia)
    - **error_code**: Kode error (jika status = error)
    - **error_message**: Pesan error detail (jika status = error)
    
    **Status Explanation:**
    - **running**: Analisis masih dalam proses. Client harus polling lagi setelah `polling_interval` ms.
    - **success**: Analisis selesai. Hasil tersedia di field `results` dan `result_url`.
    - **error**: Analisis gagal. Detail error ada di `error_code` dan `error_message`.
    
    **Error Codes:**
    - exceed_max_filesize: File terlalu besar
    - invalid_image: Format gambar tidak valid
    - no_face_detected: Tidak ada wajah yang terdeteksi
    - poor_image_quality: Kualitas gambar kurang baik
    
    """
    try:
        result = await check_task_status(task_id)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.post("/poll_task_status")
async def poll_analysis_status(request: PollTaskRequest):
    """
    Endpoint untuk melakukan polling otomatis sampai task selesai.
    
    **PERHATIAN**: Endpoint ini akan blocking sampai task selesai atau timeout.
    Untuk production, lebih disarankan menggunakan `/check_task_status` 
    dan melakukan polling di client-side.
    
    **Flow:**
    1. Client mengirim task_id
    2. Server melakukan polling otomatis tiap 2 detik
    3. Server mengembalikan hasil final setelah task selesai (success/error)
    
    **Parameters:**
    - **task_id**: ID task dari endpoint /analyze
    - **max_attempts**: Maksimal jumlah polling (default: 30 kali)
    
    **Returns:**
    Hasil akhir analisis (sama seperti /check_task_status)
    
    **Timeout:**
    Request ini bisa memakan waktu lama (max_attempts * 2 detik).
    Jika timeout, gunakan endpoint /check_task_status untuk polling manual.
    
    """
    try:
        result = await poll_task_status(request.task_id, request.max_attempts)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )

