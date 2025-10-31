# 📊 Sequence Diagram: Penyimpanan Data Hasil Prediksi ke Database

## Overview

Dokumen ini menjelaskan alur lengkap bagaimana hasil prediksi AI Skin Analysis dari Perfect Corp disimpan ke database PostgreSQL, termasuk pembuatan dataset dalam format COCO untuk future training.

---

## 🎯 Tujuan Sistem

1. **History Management**: Menyimpan riwayat analisis untuk diakses kembali oleh user
2. **Dataset Creation**: Membuat dataset terstruktur dalam format COCO Instance Segmentation
3. **Future Training**: Menyiapkan data untuk melatih model skin analyzer sendiri

---

## 🔄 Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION LAYER                              │
│                         (Browser - React/Next.js)                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. USER CAPTURES PHOTO                                                      │
│    Component: CameraComponent.tsx                                           │
│    ├─ YMK SDK Camera opens                                                  │
│    ├─ User positions face                                                   │
│    ├─ Photo auto-captured when quality is good                             │
│    └─ Output: base64Image (720x720 or custom size)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. UPLOAD TO PERFECT CORP                                                   │
│    Frontend: POST /api/upload-v2                                            │
│    Backend:  POST /v2/upload/direct?mode=sd                                 │
│                                                                              │
│    Flow:                                                                     │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ A. Frontend calls Next.js API route                              │    │
│    │    POST /api/upload-v2                                           │    │
│    │    Body: { image: base64String, mode: "sd" }                     │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                            ↓                                                 │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ B. Next.js forwards to Python Backend                            │    │
│    │    POST http://localhost:8000/v2/upload/direct                   │    │
│    │    Service: upload_service_v2.py                                 │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                            ↓                                                 │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ C. Backend requests presigned URL from Perfect Corp              │    │
│    │    POST https://api-us.perfectcorp.com/v2/image/upload           │    │
│    │    Headers: {                                                     │    │
│    │      X-API-Key: <api_key>,                                       │    │
│    │      X-API-Secret: <api_secret>                                  │    │
│    │    }                                                              │    │
│    │    Response: {                                                    │    │
│    │      file_id: "xP12I2tU3...",                                    │    │
│    │      presigned_url: "https://yce-us.s3.amazonaws.com/..."       │    │
│    │    }                                                              │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                            ↓                                                 │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ D. Upload image to presigned S3 URL                              │    │
│    │    PUT <presigned_url>                                           │    │
│    │    Body: image binary                                            │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│    Output: {                                                                │
│      file_id: "xP12I2tU3bUFXyp2Z816ZnK9S6+EO0xzu9mIQFND5GsL...",           │
│      image_url: "https://yce-us.s3-accelerate.amazonaws.com/...",          │
│      processed_size: 107020,                                                │
│      resize_info: {...}                                                     │
│    }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 3. CREATE ANALYSIS TASK                                                     │
│    Frontend: POST /api/analyze-v2                                           │
│    Backend:  POST /api/v2/analyze/create-task                               │
│                                                                              │
│    Flow:                                                                     │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ A. Frontend calls Next.js API route                              │    │
│    │    POST /api/analyze-v2                                          │    │
│    │    Body: {                                                        │    │
│    │      file_id: "xP12I2tU3...",                                    │    │
│    │      image_url: "https://...",                                   │    │
│    │      dst_actions: ["wrinkle", "pore", "texture", "acne"]        │    │
│    │    }                                                              │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                            ↓                                                 │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ B. Next.js forwards to Python Backend                            │    │
│    │    POST http://localhost:8000/api/v2/analyze/create-task         │    │
│    │    Service: analysis_service_v2.py                               │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                            ↓                                                 │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ C. Backend creates task at Perfect Corp                          │    │
│    │    POST https://api-us.perfectcorp.com/v2/skin-analysis/task     │    │
│    │    Body: {                                                        │    │
│    │      src_file_id: "xP12I2tU3...",                                │    │
│    │      dst_actions: ["wrinkle", "pore", "texture", "acne"]        │    │
│    │    }                                                              │    │
│    │    Response: {                                                    │    │
│    │      task_id: "xP12I2tU3bUFXyp2Z816ZnK9S6-EO0xzu9..."           │    │
│    │    }                                                              │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│    Output: {                                                                │
│      task_id: "xP12I2tU3bUFXyp2Z816ZnK9S6-EO0xzu9mIQFND5GsH..."           │
│    }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 4. POLL TASK STATUS (Until Complete)                                        │
│    Backend: GET /api/v2/analyze/task-status/{task_id}                      │
│                                                                              │
│    Polling Loop (max 60 attempts, 5 sec interval):                         │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ Loop every 5 seconds:                                            │    │
│    │   GET https://api-us.perfectcorp.com/v2/skin-analysis/task-status│    │
│    │   /{task_id}                                                      │    │
│    │                                                                   │    │
│    │   Responses:                                                      │    │
│    │   ├─ status: "running"  → Continue polling                       │    │
│    │   ├─ status: "success"  → Return result_url, break loop          │    │
│    │   └─ status: "error"    → Return error, break loop               │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│    Output (Success): {                                                      │
│      status: "success",                                                     │
│      task_id: "xP12I2tU3...",                                              │
│      result_url: "https://yce-us.s3-accelerate.amazonaws.com/.../xxx.zip"  │
│    }                                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 5. DOWNLOAD & PROCESS RESULTS                                               │
│    Frontend: POST /api/download-result                                      │
│    File: fe/src/app/api/download-result/route.ts                           │
│                                                                              │
│    Flow:                                                                     │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ A. Download ZIP from Perfect Corp S3                             │    │
│    │    GET <result_url>                                              │    │
│    │    Returns: result.zip (~27KB)                                   │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                            ↓                                                 │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ B. Extract ZIP Contents                                          │    │
│    │    Using: jszip library                                          │    │
│    │    Files extracted:                                              │    │
│    │      ├─ skinanalysisResult/score_info.json                       │    │
│    │      ├─ skinanalysisResult/acne_output.png                       │    │
│    │      ├─ skinanalysisResult/pore_output.png                       │    │
│    │      ├─ skinanalysisResult/wrinkle_output.png                    │    │
│    │      └─ skinanalysisResult/texture_output.png                    │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                            ↓                                                 │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ C. Parse score_info.json                                         │    │
│    │    Structure: {                                                  │    │
│    │      "acne": { "score": 85, "level": "good", ... },             │    │
│    │      "wrinkle": { "score": 72, "level": "fair", ... },          │    │
│    │      "pore": { "score": 90, "level": "excellent", ... },        │    │
│    │      "texture": { "score": 88, "level": "good", ... }           │    │
│    │    }                                                              │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                            ↓                                                 │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ D. Convert Mask Images to Base64                                │    │
│    │    For each mask PNG:                                            │    │
│    │      ├─ Read as uint8array                                       │    │
│    │      ├─ Convert to base64                                        │    │
│    │      └─ Add data URL prefix: "data:image/png;base64,..."        │    │
│    │                                                                   │    │
│    │    Result: {                                                     │    │
│    │      acne: "data:image/png;base64,iVBORw0KG...",                │    │
│    │      pore: "data:image/png;base64,iVBORw0KG...",                │    │
│    │      wrinkle: "data:image/png;base64,iVBORw0KG...",             │    │
│    │      texture: "data:image/png;base64,iVBORw0KG..."              │    │
│    │    }                                                              │    │
│    └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 6. SAVE TO BACKEND DATABASE ⭐⭐⭐ (CRITICAL STEP)                          │
│    Frontend: POST http://localhost:8000/api/v2/history/save-from-frontend  │
│    File: be/api/routes/history.py                                          │
│                                                                              │
│    Request Payload:                                                         │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ {                                                                │    │
│    │   "task_id": "xP12I2tU3...",                                     │    │
│    │   "file_id": "xP12I2tU3...",                                     │    │
│    │   "result_url": "https://yce-us.s3.../result.zip",              │    │
│    │   "original_image_base64": "data:image/jpeg;base64,...",        │    │
│    │   "result_data": {                                               │    │
│    │     "score_info": { acne: {...}, pore: {...}, ... },            │    │
│    │     "result_images": {                                           │    │
│    │       acne: "data:image/png;base64,...",                         │    │
│    │       pore: "data:image/png;base64,...",                         │    │
│    │       ...                                                         │    │
│    │     }                                                             │    │
│    │   },                                                              │    │
│    │   "user_id": null                                                │    │
│    │ }                                                                │    │
│    └──────────────────────────────────────────────────────────────────┘    │
│                                                                              │
│    Backend Processing:                                                      │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │ 📥 Receive request                                               │    │
│    │ ✅ Validate required fields (task_id, result_url, image)        │    │
│    │ 🔄 Decode base64 image                                           │    │
│    │ 🚀 Call dataset_service.process_and_save_analysis()             │    │
│    └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 7. DATASET STORAGE SERVICE PROCESSING                                       │
│    File: be/services/dataset_storage.py                                    │
│    Function: process_and_save_analysis()                                   │
│                                                                              │
│    ┌─────────────────────────────────────────────────────────────────┐     │
│    │ STEP 7.1: Save Original Image                                   │     │
│    │ ────────────────────────────────────────────────────────────    │     │
│    │ Function: save_original_image()                                 │     │
│    │                                                                  │     │
│    │ Actions:                                                         │     │
│    │ ├─ Generate filename: {task_id}_{timestamp}.jpg                │     │
│    │ ├─ Save to: dataset/images/{filename}                           │     │
│    │ ├─ Open with PIL to get dimensions                             │     │
│    │ └─ Return: (image_path, width, height)                          │     │
│    │                                                                  │     │
│    │ Example Output:                                                  │     │
│    │   Path: dataset/images/xP12I2tU3_20251031_160200.jpg           │     │
│    │   Dimensions: 720x720                                            │     │
│    └─────────────────────────────────────────────────────────────────┘     │
│                            ↓                                                 │
│    ┌─────────────────────────────────────────────────────────────────┐     │
│    │ STEP 7.2: Download & Extract Result ZIP                         │     │
│    │ ────────────────────────────────────────────────────────────    │     │
│    │ Function: download_and_extract_results()                        │     │
│    │                                                                  │     │
│    │ Actions:                                                         │     │
│    │ ├─ Create directory: dataset/masks/{task_id}/                  │     │
│    │ ├─ Download ZIP from result_url                                │     │
│    │ ├─ Save temporarily as: results.zip                            │     │
│    │ ├─ Extract all files to: dataset/masks/{task_id}/              │     │
│    │ └─ Delete results.zip                                           │     │
│    │                                                                  │     │
│    │ Example Output:                                                  │     │
│    │   dataset/masks/xP12I2tU3/                                      │     │
│    │   ├─ skinanalysisResult/score_info.json                         │     │
│    │   ├─ skinanalysisResult/acne_output.png                         │     │
│    │   ├─ skinanalysisResult/pore_output.png                         │     │
│    │   ├─ skinanalysisResult/wrinkle_output.png                      │     │
│    │   └─ skinanalysisResult/texture_output.png                      │     │
│    └─────────────────────────────────────────────────────────────────┘     │
│                            ↓                                                 │
│    ┌─────────────────────────────────────────────────────────────────┐     │
│    │ STEP 7.3: Identify Mask Files                                   │     │
│    │ ────────────────────────────────────────────────────────────    │     │
│    │ Function: identify_mask_files()                                 │     │
│    │                                                                  │     │
│    │ Pattern Matching:                                                │     │
│    │   acne       → acne, pimple, blemish                            │     │
│    │   wrinkle    → wrinkle, line, fine_line                         │     │
│    │   pore       → pore, enlarged_pore                              │     │
│    │   dark_spot  → dark_spot, spot, pigmentation, melasma           │     │
│    │   redness    → redness, red                                     │     │
│    │                                                                  │     │
│    │ Actions:                                                         │     │
│    │ ├─ Scan all *.png files in extracted directory                 │     │
│    │ ├─ Match filename to category patterns                          │     │
│    │ └─ Build dict: category_name → mask_file_path                  │     │
│    │                                                                  │     │
│    │ Example Output:                                                  │     │
│    │   {                                                              │     │
│    │     "acne": Path("dataset/masks/.../acne_output.png"),         │     │
│    │     "pore": Path("dataset/masks/.../pore_output.png"),         │     │
│    │     "wrinkle": Path("dataset/masks/.../wrinkle_output.png"),   │     │
│    │     "texture": Path("dataset/masks/.../texture_output.png")    │     │
│    │   }                                                              │     │
│    └─────────────────────────────────────────────────────────────────┘     │
│                            ↓                                                 │
│    ┌─────────────────────────────────────────────────────────────────┐     │
│    │ STEP 7.4: Create Overlay Visualization                          │     │
│    │ ────────────────────────────────────────────────────────────    │     │
│    │ Function: create_overlay_visualization()                        │     │
│    │                                                                  │     │
│    │ Color Mapping:                                                   │     │
│    │   acne       → Red (255, 0, 0, 100)                             │     │
│    │   wrinkle    → Orange (255, 165, 0, 100)                        │     │
│    │   pore       → Yellow (255, 255, 0, 100)                        │     │
│    │   dark_spot  → Purple (128, 0, 128, 100)                        │     │
│    │   dark_circle→ Blue (0, 0, 255, 100)                            │     │
│    │   eye_bag    → Cyan (0, 255, 255, 100)                          │     │
│    │   redness    → Magenta (255, 0, 255, 100)                       │     │
│    │                                                                  │     │
│    │ Actions:                                                         │     │
│    │ ├─ Load original image as RGBA                                  │     │
│    │ ├─ Create transparent overlay layer                             │     │
│    │ ├─ For each mask:                                               │     │
│    │ │  ├─ Load mask as grayscale                                    │     │
│    │ │  ├─ Resize to match original dimensions                       │     │
│    │ │  ├─ Create colored overlay with category color                │     │
│    │ │  └─ Composite onto overlay layer using mask as alpha          │     │
│    │ ├─ Composite overlay onto original image                        │     │
│    │ ├─ Convert to RGB                                               │     │
│    │ └─ Save as: dataset/overlays/{task_id}_overlay.jpg              │     │
│    │                                                                  │     │
│    │ Example Output:                                                  │     │
│    │   dataset/overlays/xP12I2tU3_overlay.jpg                        │     │
│    │   (Original image with colored mask overlays)                   │     │
│    └─────────────────────────────────────────────────────────────────┘     │
│                            ↓                                                 │
│    ┌─────────────────────────────────────────────────────────────────┐     │
│    │ STEP 7.5: Generate COCO JSON Annotation                         │     │
│    │ ────────────────────────────────────────────────────────────    │     │
│    │ Service: COCOGenerator (services/coco_generator.py)             │     │
│    │ Function: generate_coco_json()                                  │     │
│    │                                                                  │     │
│    │ COCO Format Structure:                                           │     │
│    │ {                                                                │     │
│    │   "info": {                                                      │     │
│    │     "description": "Skin Analysis Dataset",                     │     │
│    │     "version": "1.0",                                            │     │
│    │     "year": 2025,                                                │     │
│    │     "date_created": "2025-10-31T16:02:00Z"                      │     │
│    │   },                                                             │     │
│    │   "licenses": [...],                                             │     │
│    │   "images": [                                                    │     │
│    │     {                                                            │     │
│    │       "id": 1,                                                   │     │
│    │       "file_name": "xP12I2tU3_20251031_160200.jpg",            │     │
│    │       "width": 720,                                              │     │
│    │       "height": 720,                                             │     │
│    │       "date_captured": "2025-10-31T16:02:00Z"                   │     │
│    │     }                                                            │     │
│    │   ],                                                             │     │
│    │   "annotations": [                                               │     │
│    │     {                                                            │     │
│    │       "id": 1,                                                   │     │
│    │       "image_id": 1,                                             │     │
│    │       "category_id": 1,                                          │     │
│    │       "segmentation": [[x1,y1,x2,y2,x3,y3,...]],  ← Polygon    │     │
│    │       "bbox": [x, y, width, height],              ← BBox       │     │
│    │       "area": 12450,                               ← Pixels     │     │
│    │       "iscrowd": 0                                               │     │
│    │     },                                                           │     │
│    │     ... (more annotations for each detected region)             │     │
│    │   ],                                                             │     │
│    │   "categories": [                                                │     │
│    │     {                                                            │     │
│    │       "id": 1,                                                   │     │
│    │       "name": "acne",                                            │     │
│    │       "supercategory": "skin_issue"                             │     │
│    │     },                                                           │     │
│    │     {                                                            │     │
│    │       "id": 2,                                                   │     │
│    │       "name": "pore",                                            │     │
│    │       "supercategory": "skin_issue"                             │     │
│    │     },                                                           │     │
│    │     ... (more categories)                                        │     │
│    │   ]                                                              │     │
│    │ }                                                                │     │
│    │                                                                  │     │
│    │ Conversion Process (Mask → Polygon):                            │     │
│    │ ├─ Load mask image as binary (threshold)                        │     │
│    │ ├─ Find contours using OpenCV (cv2.findContours)               │     │
│    │ ├─ Approximate contours to polygons                             │     │
│    │ ├─ Calculate bounding box from contour                          │     │
│    │ ├─ Calculate area from contour                                  │     │
│    │ └─ Format as COCO segmentation: [[x1,y1,x2,y2,...]]            │     │
│    │                                                                  │     │
│    │ Example Output:                                                  │     │
│    │   dataset/annotations/xP12I2tU3_coco.json                       │     │
│    └─────────────────────────────────────────────────────────────────┘     │
│                            ↓                                                 │
│    ┌─────────────────────────────────────────────────────────────────┐     │
│    │ STEP 7.6: INSERT TO POSTGRESQL ⭐⭐⭐                            │     │
│    │ ────────────────────────────────────────────────────────────    │     │
│    │ Table: skin_analysis_history                                    │     │
│    │ ORM Model: SkinAnalysisHistory (database/models.py)            │     │
│    │                                                                  │     │
│    │ SQL Operation (via SQLAlchemy):                                 │     │
│    │                                                                  │     │
│    │ INSERT INTO skin_analysis_history (                             │     │
│    │   id,                  -- UUID (auto-generated)                 │     │
│    │   file_id,             -- "xP12I2tU3bUFXyp2Z816ZnK9S6+EO..."   │     │
│    │   task_id,             -- "xP12I2tU3bUFXyp2Z816ZnK9S6-EO..."   │     │
│    │   status,              -- "success"                             │     │
│    │   image_path,          -- "dataset/images/xP12I2tU3_....jpg"   │     │
│    │   masks_path,          -- JSON: ["dataset/masks/.../acne.png",..]│    │
│    │   overlay_path,        -- "dataset/overlays/xP12I2tU3_overlay.jpg"│  │
│    │   coco_json_path,      -- "dataset/annotations/xP12I2tU3_coco.json"│ │
│    │   result_zip_url,      -- "https://yce-us.s3.../result.zip"    │     │
│    │   result_json,         -- JSON: {score_info: {...}, ...}       │     │
│    │   image_width,         -- 720                                   │     │
│    │   image_height,        -- 720                                   │     │
│    │   user_id,             -- NULL (or user_id if provided)         │     │
│    │   created_at,          -- CURRENT_TIMESTAMP                     │     │
│    │   updated_at           -- CURRENT_TIMESTAMP                     │     │
│    │ ) VALUES (...);                                                  │     │
│    │                                                                  │     │
│    │ COMMIT;                                                          │     │
│    │                                                                  │     │
│    │ Output:                                                          │     │
│    │   Analysis ID: 550e8400-e29b-41d4-a716-446655440000 (UUID)     │     │
│    └─────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 8. RETURN SUCCESS TO FRONTEND                                               │
│                                                                              │
│    Backend Response:                                                        │
│    {                                                                         │
│      "status": "success",                                                   │
│      "message": "Analysis saved to database and dataset",                   │
│      "data": {                                                               │
│        "id": "550e8400-e29b-41d4-a716-446655440000",                        │
│        "task_id": "xP12I2tU3...",                                           │
│        "status": "success",                                                 │
│        "image_path": "dataset/images/xP12I2tU3_20251031_160200.jpg",       │
│        "masks_count": 4,                                                    │
│        "coco_json_path": "dataset/annotations/xP12I2tU3_coco.json",        │
│        "overlay_path": "dataset/overlays/xP12I2tU3_overlay.jpg",           │
│        "created_at": "2025-10-31T16:02:03.123456"                           │
│      }                                                                       │
│    }                                                                         │
│                                                                              │
│    Frontend Console Logs:                                                   │
│    [API] Backend save response status: 200                                  │
│    [API] ✅ Successfully saved to database: 550e8400-e29b-41d4-a716-...     │
│    [API] Full save result: {...}                                            │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 9. DISPLAY RESULTS TO USER                                                  │
│    Component: AnalysisResult.tsx                                            │
│                                                                              │
│    UI Display:                                                               │
│    ┌──────────────────────────────────────────────────────────────────┐    │
│    │                     Analysis Results                             │    │
│    │  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐    │    │
│    │  │  Original      │  │  Acne Mask     │  │  Pore Mask     │    │    │
│    │  │  Image         │  │  (Red overlay) │  │  (Yellow)      │    │    │
│    │  └────────────────┘  └────────────────┘  └────────────────┘    │    │
│    │                                                                  │    │
│    │  Scores:                                                         │    │
│    │  • Acne:    85/100  (Good)                                      │    │
│    │  • Pore:    90/100  (Excellent)                                 │    │
│    │  • Wrinkle: 72/100  (Fair)                                      │    │
│    │  • Texture: 88/100  (Good)                                      │    │
│    │                                                                  │    │
│    │  [Close]  [Download Full Results]                               │    │
│    └──────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Dataset Structure yang Dihasilkan

Setelah proses lengkap, struktur folder dataset adalah:

```
dataset/
├── images/                                    ← Original images
│   ├── xP12I2tU3_20251031_160200.jpg
│   ├── aBcDeF123_20251031_160530.jpg
│   └── ...
│
├── masks/                                     ← Mask outputs per task
│   ├── xP12I2tU3/
│   │   └── skinanalysisResult/
│   │       ├── score_info.json
│   │       ├── acne_output.png
│   │       ├── pore_output.png
│   │       ├── wrinkle_output.png
│   │       └── texture_output.png
│   ├── aBcDeF123/
│   │   └── ...
│   └── ...
│
├── overlays/                                  ← Annotated visualizations
│   ├── xP12I2tU3_overlay.jpg
│   ├── aBcDeF123_overlay.jpg
│   └── ...
│
└── annotations/                               ← COCO JSON files
    ├── xP12I2tU3_coco.json
    ├── aBcDeF123_coco.json
    └── ...
```

---

## 🗄️ Database Schema Details

### Table: `skin_analysis_history`

| Column | Type | Nullable | Description | Example |
|--------|------|----------|-------------|---------|
| `id` | UUID | No | Primary key | `550e8400-e29b-41d4-a716-446655440000` |
| `file_id` | String(255) | Yes | Perfect Corp file ID | `xP12I2tU3bUFXyp2Z816ZnK9S6+EO...` |
| `task_id` | String(255) | No | Perfect Corp task ID (indexed) | `xP12I2tU3bUFXyp2Z816ZnK9S6-EO...` |
| `status` | String(50) | No | Processing status | `success`, `processing`, `error` |
| `image_path` | String(500) | Yes | Relative path to original image | `dataset/images/xP12I2tU3_....jpg` |
| `masks_path` | JSON | Yes | Array of mask file paths | `["dataset/masks/.../acne.png", ...]` |
| `overlay_path` | String(500) | Yes | Path to overlay visualization | `dataset/overlays/xP12I2tU3_overlay.jpg` |
| `coco_json_path` | String(500) | Yes | Path to COCO annotation | `dataset/annotations/xP12I2tU3_coco.json` |
| `result_zip_url` | Text | Yes | Perfect Corp result ZIP URL | `https://yce-us.s3.../result.zip` |
| `result_json` | JSON | Yes | Full API response | `{"score_info": {...}, ...}` |
| `image_width` | Integer | Yes | Image width in pixels | `720` |
| `image_height` | Integer | Yes | Image height in pixels | `720` |
| `error_message` | Text | Yes | Error details if status=error | `null` or error string |
| `user_id` | String(255) | Yes | Optional user identifier | `user_123` or `null` |
| `created_at` | DateTime | No | Record creation timestamp | `2025-10-31 16:02:03.123456` |
| `updated_at` | DateTime | No | Last update timestamp | `2025-10-31 16:02:03.123456` |

### Indexes
- Primary key: `id`
- Index: `file_id`
- Index: `task_id`
- Index: `user_id`

---

## 🔑 Key Files & Responsibilities

| Component | File | Primary Function |
|-----------|------|-----------------|
| **Frontend Camera** | `fe/src/components/CameraComponent.tsx` | Capture photo, trigger analysis flow |
| **FE Upload Route** | `fe/src/app/api/upload-v2/route.ts` | Proxy upload to backend |
| **FE Analyze Route** | `fe/src/app/api/analyze-v2/route.ts` | Proxy create task & poll status |
| **FE Download Route** | `fe/src/app/api/download-result/route.ts` | Download ZIP, extract, call save |
| **BE Upload Service** | `be/services/upload_service_v2.py` | Upload to Perfect Corp S3 |
| **BE Analysis Service** | `be/services/analysis_service_v2.py` | Create task & check status |
| **BE History Route** | `be/api/routes/history.py` | Receive save request from FE |
| **BE Dataset Service** | `be/services/dataset_storage.py` | Orchestrate all save operations |
| **BE COCO Generator** | `be/services/coco_generator.py` | Convert masks to COCO format |
| **BE Database Models** | `be/database/models.py` | SQLAlchemy ORM models |

---

## 🎯 Critical Success Points

### ✅ Data Tersimpan Jika:

1. **Backend Running**: FastAPI server berjalan di `http://localhost:8000`
2. **Database Ready**: PostgreSQL service running dan tabel sudah di-create
3. **Original Image Available**: Frontend mengirim `original_image_base64` atau `original_image_url` dapat di-download
4. **Valid Payload**: Semua required fields ada (task_id, result_url, image)
5. **ZIP Downloaded**: Result ZIP dari Perfect Corp berhasil di-download
6. **Masks Extracted**: Mask files berhasil di-extract dan di-identify
7. **COCO Generated**: Polygon segmentation berhasil di-generate dari masks
8. **Database Insert**: SQLAlchemy berhasil INSERT record ke PostgreSQL

### ❌ Data TIDAK Tersimpan Jika:

1. Backend tidak running atau endpoint tidak terdaftar
2. Database connection error
3. Original image base64 kosong atau gagal di-decode
4. Result URL tidak valid atau ZIP tidak bisa di-download
5. Tidak ada mask files yang berhasil di-identify
6. Database constraint violation (e.g., duplicate task_id)
7. Disk space penuh atau permission error saat save file

---

## 📊 Logging & Monitoring

### Frontend Logs (Browser Console)

```
✅ Success Flow:
[API] Downloading result from: https://...
[API] ZIP downloaded, size: 27778
[API] ZIP extracted, files: [...]
[API] Score info loaded from: skinanalysisResult/score_info.json
[API] Extracted acne_output.png from skinanalysisResult/acne_output.png
[API] Saving to backend database...
[API] Using original image base64 from client payload
[API] Calling backend save URL: http://localhost:8000/api/v2/history/save-from-frontend
[API] Backend save response status: 200
[API] ✅ Successfully saved to database: 550e8400-e29b-41d4-a716-446655440000
```

### Backend Logs (Terminal)

```
✅ Success Flow:
INFO:api.routes.history:================================================================================
INFO:api.routes.history:📥 Received save request from frontend
INFO:api.routes.history:📋 task_id: xP12I2tU3bUFXyp2Z816ZnK9S6-EO0xzu9mIQFND5GsH...
INFO:api.routes.history:📋 file_id: xP12I2tU3bUFXyp2Z816ZnK9S6+EO0xzu9mIQFND5GsL...
INFO:api.routes.history:📋 has original_image_base64: True
INFO:api.routes.history:🔄 Decoding base64 image...
INFO:api.routes.history:✅ Image decoded, size: 88530 bytes
INFO:api.routes.history:🚀 Calling dataset_service.process_and_save_analysis...
INFO:services.dataset_storage:Processing analysis for task_id: xP12I2tU3...
INFO:services.dataset_storage:Original image saved: dataset/images/xP12I2tU3_20251031_160200.jpg (720x720)
INFO:services.dataset_storage:Downloading results from: https://yce-us.s3-accelerate.amazonaws.com/...
INFO:services.dataset_storage:Results extracted to: dataset/masks/xP12I2tU3/
INFO:services.dataset_storage:Identified mask: acne -> acne_output.png
INFO:services.dataset_storage:Identified mask: pore -> pore_output.png
INFO:services.dataset_storage:Identified mask: wrinkle -> wrinkle_output.png
INFO:services.dataset_storage:Identified mask: texture -> texture_output.png
INFO:services.dataset_storage:Overlay visualization saved: dataset/overlays/xP12I2tU3_overlay.jpg
INFO:services.coco_generator:Processing mask: acne
INFO:services.coco_generator:Found 15 contours in mask
INFO:services.coco_generator:Created annotation 1 for category acne
INFO:services.coco_generator:COCO JSON saved: dataset/annotations/xP12I2tU3_coco.json
INFO:services.dataset_storage:Analysis saved to database: 550e8400-e29b-41d4-a716-446655440000
INFO:api.routes.history:✅ Analysis saved successfully! ID: 550e8400-e29b-41d4-a716-446655440000
INFO:api.routes.history:================================================================================
```

---

## 🔧 Troubleshooting

### Problem: "No original image base64 - skipping database save"

**Cause**: Frontend tidak mengirim `original_image_base64` dan download dari `original_image_url` gagal.

**Solution**:
1. Pastikan `CameraComponent.tsx` mengirim field `original_image_base64` saat POST ke `/api/download-result`
2. Cek log: `[API] Using original image base64 from client payload`
3. Jika fallback ke download URL, pastikan `original_image_url` valid dan accessible

### Problem: Backend tidak menerima request

**Cause**: Backend tidak running atau CORS issue.

**Solution**:
```bash
# Terminal 1: Start Backend
cd be-yceSkinAnalyzer
python app.py

# Terminal 2: Test endpoint
curl http://localhost:8000/health
```

### Problem: Database INSERT gagal

**Cause**: Database tidak running, connection error, atau constraint violation.

**Solution**:
```bash
# Check PostgreSQL service
Get-Service postgresql*

# Test database connection
cd be-yceSkinAnalyzer
python -c "from database.connection import get_db_context; print('✅ DB OK')"

# Re-initialize database
python database/init_db.py
```

### Problem: COCO generation gagal

**Cause**: OpenCV tidak terinstall atau mask file corrupt.

**Solution**:
```bash
pip install opencv-python
pip install opencv-python-headless  # For server environments
```

---

## 📚 API Endpoints untuk History

### Retrieve History
```http
GET /api/v2/history?user_id=<user_id>&limit=50&offset=0

Response:
{
  "status": "success",
  "count": 10,
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "task_id": "xP12I2tU3...",
      "status": "success",
      "image_path": "dataset/images/...",
      "created_at": "2025-10-31T16:02:03.123456"
    },
    ...
  ]
}
```

### Get Single Analysis
```http
GET /api/v2/history/{analysis_id}

Response:
{
  "status": "success",
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "task_id": "xP12I2tU3...",
    "image_path": "dataset/images/...",
    "masks_path": [...],
    "coco_json_path": "dataset/annotations/...",
    "result_json": {...},
    "created_at": "2025-10-31T16:02:03.123456"
  }
}
```

### Download Image
```http
GET /api/v2/history/{analysis_id}/image?type=original
GET /api/v2/history/{analysis_id}/image?type=overlay

Response: Image file (JPEG)
```

### Download COCO JSON
```http
GET /api/v2/history/{analysis_id}/coco

Response: JSON file (COCO format)
```

---

## 🎓 COCO Format Example

```json
{
  "info": {
    "description": "Skin Analysis Dataset - Instance Segmentation",
    "version": "1.0",
    "year": 2025,
    "contributor": "YCE Skin Analyzer",
    "date_created": "2025-10-31T16:02:00Z"
  },
  "licenses": [
    {
      "id": 1,
      "name": "Attribution-NonCommercial-ShareAlike License",
      "url": "http://creativecommons.org/licenses/by-nc-sa/2.0/"
    }
  ],
  "images": [
    {
      "id": 1,
      "file_name": "xP12I2tU3_20251031_160200.jpg",
      "width": 720,
      "height": 720,
      "date_captured": "2025-10-31T16:02:00Z"
    }
  ],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 1,
      "segmentation": [[245,320,248,325,250,330,...]],
      "bbox": [240, 315, 25, 30],
      "area": 625,
      "iscrowd": 0
    },
    {
      "id": 2,
      "image_id": 1,
      "category_id": 1,
      "segmentation": [[180,200,185,205,190,210,...]],
      "bbox": [175, 195, 30, 35],
      "area": 875,
      "iscrowd": 0
    }
  ],
  "categories": [
    {
      "id": 1,
      "name": "acne",
      "supercategory": "skin_issue"
    },
    {
      "id": 2,
      "name": "pore",
      "supercategory": "skin_issue"
    },
    {
      "id": 3,
      "name": "wrinkle",
      "supercategory": "skin_issue"
    }
  ]
}
```

---

## 🚀 Next Steps

1. **Build UI for History**: Create page to display saved analyses
2. **Implement Filtering**: Add date range, status, user_id filters
3. **Export Dataset**: Create endpoint to download full dataset (images + COCO JSON)
4. **Training Pipeline**: Integrate with YOLO/Mask-RCNN/SegFormer training scripts
5. **Performance Optimization**: Add caching, batch processing, async operations
6. **Cloud Storage**: Optional integration with AWS S3/Azure Blob for file storage

---

## 📞 Support

For issues or questions:
- Check logs in both frontend (browser console) and backend (terminal)
- Review `TROUBLESHOOTING_DATABASE_SAVE.md` for common issues
- Run health check: `health_check.bat`
- Test endpoint: `python test_save_endpoint.py`

---

**Last Updated**: October 31, 2025  
**Version**: 2.0.0  
**Author**: YCE Development Team
