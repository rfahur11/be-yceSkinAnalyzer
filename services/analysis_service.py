"""
Analysis service untuk mengelola AI Skin Analysis dengan Perfect Corp API
"""
import requests
import logging
import asyncio
from fastapi import HTTPException
from config.settings import ANALYSIS_URL
from services.token_manager import token_manager

# Setup logging
logger = logging.getLogger(__name__)

# Analysis API endpoint
# ANALYSIS_URL sudah diambil langsung dari settings.py


async def analyze_skin(
    file_id: str,
    request_id: int = 0,
    submodules: list[str] = None
) -> dict:
    """
    Melakukan AI Skin Analysis menggunakan Perfect Corp API v1.0.
    
    Args:
        file_id: ID file yang sudah diupload sebelumnya
        request_id: Incremental request number (default: 0)
                   Request dengan request_id sama akan diabaikan server untuk prevent duplicate
        submodules: List submodule analisis yang diinginkan
                   Options: ["skin_type", "spots", "wrinkles", "dark_circles", 
                            "pores", "acne", "texture", "redness", "oiliness", 
                            "age_spot", "firmness"]
    
    Returns:
        Dict berisi task_id dan informasi analisis
    """
    try:
        # Default submodules jika tidak dispesifikasi
        if submodules is None:
            submodules = [
                "hd_wrinkle",      # Deteksi kerutan HD
                "hd_pore",         # Deteksi pori HD
                "hd_texture",      # Analisis tekstur kulit HD
                "hd_acne",         # Deteksi jerawat HD
                "hd_age_spot",     # Deteksi flek penuaan HD
                "hd_redness",      # Deteksi kemerahan HD
                "hd_oiliness",     # Analisis minyak kulit HD
                "hd_firmness"      # Analisis kekencangan kulit HD
            ]
        
        logger.info(f"Starting skin analysis for file_id: {file_id}")
        logger.info(f"Request ID: {request_id}, Submodules: {submodules}")
        
        # Step 1: Pastikan token valid
        access_token = await token_manager.ensure_valid_token()
        
        # Step 2: Prepare headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Step 3: Prepare request payload sesuai dokumentasi Perfect Corp
        # Menggunakan struktur payload yang lebih advanced dengan miniserver_args
        payload = {
            "request_id": request_id,
            "payload": {
                "file_sets": {
                    "src_ids": [file_id]  # File yang akan dianalisis
                },
                "actions": [
                    {
                        "id": 0,
                        "params": {},
                        "dst_actions": submodules,
                        "miniserver_args": {
                            # HD Wrinkle settings
                            "enable_dark_background_hd_wrinkle": True,
                            "color_dark_background_hd_wrinkle": "3D3D3D",
                            "opacity_dark_background_hd_wrinkle": 0.4,
                            
                            # HD Pore settings
                            "enable_dark_background_hd_pore": True,
                            "color_dark_background_hd_pore": "3D3D3D",
                            "opacity_dark_background_hd_pore": 0.4,
                            
                            # HD Acne settings
                            "enable_dark_background_hd_acne": True,
                            "color_dark_background_hd_acne": "3D3D3D",
                            "opacity_dark_background_hd_acne": 0.4,
                            
                            # HD Texture settings
                            "enable_dark_background_hd_texture": True,
                            "color_dark_background_hd_texture": "3D3D3D",
                            "opacity_dark_background_hd_texture": 0.4,
                            
                            # HD Oiliness settings
                            "enable_dark_background_hd_oiliness": True,
                            "color_dark_background_hd_oiliness": "3D3D3D",
                            "opacity_dark_background_hd_oiliness": 0.2,
                            
                            # HD Age Spot settings
                            "enable_dark_background_hd_age_spot": True,
                            "color_dark_background_hd_age_spot": "3D3D3D",
                            "opacity_dark_background_hd_age_spot": 0.2,
                            
                            # HD Redness settings
                            "enable_dark_background_hd_redness": True,
                            "color_dark_background_hd_redness": "3D3D3D",
                            "opacity_dark_background_hd_redness": 0.2,
                            
                            # HD Firmness settings
                            "enable_dark_background_hd_firmness": True,
                            "color_dark_background_hd_firmness": "3D3D3D",
                            "opacity_dark_background_hd_firmness": 0.1
                        }
                    }
                ]
            }
        }
        
        logger.info(f"Request URL: {ANALYSIS_URL}")
        logger.info(f"Request Headers: {headers}")
        logger.info(f"Request Payload: {payload}")
        
        # Step 4: Kirim request ke Perfect Corp API
        response = requests.post(
            ANALYSIS_URL,
            headers=headers,
            json=payload,
            timeout=30  # 30 detik timeout
        )
        
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        
        # Step 5: Handle response errors
        if response.status_code == 401:
            # Token invalid, coba refresh dan retry sekali
            logger.warning("Token invalid, refreshing token and retrying...")
            token_manager.invalidate_token()
            access_token = await token_manager.ensure_valid_token()
            headers["Authorization"] = f"Bearer {access_token}"
            
            # Retry request
            response = requests.post(
                ANALYSIS_URL,
                headers=headers,
                json=payload,
                timeout=30
            )
            
            logger.info(f"Retry Response Status Code: {response.status_code}")
            logger.info(f"Retry Response Body: {response.text}")
        
        if response.status_code == 400:
            error_detail = response.json() if response.text else "Bad request"
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request: {error_detail}. Periksa file_id atau parameter lainnya."
            )
        
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="File_id tidak ditemukan atau sudah kadaluarsa. Silakan upload ulang gambar."
            )
        
        if response.status_code >= 500:
            raise HTTPException(
                status_code=500,
                detail=f"Perfect Corp API error: {response.text}"
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error from Perfect Corp API: {response.text}"
            )
        
        # Step 6: Parse response
        analysis_data = response.json()
        
        # Perfect Corp API mengembalikan struktur:
        # {"status": 200, "result": {"task_id": "..."}}
        status = analysis_data.get("status")
        result = analysis_data.get("result", {})
        task_id = result.get("task_id")
        
        if status != 200 or not task_id:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Perfect Corp API: {analysis_data}"
            )
        
        logger.info(f"Analysis task created successfully. Task ID: {task_id}")
        
        # Step 7: Return hasil
        return {
            "status": "success",
            "message": "Skin analysis task berhasil dibuat",
            "task_id": task_id,
            "file_id": file_id,
            "request_id": request_id,
            "submodules": submodules,
            "note": "Gunakan task_id untuk mendapatkan hasil analisis"
        }
    
    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Request timeout. Perfect Corp API tidak merespon dalam waktu yang ditentukan."
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Network error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


async def check_task_status(task_id: str) -> dict:
    """
    Memeriksa status task analisis kulit dari Perfect Corp API.
    
    Args:
        task_id: ID task yang dikembalikan dari analyze_skin()
    
    Returns:
        Dict berisi status task dan hasil analisis (jika sudah selesai)
        
    Response structure:
        {
            "status": 200,
            "result": {
                "polling_interval": 1000,  # Interval polling dalam ms
                "status": "running" | "success" | "error",
                "error": "error_code",  # Jika ada error
                "error_message": "string",  # Pesan error
                "results": [...]  # Hasil analisis jika success
            }
        }
    """
    try:
        logger.info(f"Checking task status for task_id: {task_id}")
        
        # Step 1: Pastikan token valid
        access_token = await token_manager.ensure_valid_token()
        
        # Step 2: Prepare headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Step 3: Prepare URL dengan query parameter
        check_url = f"{ANALYSIS_URL}?task_id={task_id}"
        
        logger.info(f"Request URL: {check_url}")
        
        # Step 4: Kirim GET request ke Perfect Corp API
        response = requests.get(
            check_url,
            headers=headers
        )
        
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        
        # Step 5: Handle response errors
        if response.status_code == 401:
            # Token invalid, coba refresh dan retry sekali
            logger.warning("Token invalid, refreshing token and retrying...")
            token_manager.invalidate_token()
            access_token = await token_manager.ensure_valid_token()
            headers["Authorization"] = f"Bearer {access_token}"
            
            # Retry request
            response = requests.get(
                check_url,
                headers=headers,
                timeout=30
            )
            
            logger.info(f"Retry Response Status Code: {response.status_code}")
            logger.info(f"Retry Response Body: {response.text}")
        
        if response.status_code == 400:
            error_detail = response.json() if response.text else "Bad request"
            raise HTTPException(
                status_code=400,
                detail=f"Invalid task_id: {error_detail}"
            )
        
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="Task_id tidak ditemukan atau sudah kadaluarsa."
            )
        
        if response.status_code >= 500:
            raise HTTPException(
                status_code=500,
                detail=f"Perfect Corp API error: {response.text}"
            )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error from Perfect Corp API: {response.text}"
            )
        
        # Step 6: Parse response
        task_data = response.json()
        
        status = task_data.get("status")
        result = task_data.get("result", {})
        task_status = result.get("status")
        
        if status != 200:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Perfect Corp API: {task_data}"
            )
        
        # Step 7: Format response berdasarkan status
        response_data = {
            "task_id": task_id,
            "status": task_status,
            "polling_interval": result.get("polling_interval", 1000),
        }
        
        if task_status == "running":
            logger.info(f"Task {task_id} masih diproses")
            response_data["message"] = "Analisis kulit sedang diproses. Silakan cek kembali."
            
        elif task_status == "success":
            logger.info(f"Task {task_id} selesai dengan sukses")
            response_data["message"] = "Analisis kulit selesai!"
            response_data["results"] = result.get("results", [])
            
            # Extract URL hasil jika ada
            if response_data["results"]:
                first_result = response_data["results"][0]
                if "data" in first_result and first_result["data"]:
                    response_data["result_url"] = first_result["data"][0].get("url")
            
        elif task_status == "error":
            error_code = result.get("error", "unknown_error")
            error_message = result.get("error_message", "Unknown error occurred")
            logger.error(f"Task {task_id} failed: {error_code} - {error_message}")
            response_data["message"] = f"Analisis gagal: {error_message}"
            response_data["error_code"] = error_code
            response_data["error_message"] = error_message
        
        return response_data
    
    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Request timeout. Perfect Corp API tidak merespon dalam waktu yang ditentukan."
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during status check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Network error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during status check: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


async def poll_task_status(task_id: str, max_attempts: int = 30) -> dict:
    """
    Melakukan polling otomatis status task sampai selesai (success/error).
    
    Args:
        task_id: ID task yang dikembalikan dari analyze_skin()
        max_attempts: Maksimal jumlah polling (default: 30 kali)
    
    Returns:
        Dict berisi hasil akhir analisis
    """
    logger.info(f"Starting polling for task_id: {task_id}")
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Polling attempt {attempt}/{max_attempts}")
        
        # Check status
        status_data = await check_task_status(task_id)
        task_status = status_data.get("status")
        
        # Jika sudah selesai (success atau error), return hasilnya
        if task_status in ["success", "error"]:
            logger.info(f"Polling completed with status: {task_status}")
            return status_data
        
        # Jika masih running, tunggu sesuai polling_interval
        polling_interval = status_data.get("polling_interval", 2000)
        wait_seconds = polling_interval / 1000  # Convert ms to seconds
        
        logger.info(f"Task still running, waiting {wait_seconds} seconds...")
        await asyncio.sleep(wait_seconds)
    
    # Jika sudah max_attempts tapi masih belum selesai
    logger.warning(f"Polling timeout after {max_attempts} attempts")
    raise HTTPException(
        status_code=408,
        detail=f"Polling timeout: Task masih diproses setelah {max_attempts} percobaan"
    )

