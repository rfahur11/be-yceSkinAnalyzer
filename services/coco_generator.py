"""
Service untuk generate COCO format JSON dari mask images.
Mengkonversi mask PNG menjadi polygon segmentation.
"""
import cv2
import numpy as np
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime
from config.settings import COCO_CATEGORIES

logger = logging.getLogger(__name__)


class COCOGenerator:
    """
    Generator untuk membuat COCO Instance Segmentation format
    dari mask images hasil Perfect Corp API.
    """
    
    def __init__(self):
        self.annotation_id = 1
        self.image_id = 1
    
    def mask_to_polygons(
        self, 
        mask_path: Path, 
        tolerance: float = 2.0
    ) -> List[List[float]]:
        """
        Convert binary mask image ke polygon segmentation format.
        
        Args:
            mask_path: Path ke mask image (PNG grayscale/binary)
            tolerance: Tolerance untuk polygon approximation (default 2.0)
            
        Returns:
            List of polygons dalam format [x1,y1,x2,y2,...,xn,yn]
            Bisa return multiple polygons jika ada multiple regions
        """
        try:
            # Read mask image
            mask = cv2.imread(str(mask_path), cv2.IMREAD_GRAYSCALE)
            if mask is None:
                logger.error(f"Failed to read mask: {mask_path}")
                return []
            
            # Threshold to ensure binary mask
            _, binary_mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
            
            # Find contours
            contours, _ = cv2.findContours(
                binary_mask, 
                cv2.RETR_EXTERNAL,  # Only external contours
                cv2.CHAIN_APPROX_SIMPLE
            )
            
            polygons = []
            for contour in contours:
                # Filter small contours (noise)
                if cv2.contourArea(contour) < 10:
                    continue
                
                # Approximate polygon
                epsilon = tolerance
                approx = cv2.approxPolyDP(contour, epsilon, True)
                
                # Convert to flat list [x1,y1,x2,y2,...]
                polygon = approx.flatten().tolist()
                
                # COCO requires at least 6 coordinates (3 points)
                if len(polygon) >= 6:
                    polygons.append(polygon)
            
            return polygons
            
        except Exception as e:
            logger.error(f"Error converting mask to polygon: {e}")
            return []
    
    def calculate_bbox_from_polygon(
        self, 
        polygon: List[float]
    ) -> Tuple[float, float, float, float]:
        """
        Calculate bounding box dari polygon.
        
        Args:
            polygon: Flat list [x1,y1,x2,y2,...,xn,yn]
            
        Returns:
            Tuple (x, y, width, height) dalam format COCO bbox
        """
        # Extract x and y coordinates
        x_coords = polygon[0::2]
        y_coords = polygon[1::2]
        
        x_min = min(x_coords)
        x_max = max(x_coords)
        y_min = min(y_coords)
        y_max = max(y_coords)
        
        width = x_max - x_min
        height = y_max - y_min
        
        return (x_min, y_min, width, height)
    
    def calculate_area_from_polygon(
        self, 
        polygon: List[float]
    ) -> float:
        """
        Calculate area dari polygon menggunakan Shoelace formula.
        
        Args:
            polygon: Flat list [x1,y1,x2,y2,...,xn,yn]
            
        Returns:
            Area dalam pixels
        """
        x_coords = polygon[0::2]
        y_coords = polygon[1::2]
        
        n = len(x_coords)
        area = 0.0
        
        for i in range(n):
            j = (i + 1) % n
            area += x_coords[i] * y_coords[j]
            area -= x_coords[j] * y_coords[i]
        
        return abs(area) / 2.0
    
    def create_annotation(
        self,
        polygons: List[List[float]],
        category_id: int,
        image_id: int,
        iscrowd: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Create COCO annotation objects dari polygons.
        
        Args:
            polygons: List of polygon segmentations
            category_id: COCO category ID
            image_id: Image ID
            iscrowd: 0 for polygon, 1 for RLE (default 0)
            
        Returns:
            List of annotation dicts
        """
        annotations = []
        
        for polygon in polygons:
            # Calculate bbox and area
            bbox = self.calculate_bbox_from_polygon(polygon)
            area = self.calculate_area_from_polygon(polygon)
            
            annotation = {
                "id": self.annotation_id,
                "image_id": image_id,
                "category_id": category_id,
                "segmentation": [polygon],  # COCO format expects list of polygons
                "area": area,
                "bbox": bbox,  # [x, y, width, height]
                "iscrowd": iscrowd
            }
            
            annotations.append(annotation)
            self.annotation_id += 1
        
        return annotations
    
    def generate_coco_json(
        self,
        image_filename: str,
        image_width: int,
        image_height: int,
        masks_info: List[Dict[str, Any]],
        output_path: Path
    ) -> Dict[str, Any]:
        """
        Generate complete COCO JSON untuk single image analysis.
        
        Args:
            image_filename: Original image filename
            image_width: Image width
            image_height: Image height
            masks_info: List of dicts with keys: 
                - mask_path: Path to mask file
                - category_name: Category name (acne, wrinkle, etc)
            output_path: Path untuk save JSON file
            
        Returns:
            COCO format dict
        """
        # Create info section
        info = {
            "description": "YCE Skin Analysis Dataset",
            "version": "1.0",
            "year": datetime.now().year,
            "contributor": "YCE Skin Analyzer",
            "date_created": datetime.now().isoformat()
        }
        
        # Create licenses section
        licenses = [
            {
                "id": 1,
                "name": "Proprietary",
                "url": ""
            }
        ]
        
        # Create image entry
        image_entry = {
            "id": self.image_id,
            "file_name": image_filename,
            "width": image_width,
            "height": image_height,
            "date_captured": datetime.now().isoformat()
        }
        
        # Process masks and create annotations
        annotations = []
        
        for mask_info in masks_info:
            mask_path = mask_info.get("mask_path")
            category_name = mask_info.get("category_name")
            
            if not mask_path or not category_name:
                logger.warning(f"Skipping invalid mask_info: {mask_info}")
                continue
            
            # Find category ID
            category_id = None
            for cat in COCO_CATEGORIES:
                if cat["name"] == category_name:
                    category_id = cat["id"]
                    break
            
            if category_id is None:
                logger.warning(f"Category not found: {category_name}")
                continue
            
            # Convert mask to polygons
            polygons = self.mask_to_polygons(Path(mask_path))
            
            if not polygons:
                logger.warning(f"No polygons found in mask: {mask_path}")
                continue
            
            # Create annotations
            mask_annotations = self.create_annotation(
                polygons=polygons,
                category_id=category_id,
                image_id=self.image_id,
                iscrowd=0
            )
            
            annotations.extend(mask_annotations)
        
        # Build COCO dict
        coco_dict = {
            "info": info,
            "licenses": licenses,
            "images": [image_entry],
            "annotations": annotations,
            "categories": COCO_CATEGORIES
        }
        
        # Save to file
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(coco_dict, f, indent=2, ensure_ascii=False)
            logger.info(f"COCO JSON saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving COCO JSON: {e}")
            raise
        
        # Increment image ID for next image
        self.image_id += 1
        
        return coco_dict
    
    def merge_coco_datasets(
        self,
        coco_files: List[Path],
        output_path: Path
    ) -> Dict[str, Any]:
        """
        Merge multiple COCO JSON files into one master dataset.
        Useful untuk create single dataset dari multiple analyses.
        
        Args:
            coco_files: List of paths ke COCO JSON files
            output_path: Path untuk save merged JSON
            
        Returns:
            Merged COCO dict
        """
        merged = {
            "info": {
                "description": "YCE Skin Analysis Merged Dataset",
                "version": "1.0",
                "year": datetime.now().year,
                "contributor": "YCE Skin Analyzer",
                "date_created": datetime.now().isoformat()
            },
            "licenses": [
                {
                    "id": 1,
                    "name": "Proprietary",
                    "url": ""
                }
            ],
            "images": [],
            "annotations": [],
            "categories": COCO_CATEGORIES
        }
        
        image_id_offset = 0
        annotation_id_offset = 0
        
        for coco_file in coco_files:
            try:
                with open(coco_file, 'r', encoding='utf-8') as f:
                    coco_data = json.load(f)
                
                # Remap image IDs
                for img in coco_data.get("images", []):
                    old_id = img["id"]
                    img["id"] = old_id + image_id_offset
                    merged["images"].append(img)
                
                # Remap annotation IDs and image IDs
                for ann in coco_data.get("annotations", []):
                    ann["id"] = ann["id"] + annotation_id_offset
                    ann["image_id"] = ann["image_id"] + image_id_offset
                    merged["annotations"].append(ann)
                
                # Update offsets
                if coco_data.get("images"):
                    max_img_id = max(img["id"] for img in coco_data["images"])
                    image_id_offset = max_img_id
                
                if coco_data.get("annotations"):
                    max_ann_id = max(ann["id"] for ann in coco_data["annotations"])
                    annotation_id_offset = max_ann_id
                
            except Exception as e:
                logger.error(f"Error merging COCO file {coco_file}: {e}")
                continue
        
        # Save merged dataset
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(merged, f, indent=2, ensure_ascii=False)
            logger.info(f"Merged COCO JSON saved to: {output_path}")
        except Exception as e:
            logger.error(f"Error saving merged COCO JSON: {e}")
            raise
        
        return merged
