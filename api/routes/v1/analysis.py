"""
Analysis routes untuk AI Skin Analysis - API v1
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from services.analysis_service import analyze_skin, check_task_status, poll_task_status

router = APIRouter(prefix="/v1/analyze", tags=["V1 - Analysis"])


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
    - **submodules**: List modul analisis (optional)
    
    **Returns:**
    - **task_id**: ID task untuk mengambil hasil analisis
    - **status**: Status request (success/error)
    - **message**: Pesan informatif
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
    Endpoint untuk memeriksa status analisis kulit dari Perfect Corp API v1.0.
    
    **Parameters:**
    - **task_id**: ID task yang dikembalikan dari endpoint /analyze
    
    **Returns:**
    - **status**: Status task (running/success/error)
    - **polling_interval**: Interval yang direkomendasikan untuk polling berikutnya (dalam ms)
    - **message**: Pesan informatif
    - **results**: Hasil analisis (jika status = success)
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
    
    **Parameters:**
    - **task_id**: ID task dari endpoint /analyze
    - **max_attempts**: Maksimal jumlah polling (default: 30 kali)
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
