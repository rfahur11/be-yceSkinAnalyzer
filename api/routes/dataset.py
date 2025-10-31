"""
API routes untuk download complete dataset
"""
from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse
import zipfile
import logging
from pathlib import Path
from datetime import datetime
import json
from typing import Optional

from services.coco_generator import COCOGenerator
from services.dataset_storage import DatasetStorageService
from config.settings import DATASET_DIR, ANNOTATIONS_DIR

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v2/dataset",
    tags=["Dataset V2"]
)

dataset_service = DatasetStorageService()
coco_generator = COCOGenerator()


@router.get("/download")
async def download_complete_dataset(
    background_tasks: BackgroundTasks,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    format: str = Query("zip", regex="^(zip|files)$", description="Download format")
):
    """
    Download complete dataset dengan images, masks, dan COCO annotations.
    
    Query Parameters:
    - user_id: Optional user ID filter
    - format: "zip" untuk download as ZIP, "files" untuk list files only
    
    Returns:
    - ZIP file containing complete dataset or JSON list of files
    """
    try:
        # Get all analysis records
        history = dataset_service.get_analysis_history(
            user_id=user_id,
            limit=10000  # Get all
        )
        
        if not history:
            raise HTTPException(
                status_code=404,
                detail="No analysis found in database"
            )
        
        if format == "files":
            # Return list of files only
            file_list = {
                "images": [],
                "masks": [],
                "annotations": [],
                "overlays": []
            }
            
            for record in history:
                if record.get("image_path"):
                    file_list["images"].append(record["image_path"])
                if record.get("masks_path"):
                    file_list["masks"].extend(record["masks_path"])
                if record.get("coco_json_path"):
                    file_list["annotations"].append(record["coco_json_path"])
                if record.get("overlay_path"):
                    file_list["overlays"].append(record["overlay_path"])
            
            return {
                "status": "success",
                "total_analyses": len(history),
                "files": file_list
            }
        
        # Create ZIP file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"yce_skin_dataset_{timestamp}.zip"
        zip_path = DATASET_DIR / zip_filename
        
        logger.info(f"Creating dataset ZIP: {zip_path}")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add README
            readme_content = f"""YCE Skin Analysis Dataset
Generated: {datetime.now().isoformat()}
Total Analyses: {len(history)}

Dataset Structure:
- images/          : Original face images
- masks/           : Mask images for each skin issue category
- annotations/     : COCO format JSON annotations
- overlays/        : Visualization images with overlay masks

Categories:
- acne
- wrinkle
- pore
- dark_spot
- dark_circle
- eye_bag
- redness

Usage:
This dataset can be used for training skin analysis models using:
- YOLO (object detection)
- Mask R-CNN (instance segmentation)
- SegFormer (semantic segmentation)
- U-Net (segmentation)

COCO Format:
The annotations follow COCO Instance Segmentation format with:
- Polygon segmentations
- Bounding boxes
- Category labels
- Area calculations
"""
            zipf.writestr("README.txt", readme_content)
            
            # Collect all COCO files untuk merge
            coco_files = []
            
            # Add files dari each analysis
            for record in history:
                try:
                    # Add image
                    if record.get("image_path"):
                        img_full_path = DATASET_DIR / record["image_path"]
                        if img_full_path.exists():
                            zipf.write(img_full_path, f"images/{img_full_path.name}")
                    
                    # Add masks
                    if record.get("masks_path"):
                        for mask_rel_path in record["masks_path"]:
                            mask_full_path = DATASET_DIR / mask_rel_path
                            if mask_full_path.exists():
                                # Preserve directory structure for masks
                                zipf.write(
                                    mask_full_path,
                                    f"masks/{mask_full_path.parent.name}/{mask_full_path.name}"
                                )
                    
                    # Add COCO annotation
                    if record.get("coco_json_path"):
                        coco_full_path = DATASET_DIR / record["coco_json_path"]
                        if coco_full_path.exists():
                            zipf.write(
                                coco_full_path,
                                f"annotations/{coco_full_path.name}"
                            )
                            coco_files.append(coco_full_path)
                    
                    # Add overlay
                    if record.get("overlay_path"):
                        overlay_full_path = DATASET_DIR / record["overlay_path"]
                        if overlay_full_path.exists():
                            zipf.write(
                                overlay_full_path,
                                f"overlays/{overlay_full_path.name}"
                            )
                
                except Exception as e:
                    logger.warning(f"Error adding files for record {record.get('id')}: {e}")
                    continue
            
            # Create merged COCO JSON
            if coco_files:
                try:
                    logger.info(f"Merging {len(coco_files)} COCO files")
                    merged_coco_path = ANNOTATIONS_DIR / f"merged_dataset_{timestamp}.json"
                    merged_coco = coco_generator.merge_coco_datasets(
                        coco_files,
                        merged_coco_path
                    )
                    zipf.write(merged_coco_path, "annotations/coco_merged.json")
                    
                    # Add dataset stats
                    stats = {
                        "total_images": len(merged_coco.get("images", [])),
                        "total_annotations": len(merged_coco.get("annotations", [])),
                        "categories": merged_coco.get("categories", []),
                        "generated_at": datetime.now().isoformat()
                    }
                    zipf.writestr(
                        "annotations/dataset_stats.json",
                        json.dumps(stats, indent=2)
                    )
                except Exception as e:
                    logger.error(f"Error creating merged COCO: {e}")
        
        logger.info(f"Dataset ZIP created: {zip_path}")
        
        # Schedule cleanup after download
        def cleanup_zip():
            try:
                if zip_path.exists():
                    zip_path.unlink()
                    logger.info(f"Cleaned up ZIP: {zip_path}")
            except Exception as e:
                logger.error(f"Error cleaning up ZIP: {e}")
        
        background_tasks.add_task(cleanup_zip)
        
        return FileResponse(
            path=str(zip_path),
            media_type="application/zip",
            filename=zip_filename,
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating dataset download: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_dataset_stats(
    user_id: Optional[str] = Query(None, description="Filter by user ID")
):
    """
    Get statistics tentang current dataset.
    
    Query Parameters:
    - user_id: Optional user ID filter
    
    Returns:
    - Dataset statistics
    """
    try:
        history = dataset_service.get_analysis_history(
            user_id=user_id,
            limit=10000
        )
        
        stats = {
            "total_analyses": len(history),
            "successful": len([h for h in history if h.get("status") == "success"]),
            "failed": len([h for h in history if h.get("status") == "error"]),
            "processing": len([h for h in history if h.get("status") == "processing"]),
            "categories": {}
        }
        
        # Count masks by category
        for record in history:
            if record.get("masks_path"):
                for mask_path in record["masks_path"]:
                    # Extract category dari path
                    for category in ["acne", "wrinkle", "pore", "dark_spot", 
                                   "dark_circle", "eye_bag", "redness"]:
                        if category in mask_path.lower():
                            stats["categories"][category] = stats["categories"].get(category, 0) + 1
        
        return {
            "status": "success",
            "data": stats
        }
    
    except Exception as e:
        logger.error(f"Error getting dataset stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
