"""
Token management service untuk Perfect Corp API
"""
import time
import requests
from fastapi import HTTPException
from config.settings import CLIENT_ID, CLIENT_SECRET, TOKEN_URL
from utils.encryption import encrypt_with_rsa


class TokenManager:
    """Class untuk mengelola access token"""
    
    def __init__(self):
        self.access_token = None
    
    def has_token(self) -> bool:
        """
        Cek apakah token tersedia.
        
        Returns:
            True jika token ada, False jika tidak ada
        """
        return self.access_token is not None
    
    async def get_token(self) -> str:
        """
        Mendapatkan access_token dari Perfect Corp API.
        
        Alur:
        1. Buat timestamp dalam millisecond
        2. Gabungkan string: client_id=<CLIENT_ID>&timestamp=<timestamp>
        3. Enkripsi string menggunakan RSA public key
        4. Panggil API Perfect Corp untuk mendapatkan access_token
        5. Simpan token ke variabel instance
        
        Returns:
            access_token yang didapatkan dari API
        """
        try:
            # Step 1: Buat timestamp dalam millisecond
            timestamp = int(time.time() * 1000)
            
            # Step 2: Gabungkan client_id dan timestamp
            data_string = f"client_id={CLIENT_ID}&timestamp={timestamp}"
            
            # Step 3: Enkripsi menggunakan RSA public key
            id_token = encrypt_with_rsa(data_string, CLIENT_SECRET)
            
            # Step 4: Siapkan payload untuk request token
            payload = {
                "client_id": CLIENT_ID,
                "id_token": id_token
            }
            
            # Step 5: Panggil API Perfect Corp untuk mendapatkan token
            headers = {
                "Content-Type": "application/json"
            }
            response = requests.post(TOKEN_URL, json=payload, headers=headers)
            
            # Handle error response
            if response.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Unauthorized: Invalid client credentials"
                )
            elif response.status_code == 404:
                raise HTTPException(
                    status_code=404,
                    detail="Token endpoint not found"
                )
            elif response.status_code >= 500:
                raise HTTPException(
                    status_code=500,
                    detail=f"Perfect Corp API error: {response.text}"
                )
            elif response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Error getting token: {response.text}"
                )
            
            # Parse response
            token_response = response.json()
            
            # Perfect Corp API mengembalikan struktur: {"status": 200, "result": {"access_token": "..."}}
            result = token_response.get("result", {})
            access_token = result.get("access_token")
            
            # Validasi jika access_token tidak ada
            if not access_token:
                raise HTTPException(
                    status_code=500,
                    detail=f"API mengembalikan respons sukses tetapi access_token null. Response: {token_response}"
                )
            
            # Simpan token ke variabel instance
            self.access_token = access_token
            
            return access_token
        
        except HTTPException:
            raise
        except requests.exceptions.RequestException as e:
            raise HTTPException(
                status_code=500,
                detail=f"Network error saat memanggil Perfect Corp API: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )
    
    async def ensure_valid_token(self) -> str:
        """
        Memastikan token valid, jika tidak ada maka dapatkan token baru.
        
        Returns:
            access_token yang valid
        """
        if not self.has_token():
            return await self.get_token()
        
        return self.access_token
    
    def invalidate_token(self):
        """Invalidate/reset token yang tersimpan"""
        self.access_token = None
    
    def get_status(self) -> dict:
        """
        Mendapatkan status token saat ini.
        
        Returns:
            Dict berisi informasi status token
        """
        if not self.has_token():
            return {
                "status": "no_token",
                "message": "Token belum pernah di-request",
                "has_token": False
            }
        
        return {
            "status": "valid",
            "has_token": True,
            "message": "Token tersedia"
        }


# Singleton instance
token_manager = TokenManager()
