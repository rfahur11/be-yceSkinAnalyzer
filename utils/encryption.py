"""
Utility untuk enkripsi RSA
"""
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
import base64
from fastapi import HTTPException


def encrypt_with_rsa(data: str, public_key_string: str) -> str:
    """
    Enkripsi data menggunakan RSA public key dan encode ke Base64.
    
    Args:
        data: String yang akan dienkripsi
        public_key_string: RSA public key dalam format Base64
        
    Returns:
        String hasil enkripsi dalam format Base64
    """
    try:
        # Format public key sesuai standar PEM
        public_key_pem = f"-----BEGIN PUBLIC KEY-----\n{public_key_string}\n-----END PUBLIC KEY-----"
        
        # Load public key dari format PEM
        public_key = serialization.load_pem_public_key(
            public_key_pem.encode(),
            backend=default_backend()
        )
        
        # Enkripsi data menggunakan PKCS1v15 padding
        encrypted = public_key.encrypt(
            data.encode(),
            padding.PKCS1v15()
        )
        
        # Convert ke base64 dan return sebagai string
        return base64.b64encode(encrypted).decode()
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saat enkripsi data: {str(e)}"
        )
