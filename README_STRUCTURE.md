# Struktur Folder Backend

Aplikasi telah direstrukturisasi menjadi arsitektur yang lebih modular dan maintainable.

## 📁 Struktur Folder

```
backend/
├── app.py                      # Entry point aplikasi FastAPI
├── main.py                     # File lama (bisa dihapus setelah migrasi)
│
├── config/                     # Konfigurasi aplikasi
│   ├── __init__.py
│   └── settings.py            # Settings dan environment variables
│
├── api/                        # Layer API
│   ├── __init__.py
│   ├── middleware.py          # CORS dan middleware lainnya
│   ├── error_handlers.py      # Global error handlers
│   └── routes/                # Route handlers
│       ├── __init__.py
│       ├── health.py          # Health check endpoints
│       ├── token.py           # Token management endpoints
│       └── upload.py          # File upload endpoints
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── token_manager.py       # Token management service
│   └── upload_service.py      # Upload file service
│
└── utils/                      # Utility functions
    ├── __init__.py
    └── encryption.py          # RSA encryption utilities
```

## 🚀 Cara Menjalankan

### Menggunakan file baru (app.py):
```bash
uvicorn app:app --reload --host localhost --port 8000
```

### Atau menggunakan Python:
```bash
python app.py
```

## 📝 Endpoint yang Tersedia

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Token Management
- `POST /token/get` - Mendapatkan access token
- `GET /token/status` - Cek status token

### File Upload
- `POST /upload` - Upload file gambar

## 🔧 Perubahan Utama

### 1. **Separation of Concerns**
   - **Config**: Semua konfigurasi terpusat di `config/settings.py`
   - **Services**: Business logic terpisah dari routes
   - **Utils**: Helper functions yang reusable
   - **API**: Route handlers yang clean dan minimal

### 2. **Token Manager Class**
   - Menggunakan class-based approach untuk token management
   - Singleton pattern untuk shared state
   - Methods yang lebih jelas dan testable

### 3. **Service Layer**
   - Upload logic terpisah di `upload_service.py`
   - Easier to test dan maintain
   - Reusable di berbagai routes

### 4. **Router Organization**
   - Routes diorganisir berdasarkan domain
   - Prefix dan tags untuk dokumentasi yang lebih baik
   - Cleaner URL structure

### 5. **Middleware & Error Handlers**
   - Terpisah di file sendiri
   - Mudah untuk dikonfigurasi dan dimodifikasi
   - Centralized error handling

## 📊 Keuntungan Struktur Baru

1. **Maintainability**: Code lebih mudah dibaca dan dipelihara
2. **Testability**: Setiap komponen bisa ditest secara terpisah
3. **Scalability**: Mudah menambah fitur baru
4. **Reusability**: Functions dan classes bisa digunakan kembali
5. **Organization**: Jelas pembagian responsibility setiap module

## 🔄 Migrasi dari main.py

File `main.py` yang lama masih ada untuk referensi. Setelah memastikan semua berjalan dengan baik menggunakan `app.py`, Anda bisa:

1. Backup `main.py` jika diperlukan
2. Hapus `main.py` untuk menghindari konfusi
3. Update documentation dan scripts untuk menggunakan `app.py`

## 🧪 Testing

Struktur baru memudahkan untuk membuat unit tests:

```python
# Example test
from services.token_manager import TokenManager

async def test_token_manager():
    manager = TokenManager()
    assert not manager.has_token()
    
    token = await manager.get_token()
    assert manager.has_token()
    assert token is not None
```

## 📖 Best Practices

1. **Environment Variables**: Pindahkan credentials ke `.env` file
2. **Type Hints**: Gunakan type hints untuk better IDE support
3. **Docstrings**: Dokumentasi lengkap untuk setiap function
4. **Error Handling**: Proper exception handling di semua layers
5. **Logging**: Tambahkan logging untuk monitoring dan debugging
