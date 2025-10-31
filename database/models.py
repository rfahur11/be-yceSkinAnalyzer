"""
Database models untuk skin analysis history dan dataset
"""
from sqlalchemy import Column, String, JSON, DateTime, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from database.connection import Base


class SkinAnalysisHistory(Base):
    """
    Model untuk menyimpan riwayat analisis kulit.
    Menyimpan reference ke file gambar, masks, COCO annotation, dan hasil analisis.
    """
    __tablename__ = "skin_analysis_history"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Task & File identifiers
    file_id = Column(String(255), nullable=True, index=True, comment="File ID dari Perfect Corp upload")
    task_id = Column(String(255), nullable=False, index=True, comment="Task ID dari Perfect Corp analysis")
    
    # Status tracking
    status = Column(
        String(50), 
        nullable=False, 
        default="processing",
        comment="Status: processing, success, error"
    )
    
    # File paths (relative to dataset directory)
    image_path = Column(String(500), nullable=True, comment="Path gambar original")
    masks_path = Column(JSON, nullable=True, comment="Array paths ke mask files")
    overlay_path = Column(String(500), nullable=True, comment="Path gambar dengan overlay annotation")
    coco_json_path = Column(String(500), nullable=True, comment="Path ke COCO JSON file")
    result_zip_url = Column(Text, nullable=True, comment="URL hasil ZIP dari Perfect Corp")
    
    # Analysis results
    result_json = Column(JSON, nullable=True, comment="Full JSON response dari Perfect Corp API")
    
    # Image metadata
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
    
    # Error handling
    error_message = Column(Text, nullable=True, comment="Error message jika status = error")
    
    # User tracking (optional, untuk multi-user system)
    user_id = Column(String(255), nullable=True, index=True, comment="User ID (optional)")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<SkinAnalysisHistory(id={self.id}, task_id={self.task_id}, status={self.status})>"
    
    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": str(self.id),
            "file_id": self.file_id,
            "task_id": self.task_id,
            "status": self.status,
            "image_path": self.image_path,
            "masks_path": self.masks_path,
            "overlay_path": self.overlay_path,
            "coco_json_path": self.coco_json_path,
            "result_zip_url": self.result_zip_url,
            "result_json": self.result_json,
            "image_width": self.image_width,
            "image_height": self.image_height,
            "error_message": self.error_message,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class COCODatasetMetadata(Base):
    """
    Model untuk tracking COCO dataset metadata.
    Digunakan untuk generate master coco.json yang menggabungkan semua analisis.
    """
    __tablename__ = "coco_dataset_metadata"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Dataset info
    dataset_version = Column(String(50), nullable=False, default="1.0")
    total_images = Column(Integer, default=0)
    total_annotations = Column(Integer, default=0)
    
    # COCO master file path
    master_coco_path = Column(String(500), nullable=True, comment="Path ke master COCO JSON")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<COCODatasetMetadata(version={self.dataset_version}, images={self.total_images})>"
