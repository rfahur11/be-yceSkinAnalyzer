"""
Analysis service untuk Perfect Corp API v2.0
"""
import requests
import logging
from fastapi import HTTPException
from config.settings import ANALYSIS_URL_V2, API_KEY_V2

# Setup logging
logger = logging.getLogger(__name__)


async def create_analysis_task_v2(
    src_file_url: str | None = None,
    src_file_id: str | None = None,
    dst_actions: list[str] | None = None,
    miniserver_args: dict | None = None,
) -> dict:
    """
    Membuat task skin-analysis pada Perfect Corp API v2.0.

    Args:
        src_file_url: (optional) URL sumber gambar
        src_file_id: (optional) file_id yang didapat dari upload v2
        dst_actions: list modul HD (contoh: ["hd_wrinkle","hd_pore"])
        miniserver_args: dict miniserver args

    Returns:
        Dict berisi task_id dan informasi lainnya
    """
    try:
        logger.info("Creating v2 analysis task")

        if not API_KEY_V2:
            raise HTTPException(
                status_code=500,
                detail="API_KEY_V2 tidak dikonfigurasi. Tambahkan API key v2 ke .env"
            )

        headers = {
            "Authorization": f"Bearer {API_KEY_V2}",
            "Content-Type": "application/json"
        }

        payload: dict = {}
        if src_file_url:
            payload["src_file_url"] = src_file_url
        if src_file_id:
            payload["src_file_id"] = src_file_id
        if dst_actions:
            payload["dst_actions"] = dst_actions
        if miniserver_args:
            payload["miniserver_args"] = miniserver_args

        logger.info(f"Request URL: {ANALYSIS_URL_V2}")
        logger.info(f"Request payload: {payload}")

        response = requests.post(
            ANALYSIS_URL_V2,
            headers=headers,
            json=payload,
            # timeout=30
        )

        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text}")

        if response.status_code == 400:
            raise HTTPException(status_code=400, detail=response.text)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="API Key invalid or unauthorized")
        if response.status_code >= 500:
            raise HTTPException(status_code=500, detail=response.text)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)

        data = response.json()
        status = data.get("status")
        payload = data.get("data", {})
        task_id = payload.get("task_id")

        if status != 200 or not task_id:
            raise HTTPException(status_code=500, detail=f"Invalid response: {data}")

        return {"status": "success", "task_id": task_id, "raw": data}

    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timeout to Perfect Corp v2")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error v2 analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error v2 analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def check_task_status_v2(task_id: str) -> dict:
    """
    Mengecek status task analysis v2.0 dari Perfect Corp API.
    
    Args:
        task_id: ID task yang didapat dari create_analysis_task_v2()
    
    Returns:
        Dict berisi status task dan hasil analisis (jika sudah selesai)
        
    Response structure:
        {
            "status": 200,
            "data": {
                "task_status": "running" | "success" | "error",
                "error": "error_code",  # Jika ada error
                "error_message": "string",  # Pesan error
                "results": {
                    "url": "https://..."  # URL hasil ZIP jika success
                }
            }
        }
    """
    try:
        logger.info(f"Checking v2 task status for task_id: {task_id}")
        
        if not API_KEY_V2:
            raise HTTPException(
                status_code=500,
                detail="API_KEY_V2 tidak dikonfigurasi. Tambahkan API key v2 ke .env"
            )
        
        # Step 1: Prepare headers
        headers = {
            "Authorization": f"Bearer {API_KEY_V2}",
            "Content-Type": "application/json"
        }
        
        # Step 2: Prepare URL dengan task_id di path
        check_url = f"{ANALYSIS_URL_V2}/{task_id}"
        
        logger.info(f"Request URL: {check_url}")
        
        # Step 3: Kirim GET request
        response = requests.get(
            check_url,
            headers=headers,
            # timeout=30
        )
        
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response body: {response.text}")
        
        # Step 4: Handle response errors
        if response.status_code == 400:
            raise HTTPException(status_code=400, detail=response.text)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="API Key invalid or unauthorized")
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Task ID tidak ditemukan atau sudah expired")
        if response.status_code >= 500:
            raise HTTPException(status_code=500, detail=response.text)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        # Step 5: Parse response
        data = response.json()
        status = data.get("status")
        result = data.get("data", {})
        task_status = result.get("task_status")
        
        if status != 200:
            raise HTTPException(status_code=500, detail=f"Invalid response: {data}")
        
        # Step 6: Format response berdasarkan task_status
        response_data = {
            "task_id": task_id,
            "task_status": task_status,
        }
        
        if task_status == "running":
            logger.info(f"Task {task_id} masih diproses")
            response_data["message"] = "Analisis masih dalam proses. Silakan cek kembali."
            
        elif task_status == "success":
            logger.info(f"Task {task_id} selesai dengan sukses")
            response_data["message"] = "Analisis selesai!"
            results = result.get("results", {})
            response_data["results"] = results
            
            # Extract result URL jika ada
            result_url = results.get("url") if isinstance(results, dict) else None
            if result_url:
                response_data["result_url"] = result_url
                response_data["note"] = "Download ZIP hasil analisis dari result_url"
            
        elif task_status == "error":
            error_code = result.get("error", "unknown_error")
            error_message = result.get("error_message", "Unknown error occurred")
            logger.error(f"Task {task_id} failed: {error_code} - {error_message}")
            response_data["message"] = f"Analisis gagal: {error_message}"
            response_data["error_code"] = error_code
            response_data["error_message"] = error_message
        
        else:
            # Unknown status
            response_data["message"] = f"Status tidak dikenal: {task_status}"
            response_data["raw_data"] = result
        
        return response_data
    
    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Request timeout to Perfect Corp v2")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error checking v2 status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error checking v2 status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
