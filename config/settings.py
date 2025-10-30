"""
Konfigurasi aplikasi dan Perfect Corp API
"""
import os
from dotenv import load_dotenv

# Load environment variables dari .env file
load_dotenv()

# Perfect Corp API Configuration
CLIENT_ID = os.getenv(
    "CLIENT_ID"
)
CLIENT_SECRET = os.getenv(
    "CLIENT_SECRET"
)
API_KEY_V2 = os.getenv(
    "API_KEY_V2",
    ""  # API Key untuk v2.0
)

# API Endpoints V1
TOKEN_URL = os.getenv(
    "TOKEN_URL"
)
UPLOAD_URL = os.getenv(
    "UPLOAD_URL"
)
ANALYSIS_URL = os.getenv(
    "ANALYSIS_URL"
)

# API Endpoints V2
UPLOAD_URL_V2 = os.getenv(
    "UPLOAD_URL_V2",
    "https://yce-api-01.perfectcorp.com/s2s/v2.0/file/skin-analysis"
)
ANALYSIS_URL_V2 = os.getenv(
    "ANALYSIS_URL_V2",
    "https://yce-api-01.perfectcorp.com/s2s/v2.0/task/skin-analysis"
)

# CORS Configuration
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
CORS_ALLOW_CREDENTIALS = os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
CORS_ALLOW_METHODS = os.getenv("CORS_ALLOW_METHODS", "*").split(",")
CORS_ALLOW_HEADERS = os.getenv("CORS_ALLOW_HEADERS", "*").split(",")

# File Upload Configuration
ALLOWED_FILE_TYPES = os.getenv(
    "ALLOWED_FILE_TYPES",
    "image/jpeg,image/jpg,image/png"
).split(",")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(10 * 1024 * 1024)))  # Default 10MB

# Server Configuration
HOST = os.getenv("HOST")
PORT = int(os.getenv("PORT"))
