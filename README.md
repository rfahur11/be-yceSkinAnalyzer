# Perfect Corp Skin Analysis API

FastAPI application untuk autentikasi dan upload file ke Perfect Corp (YouCam AI Skin Analysis) API.

## Fitur

- ✅ Autentikasi dengan RSA encryption
- ✅ Token management otomatis (refresh saat expired)
- ✅ Upload file gambar ke Perfect Corp
- ✅ Error handling lengkap (401, 404, 500)
- ✅ CORS support
- ✅ API documentation otomatis (Swagger UI)

## Instalasi

1. Buat virtual environment:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

2. Install dependencies:
```powershell
pip install -r requirements.txt
```

3. Copy `.env.example` ke `.env` (opsional):
```powershell
copy .env.example .env
```

## Menjalankan Server

```powershell
python main.py
```

Atau menggunakan uvicorn langsung:
```powershell
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server akan berjalan di: `http://localhost:8000`

## API Endpoints

### 1. Health Check
```
GET /
```
Mengecek status aplikasi dan token.

**Response:**
```json
{
  "message": "Perfect Corp Skin Analysis API",
  "status": "running",
  "token_status": "valid"
}
```

### 2. Get Token
```
POST /get_token
```
Mendapatkan access token dari Perfect Corp API.

**Alur:**
1. Buat timestamp (millisecond)
2. Enkripsi `client_id=<CLIENT_ID>&timestamp=<timestamp>` dengan RSA public key
3. Request token ke Perfect Corp
4. Simpan token di memory

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "expires_at": "2025-10-27T15:30:00",
  "message": "Token berhasil didapatkan"
}
```

### 3. Upload File
```
POST /upload
```
Upload gambar ke Perfect Corp API.

**Parameters:**
- `file`: File gambar (JPEG/PNG)

**Alur:**
1. Validasi token (otomatis refresh jika expired)
2. Request `upload_url` dan `file_id` dari Perfect Corp
3. Upload file ke `upload_url`
4. Return `file_id`

**Response:**
```json
{
  "file_id": "abc123xyz",
  "filename": "face.jpg",
  "content_type": "image/jpeg",
  "size": 245678,
  "message": "File berhasil diupload",
  "upload_status": "success"
}
```

### 4. Token Status
```
GET /token_status
```
Mengecek status token saat ini.

**Response:**
```json
{
  "status": "valid",
  "has_token": true,
  "expires_at": "2025-10-27T15:30:00",
  "time_until_expiry": 2845,
  "message": "Token masih valid"
}
```

## Testing dengan cURL

### Get Token
```powershell
curl -X POST http://localhost:8000/get_token
```

### Upload File
```powershell
curl -X POST http://localhost:8000/upload `
  -F "file=@path/to/image.jpg"
```

### Check Token Status
```powershell
curl http://localhost:8000/token_status
```

## Testing dengan Python

```python
import requests

# Get token
response = requests.post("http://localhost:8000/get_token")
print(response.json())

# Upload file
with open("image.jpg", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8000/upload", files=files)
    print(response.json())
```

## API Documentation

Setelah server berjalan, akses dokumentasi interaktif di:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Token Management

Token disimpan di memory (variabel global) dengan fitur:
- Auto-refresh saat expired
- Buffer 60 detik sebelum expiry untuk refresh awal
- Validasi otomatis sebelum setiap request

## Error Handling

API menangani berbagai error:
- **400**: File type tidak didukung
- **401**: Credential invalid atau token expired
- **404**: Endpoint tidak ditemukan
- **500**: Server error atau network error

## Struktur Project

```
backend/
├── main.py              # FastAPI application utama
├── convert.py           # Script testing enkripsi RSA
├── requirements.txt     # Python dependencies
├── .env.example        # Contoh konfigurasi environment
└── README.md           # Dokumentasi ini
```

## Dependencies

- `fastapi[standard]` - Web framework
- `uvicorn[standard]` - ASGI server
- `cryptography` - RSA encryption
- `requests` - HTTP client
- `python-multipart` - File upload support

## Notes

- Client ID dan Secret sudah hardcoded di `main.py` (bisa dipindah ke `.env`)
- Token disimpan di memory, akan hilang saat restart server
- Untuk production, pertimbangkan menggunakan Redis atau database untuk token storage
- Upload file maksimal size tergantung konfigurasi Perfect Corp API

## License

MIT