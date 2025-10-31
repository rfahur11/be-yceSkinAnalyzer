"""
Service untuk menyimpan hasil analisis sebagai dataset.
Handle download ZIP dari Perfect Corp, extract masks, generate COCO, dan save to database.
"""
import aiofiles
import requests
import zipfile
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from PIL import Image

from config.settings import (
    IMAGES_DIR, MASKS_DIR, ANNOTATIONS_DIR, OVERLAYS_DIR
)
from services.coco_generator import COCOGenerator
from database.connection import get_db_context
from database.models import SkinAnalysisHistory

logger = logging.getLogger(__name__)


class DatasetStorageService:
    """
    Service untuk handle storage hasil analisis sebagai dataset.
    """
    
    def __init__(self):
        self.coco_generator = COCOGenerator()
    
    async def download_and_extract_results(
        self,
        result_url: str,
        task_id: str
    ) -> Path:
        """
        Download ZIP hasil analisis dari Perfect Corp dan extract.
        
        Args:
            result_url: URL ke ZIP file
            task_id: Task ID untuk naming folder
            
        Returns:
            Path ke folder extracted files
        """
        try:
            # Create temp directory untuk task ini
            task_dir = MASKS_DIR / task_id
            task_dir.mkdir(parents=True, exist_ok=True)
            
            # Download ZIP file
            logger.info(f"Downloading results from: {result_url}")
            response = requests.get(result_url, timeout=60)
            response.raise_for_status()
            
            # Save ZIP temporarily
            zip_path = task_dir / "results.zip"
            async with aiofiles.open(zip_path, 'wb') as f:
                await f.write(response.content)
            
            # Extract ZIP
            logger.info(f"Extracting ZIP to: {task_dir}")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(task_dir)
            
            # Remove ZIP file
            zip_path.unlink()
            
            logger.info(f"Results extracted to: {task_dir}")
            return task_dir
            
        except Exception as e:
            logger.error(f"Error downloading/extracting results: {e}")
            raise
    
    def identify_mask_files(
        self,
        extracted_dir: Path
    ) -> Dict[str, Path]:
        """
        Identify mask files dari extracted directory.
        Perfect Corp biasanya return files dengan naming pattern tertentu.
        
        Args:
            extracted_dir: Path ke folder hasil extract
            
        Returns:
            Dict mapping category_name -> mask_file_path
        """
        mask_files = {}
        
        # Mapping dari Perfect Corp filename patterns ke category names
        # Adjust sesuai dengan actual output dari Perfect Corp API
        pattern_mapping = {
            "acne": ["acne", "pimple", "blemish"],
            "wrinkle": ["wrinkle", "line", "fine_line"],
            "pore": ["pore", "enlarged_pore"],
            "dark_spot": ["dark_spot", "spot", "pigmentation", "melasma"],
            "dark_circle": ["dark_circle", "eye_dark"],
            "eye_bag": ["eye_bag", "bag"],
            "redness": ["redness", "red"],
        }
        
        # Scan all PNG files in directory
        for file_path in extracted_dir.rglob("*.png"):
            filename_lower = file_path.stem.lower()
            
            # Try to match dengan category patterns
            for category, patterns in pattern_mapping.items():
                for pattern in patterns:
                    if pattern in filename_lower:
                        mask_files[category] = file_path
                        logger.info(f"Identified mask: {category} -> {file_path.name}")
                        break
        
        return mask_files
    
    async def save_original_image(
        self,
        image_data: bytes,
        task_id: str
    ) -> tuple[Path, int, int]:
        """
        Save original image dan return path + dimensions.
        
        Args:
            image_data: Raw image bytes
            task_id: Task ID untuk naming
            
        Returns:
            Tuple (image_path, width, height)
        """
        try:
            # Generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            image_filename = f"{task_id}_{timestamp}.jpg"
            image_path = IMAGES_DIR / image_filename
            
            # Save image
            async with aiofiles.open(image_path, 'wb') as f:
                await f.write(image_data)
            
            # Get dimensions
            with Image.open(image_path) as img:
                width, height = img.size
            
            logger.info(f"Original image saved: {image_path} ({width}x{height})")
            return image_path, width, height
            
        except Exception as e:
            logger.error(f"Error saving original image: {e}")
            raise
    
    def create_overlay_visualization(
        self,
        original_image_path: Path,
        mask_files: Dict[str, Path],
        output_path: Path
    ) -> Path:
        """
        Create visualization dengan overlay masks pada original image.
        
        Args:
            original_image_path: Path ke original image
            mask_files: Dict mapping category -> mask_path
            output_path: Path untuk save overlay image
            
        Returns:
            Path ke overlay image
        """
        try:
            # Load original image
            original = Image.open(original_image_path).convert('RGBA')
            width, height = original.size
            
            # Create overlay layer
            overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
            
            # Color mapping untuk categories
            color_mapping = {
                "acne": (255, 0, 0, 100),      # Red
                "wrinkle": (255, 165, 0, 100),  # Orange
                "pore": (255, 255, 0, 100),     # Yellow
                "dark_spot": (128, 0, 128, 100), # Purple
                "dark_circle": (0, 0, 255, 100), # Blue
                "eye_bag": (0, 255, 255, 100),   # Cyan
                "redness": (255, 0, 255, 100),   # Magenta
            }
            
            # Overlay each mask
            for category, mask_path in mask_files.items():
                try:
                    mask = Image.open(mask_path).convert('L')
                    mask = mask.resize((width, height), Image.Resampling.LANCZOS)
                    
                    # Create colored overlay untuk category ini
                    color = color_mapping.get(category, (255, 255, 255, 100))
                    colored_mask = Image.new('RGBA', (width, height), color)
                    
                    # Apply mask as alpha
                    overlay.paste(colored_mask, (0, 0), mask)
                    
                except Exception as e:
                    logger.warning(f"Error overlaying mask {category}: {e}")
                    continue
            
            # Composite
            result = Image.alpha_composite(original, overlay)
            
            # Convert to RGB and save
            result_rgb = result.convert('RGB')
            output_path.parent.mkdir(parents=True, exist_ok=True)
            result_rgb.save(output_path, 'JPEG', quality=95)
            
            logger.info(f"Overlay visualization saved: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating overlay visualization: {e}")
            raise
    
    async def process_and_save_analysis(
        self,
        task_id: str,
        file_id: Optional[str],
        result_url: str,
        original_image_data: bytes,
        result_json: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main function untuk process dan save complete analysis sebagai dataset.
        
        Args:
            task_id: Task ID dari Perfect Corp
            file_id: File ID dari upload (optional)
            result_url: URL ke ZIP results
            original_image_data: Original image bytes
            result_json: Full JSON response dari Perfect Corp
            user_id: User ID (optional)
            
        Returns:
            Dict dengan informasi saved analysis
        """
        try:
            logger.info(f"Processing analysis for task_id: {task_id}")
            
            # 1. Save original image
            image_path, width, height = await self.save_original_image(
                original_image_data, task_id
            )
            
            # 2. Download dan extract results
            extracted_dir = await self.download_and_extract_results(
                result_url, task_id
            )
            
            # 3. Identify mask files
            mask_files = self.identify_mask_files(extracted_dir)
            
            if not mask_files:
                logger.warning(f"No mask files found for task {task_id}")
            
            # 4. Create overlay visualization
            overlay_filename = f"{task_id}_overlay.jpg"
            overlay_path = OVERLAYS_DIR / overlay_filename
            
            if mask_files:
                self.create_overlay_visualization(
                    image_path, mask_files, overlay_path
                )
            
            # 5. Generate COCO JSON
            masks_info = []
            masks_path_list = []
            
            for category_name, mask_path in mask_files.items():
                masks_info.append({
                    "mask_path": mask_path,
                    "category_name": category_name
                })
                # Store relative path untuk database
                masks_path_list.append(str(mask_path.relative_to(MASKS_DIR.parent)))
            
            coco_filename = f"{task_id}_coco.json"
            coco_path = ANNOTATIONS_DIR / coco_filename
            
            if masks_info:
                self.coco_generator.generate_coco_json(
                    image_filename=image_path.name,
                    image_width=width,
                    image_height=height,
                    masks_info=masks_info,
                    output_path=coco_path
                )
            
            # 6. Save to database
            with get_db_context() as db:
                analysis_record = SkinAnalysisHistory(
                    file_id=file_id,
                    task_id=task_id,
                    status="success",
                    image_path=str(image_path.relative_to(IMAGES_DIR.parent)),
                    masks_path=masks_path_list,
                    overlay_path=str(overlay_path.relative_to(OVERLAYS_DIR.parent)),
                    coco_json_path=str(coco_path.relative_to(ANNOTATIONS_DIR.parent)),
                    result_zip_url=result_url,
                    result_json=result_json,
                    image_width=width,
                    image_height=height,
                    user_id=user_id
                )
                
                db.add(analysis_record)
                db.commit()
                db.refresh(analysis_record)
                
                logger.info(f"Analysis saved to database: {analysis_record.id}")
                
                return {
                    "id": str(analysis_record.id),
                    "task_id": task_id,
                    "status": "success",
                    "image_path": str(image_path),
                    "masks_count": len(mask_files),
                    "coco_json_path": str(coco_path),
                    "overlay_path": str(overlay_path),
                    "created_at": analysis_record.created_at.isoformat()
                }
        
        except Exception as e:
            logger.error(f"Error processing analysis: {e}")
            
            # Save error to database
            try:
                with get_db_context() as db:
                    error_record = SkinAnalysisHistory(
                        file_id=file_id,
                        task_id=task_id,
                        status="error",
                        error_message=str(e),
                        result_json=result_json,
                        user_id=user_id
                    )
                    db.add(error_record)
                    db.commit()
            except Exception as db_error:
                logger.error(f"Error saving error record: {db_error}")
            
            raise
    
    def get_analysis_history(
        self,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Retrieve analysis history dari database.
        
        Args:
            user_id: Filter by user_id (optional)
            limit: Max results
            offset: Offset for pagination
            
        Returns:
            List of analysis records
        """
        try:
            with get_db_context() as db:
                query = db.query(SkinAnalysisHistory)
                
                if user_id:
                    query = query.filter(SkinAnalysisHistory.user_id == user_id)
                
                query = query.order_by(SkinAnalysisHistory.created_at.desc())
                query = query.limit(limit).offset(offset)
                
                results = query.all()
                
                return [record.to_dict() for record in results]
        
        except Exception as e:
            logger.error(f"Error getting analysis history: {e}")
            raise
    
    def get_analysis_by_id(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific analysis by ID.
        
        Args:
            analysis_id: Analysis UUID
            
        Returns:
            Analysis record dict or None
        """
        try:
            with get_db_context() as db:
                record = db.query(SkinAnalysisHistory).filter(
                    SkinAnalysisHistory.id == analysis_id
                ).first()
                
                if record:
                    return record.to_dict()
                return None
        
        except Exception as e:
            logger.error(f"Error getting analysis by ID: {e}")
            raise
