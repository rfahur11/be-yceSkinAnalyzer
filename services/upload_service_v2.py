"""
Upload service untuk Perfect Corp API v2.0
"""
import requests
import logging
from io import BytesIO
from PIL import Image
from fastapi import HTTPException
from config.settings import UPLOAD_URL_V2, API_KEY_V2

# Setup logging
logger = logging.getLogger(__name__)

# Reuse resize_image from the v1 upload service to avoid duplication.
# This keeps one authoritative implementation and preserves logging/behavior.
from services.upload_service import resize_image


async def request_upload_url_v2(
    file_name: str,
    content_type: str,
    file_size: int
) -> dict:
    """
    Request presigned upload URL dari Perfect Corp API v2.0.
    
    Perbedaan v2.0 dengan v1.x:
    - Menggunakan API Key instead of Bearer Token
    - Menggunakan presigned URL untuk upload
    - Mendukung multiple files dalam satu request
    - Response structure berbeda
    
    Args:
        file_name: Nama file (contoh: "my-selfie.jpg")
        content_type: MIME type (contoh: "image/jpg")
        file_size: Ukuran file dalam bytes
    
    Returns:
        Dict berisi file_id dan presigned upload URL
        
    Example Response:
        {
            "file_id": "U8aqJbsXGT537jtGnEDFHqxdDXqh8+oTF/cSkLimzuvVwMP+Jb1XbjPsf7ZgUgLY",
            "upload_url": "https://example.com/presigned-upload-url",
            "upload_method": "PUT",
            "upload_headers": {
                "Content-Type": "image/jpg",
                "Content-Length": 50000
            }
        }
    """
    try:
        logger.info(f"Requesting upload URL for file: {file_name}")
        logger.info(f"Content-Type: {content_type}, Size: {file_size} bytes")
        
        # Validate API Key
        if not API_KEY_V2:
            raise HTTPException(
                status_code=500,
                detail="API_KEY_V2 tidak dikonfigurasi. Tambahkan ke file .env"
            )
        
        # Step 1: Prepare headers untuk v2.0
        headers = {
            "Authorization": f"Bearer {API_KEY_V2}",  # v2.0 menggunakan API Key
            "Content-Type": "application/json"
        }
        
        # Step 2: Prepare request payload
        payload = {
            "files": [
                {
                    "file_name": file_name,
                    "content_type": content_type,
                    "file_size": file_size
                }
            ]
        }
        
        logger.info(f"Request URL: {UPLOAD_URL_V2}")
        logger.info(f"Request Payload: {payload}")
        
        # Step 3: Request presigned URL dari Perfect Corp API v2.0
        response = requests.post(
            UPLOAD_URL_V2,
            headers=headers,
            json=payload,
            # timeout=30
        )
        
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Body: {response.text}")
        
        # Step 4: Handle response errors
        if response.status_code == 400:
            error_detail = response.json() if response.text else "Bad request"
            raise HTTPException(
                status_code=400,
                detail=f"Invalid request: {error_detail}"
            )
        
        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="API Key tidak valid. Periksa API_KEY_V2 di file .env"
            )
        
        if response.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail="Akses ditolak. Periksa permission API Key"
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
        
        # Step 5: Parse response
        response_data = response.json()
        
        # Response structure dari Perfect Corp v2.0:
        # {
        #   "status": 200,
        #   "data": {
        #     "files": [
        #       {
        #         "file_id": "...",
        #         "file_name": "...",
        #         "content_type": "...",
        #         "requests": [
        #           {
        #             "url": "https://...",
        #             "method": "PUT",
        #             "headers": {...}
        #           }
        #         ]
        #       }
        #     ]
        #   }
        # }
        
        status = response_data.get("status")
        data = response_data.get("data", {})
        files = data.get("files", [])
        
        if status != 200 or not files:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid response from Perfect Corp API: {response_data}"
            )
        
        # Ambil data file pertama (karena kita hanya upload 1 file)
        file_data = files[0]
        file_id = file_data.get("file_id")
        requests_data = file_data.get("requests", [])
        
        if not file_id or not requests_data:
            raise HTTPException(
                status_code=500,
                detail=f"Missing file_id or upload URL in response: {file_data}"
            )
        
        # Ambil presigned URL request pertama
        upload_request = requests_data[0]
        upload_url = upload_request.get("url")
        upload_method = upload_request.get("method", "PUT")
        upload_headers = upload_request.get("headers", {})
        
        # Extract base URL gambar (tanpa query parameters) untuk digunakan di analysis v2
        # Presigned URL format: https://domain/path?signature...
        # Image URL untuk analysis: https://domain/path (tanpa query params)
        image_url = upload_url.split('?')[0] if upload_url else None
        
        logger.info(f"Upload URL received successfully. File ID: {file_id}")
        logger.info(f"Image URL for analysis: {image_url}")
        
        # Step 6: Return hasil
        return {
            "file_id": file_id,
            "file_name": file_data.get("file_name"),
            "content_type": file_data.get("content_type"),
            "upload_url": upload_url,
            "upload_method": upload_method,
            "upload_headers": upload_headers,
            "image_url": image_url,  # URL gambar untuk digunakan di analysis v2
            "note": "Gunakan upload_url untuk upload file, lalu gunakan image_url untuk analysis"
        }
    
    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Request timeout. Perfect Corp API tidak merespon dalam waktu yang ditentukan."
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during upload URL request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Network error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during upload URL request: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


async def upload_to_presigned_url(
    presigned_url: str,
    file_content: bytes,
    headers: dict
) -> bool:
    """
    Upload file ke presigned URL yang didapat dari request_upload_url_v2().
    
    Args:
        presigned_url: URL presigned dari Perfect Corp
        file_content: Binary content file
        headers: Headers yang harus digunakan untuk upload
    
    Returns:
        True jika upload sukses
    """
    try:
        logger.info(f"Uploading file to presigned URL...")
        
        # Upload file ke presigned URL menggunakan PUT
        response = requests.put(
            presigned_url,
            data=file_content,
            headers=headers,
            timeout=60  # Upload bisa memakan waktu lebih lama
        )
        
        logger.info(f"Upload Response Status Code: {response.status_code}")
        
        # Presigned URL biasanya return 200 atau 204 untuk sukses
        if response.status_code not in [200, 204]:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file to presigned URL. Status: {response.status_code}"
            )
        
        logger.info("File uploaded successfully to presigned URL")
        return True
    
    except HTTPException:
        raise
    except requests.exceptions.Timeout:
        raise HTTPException(
            status_code=504,
            detail="Upload timeout. File terlalu besar atau koneksi lambat."
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error during file upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Network error during upload: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error during upload: {str(e)}"
        )
