"""
Route handlers untuk file upload - API v1
"""
from fastapi import APIRouter, UploadFile, File, Query
from services.upload_service import upload_file_to_perfect_corp

router = APIRouter(prefix="/v1/upload", tags=["V1 - File Upload"])


@router.post("")
async def upload_file(
    file: UploadFile = File(...),
    mode: str = Query(default="sd", regex="^(sd|hd)$", description="Resize mode: 'sd' (max 1920px) atau 'hd' (max 2560px)")
):
    """
    Endpoint untuk upload file gambar ke Perfect Corp API v1.1.
    
    Args:
        file: File gambar yang akan diupload (JPEG, JPG, atau PNG)
        mode: Mode resize - 'sd' (Standard Definition) atau 'hd' (High Definition)
              - sd: max 1920px (sisi terpanjang), min 480px (sisi pendek)
              - hd: max 2560px (sisi terpanjang), min 1080px (sisi pendek)
        
    Returns:
        Dict berisi file_id dan informasi upload
    """
    return await upload_file_to_perfect_corp(file, mode)
