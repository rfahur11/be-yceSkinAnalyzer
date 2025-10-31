"""
API routes untuk skin analysis history
"""
from fastapi import APIRouter, HTTPException, Query, Depends, Body
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, Dict, Any
from pathlib import Path
import logging
import base64

from services.dataset_storage import DatasetStorageService
from services.recommendation_service import get_all_recommendations
from config.settings import IMAGES_DIR, OVERLAYS_DIR, ANNOTATIONS_DIR
from database.connection import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v2/history",
    tags=["History V2"]
)

dataset_service = DatasetStorageService()


@router.get("/")
async def get_analysis_history(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    limit: int = Query(50, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Retrieve analysis history.
    
    Query Parameters:
    - user_id: Optional user ID filter
    - limit: Max results (1-100, default 50)
    - offset: Pagination offset (default 0)
    
    Returns:
    - List of analysis records with metadata
    """
    try:
        history = dataset_service.get_analysis_history(
            user_id=user_id,
            limit=limit,
            offset=offset
        )
        
        return {
            "status": "success",
            "count": len(history),
            "data": history
        }
    
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{analysis_id}")
async def get_analysis_detail(analysis_id: str):
    """
    Get detailed information tentang specific analysis.
    
    Path Parameters:
    - analysis_id: UUID of the analysis
    
    Returns:
    - Complete analysis record with all metadata
    """
    try:
        analysis = dataset_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID {analysis_id} not found"
            )
        
        return {
            "status": "success",
            "data": analysis
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{analysis_id}/image")
async def get_analysis_image(
    analysis_id: str,
    type: str = Query("original", regex="^(original|overlay)$")
):
    """
    Download image dari specific analysis.
    
    Path Parameters:
    - analysis_id: UUID of the analysis
    
    Query Parameters:
    - type: "original" or "overlay" (default: original)
    
    Returns:
    - Image file
    """
    try:
        analysis = dataset_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID {analysis_id} not found"
            )
        
        if type == "overlay":
            image_path = analysis.get("overlay_path")
            if not image_path:
                raise HTTPException(
                    status_code=404,
                    detail="Overlay image not available"
                )
            # Reconstruct full path
            full_path = OVERLAYS_DIR.parent / image_path
        else:
            image_path = analysis.get("image_path")
            if not image_path:
                raise HTTPException(
                    status_code=404,
                    detail="Original image not available"
                )
            # Reconstruct full path
            full_path = IMAGES_DIR.parent / image_path
        
        if not full_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Image file not found: {full_path}"
            )
        
        return FileResponse(
            path=str(full_path),
            media_type="image/jpeg",
            filename=full_path.name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{analysis_id}/coco")
async def get_analysis_coco(analysis_id: str):
    """
    Download COCO annotation JSON untuk specific analysis.
    
    Path Parameters:
    - analysis_id: UUID of the analysis
    
    Returns:
    - COCO JSON file
    """
    try:
        analysis = dataset_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID {analysis_id} not found"
            )
        
        coco_path = analysis.get("coco_json_path")
        if not coco_path:
            raise HTTPException(
                status_code=404,
                detail="COCO annotation not available"
            )
        
        # Reconstruct full path
        full_path = ANNOTATIONS_DIR.parent / coco_path
        
        if not full_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"COCO file not found: {full_path}"
            )
        
        return FileResponse(
            path=str(full_path),
            media_type="application/json",
            filename=full_path.name
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting COCO annotation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{analysis_id}/result-json")
async def get_analysis_result_json(analysis_id: str):
    """
    Get raw result JSON dari Perfect Corp API.
    
    Path Parameters:
    - analysis_id: UUID of the analysis
    
    Returns:
    - JSON response dari Perfect Corp
    """
    try:
        analysis = dataset_service.get_analysis_by_id(analysis_id)
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail=f"Analysis with ID {analysis_id} not found"
            )
        
        result_json = analysis.get("result_json")
        if not result_json:
            raise HTTPException(
                status_code=404,
                detail="Result JSON not available"
            )
        
        return JSONResponse(content=result_json)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting result JSON: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save-from-frontend")
async def save_analysis_from_frontend(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """
    Save analysis result yang sudah di-download oleh frontend.
    Endpoint ini dipanggil dari Next.js setelah download ZIP.
    
    Request Body:
    {
        "task_id": "string",
        "file_id": "string (optional)",
        "result_url": "string",
        "original_image_base64": "string",
        "result_data": {...},
        "user_id": "string (optional)"
    }
    
    Returns:
    - Saved analysis info + skin care recommendations
    """
    try:
        logger.info("=" * 80)
        logger.info("📥 Received save request from frontend")
        logger.info(f"Payload keys: {list(payload.keys())}")
        
        task_id = payload.get("task_id")
        file_id = payload.get("file_id")
        result_url = payload.get("result_url")
        original_image_base64 = payload.get("original_image_base64")
        result_data = payload.get("result_data", {})
        user_id = payload.get("user_id")
        
        logger.info(f"📋 task_id: {task_id}")
        logger.info(f"📋 file_id: {file_id}")
        logger.info(f"📋 result_url: {result_url[:100] if result_url else None}...")
        logger.info(f"📋 user_id: {user_id}")
        logger.info(f"📋 has original_image_base64: {bool(original_image_base64)}")
        logger.info(f"📋 result_data keys: {list(result_data.keys()) if result_data else None}")
        
        if not task_id or not result_url or not original_image_base64:
            logger.error("❌ Missing required fields!")
            raise HTTPException(
                status_code=400,
                detail="Missing required fields: task_id, result_url, original_image_base64"
            )
        
        # Decode base64 image
        try:
            logger.info("🔄 Decoding base64 image...")
            # Remove data URL prefix if exists
            if "," in original_image_base64:
                original_image_base64 = original_image_base64.split(",")[1]
            
            original_image_data = base64.b64decode(original_image_base64)
            logger.info(f"✅ Image decoded, size: {len(original_image_data)} bytes")
        except Exception as e:
            logger.error(f"❌ Error decoding base64: {e}")
            raise HTTPException(
                status_code=400,
                detail=f"Invalid base64 image data: {e}"
            )
        
        logger.info(f"🚀 Calling dataset_service.process_and_save_analysis for task_id: {task_id}")
        
        # Call dataset storage service
        dataset_info = await dataset_service.process_and_save_analysis(
            task_id=task_id,
            file_id=file_id,
            result_url=result_url,
            original_image_data=original_image_data,
            result_json=result_data,
            user_id=user_id
        )
        
        logger.info(f"✅ Analysis saved successfully! ID: {dataset_info.get('id')}")
        
        # ==================== GET RECOMMENDATIONS ====================
        recommendations = []
        try:
            logger.info("🔍 Generating ingredient & product recommendations...")
            
            # Extract score_info from result_data
            score_info = result_data.get("score_info", {})
            
            if score_info:
                logger.info(f"📊 Found {len(score_info)} conditions in score_info")
                
                # Generate recommendations for all conditions
                recommendations = get_all_recommendations(db, score_info)
                
                logger.info(
                    f"✅ Generated {len(recommendations)} recommendation sets"
                )
            else:
                logger.warning("⚠️ No score_info found in result_data, skipping recommendations")
        
        except Exception as rec_error:
            logger.error(f"❌ Error generating recommendations: {rec_error}", exc_info=True)
            # Don't fail the entire request if recommendations fail
            recommendations = []
        
        # ============================================================
        
        logger.info("=" * 80)
        
        return {
            "status": "success",
            "message": "Analysis saved to database and dataset",
            "data": dataset_info,
            "recommendations": recommendations  # 🆕 Added recommendations
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error saving analysis from frontend: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
