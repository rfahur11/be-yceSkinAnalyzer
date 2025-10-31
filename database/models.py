"""
Database models untuk skin analysis history, dataset, dan recommendation system
"""
from sqlalchemy import Column, String, JSON, DateTime, Text, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
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


# ==================== RECOMMENDATION SYSTEM MODELS ====================

class SeverityLevel(Base):
    """
    Model untuk severity levels (Poor, Fair, Good).
    Mapping score range ke level kondisi kulit.
    """
    __tablename__ = "severity_levels"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True, comment="Poor, Fair, Good")
    description = Column(Text, nullable=True)
    min_score = Column(Integer, nullable=False, comment="Minimum score (inclusive)")
    max_score = Column(Integer, nullable=False, comment="Maximum score (inclusive)")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    condition_mappings = relationship("ConditionIngredient", back_populates="severity")
    
    def __repr__(self):
        return f"<SeverityLevel(name={self.name}, range={self.min_score}-{self.max_score})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "min_score": self.min_score,
            "max_score": self.max_score
        }
    
    @classmethod
    def get_severity_by_score(cls, db, score: int):
        """Get severity level based on score"""
        return db.query(cls).filter(
            cls.min_score <= score,
            cls.max_score >= score
        ).first()


class Condition(Base):
    """
    Model untuk kondisi kulit (acne, wrinkle, pore, etc).
    """
    __tablename__ = "conditions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True, comment="acne, wrinkle, pore, etc")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    condition_mappings = relationship("ConditionIngredient", back_populates="condition")
    
    def __repr__(self):
        return f"<Condition(name={self.name})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description
        }


class Ingredient(Base):
    """
    Model untuk bahan aktif (ingredients) untuk perawatan kulit.
    """
    __tablename__ = "ingredients"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True, comment="Brand/commercial name")
    generic_name = Column(String(255), nullable=True, index=True, comment="Generic/scientific name")
    benefit = Column(Text, nullable=False, comment="Benefits description")
    warnings = Column(Text, nullable=True, comment="Usage warnings or side effects")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    condition_mappings = relationship("ConditionIngredient", back_populates="ingredient")
    products = relationship("Product", back_populates="ingredient")
    
    def __repr__(self):
        return f"<Ingredient(name={self.name}, generic={self.generic_name})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "generic_name": self.generic_name,
            "benefit": self.benefit,
            "warnings": self.warnings
        }


class ConditionIngredient(Base):
    """
    Model untuk mapping antara kondisi, severity, dan ingredient.
    Menentukan ingredient apa yang direkomendasikan untuk kondisi tertentu dengan severity tertentu.
    """
    __tablename__ = "condition_ingredients"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    condition_id = Column(Integer, ForeignKey('conditions.id', ondelete='CASCADE'), nullable=False, index=True)
    severity_id = Column(Integer, ForeignKey('severity_levels.id', ondelete='CASCADE'), nullable=False, index=True)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id', ondelete='CASCADE'), nullable=False, index=True)
    suggested_use = Column(Text, nullable=True, comment="How to use this ingredient")
    priority = Column(Integer, default=1, comment="1=highest priority")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    condition = relationship("Condition", back_populates="condition_mappings")
    severity = relationship("SeverityLevel", back_populates="condition_mappings")
    ingredient = relationship("Ingredient", back_populates="condition_mappings")
    
    def __repr__(self):
        return f"<ConditionIngredient(condition_id={self.condition_id}, severity_id={self.severity_id}, ingredient_id={self.ingredient_id})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "condition_id": self.condition_id,
            "severity_id": self.severity_id,
            "ingredient_id": self.ingredient_id,
            "suggested_use": self.suggested_use,
            "priority": self.priority
        }


class Product(Base):
    """
    Model untuk produk komersial yang mengandung ingredient.
    """
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="Product name")
    brand = Column(String(255), nullable=False, index=True, comment="Brand name")
    ingredient_id = Column(Integer, ForeignKey('ingredients.id', ondelete='CASCADE'), nullable=False, index=True)
    country = Column(String(100), nullable=True, index=True, comment="Country of origin")
    url = Column(Text, nullable=True, comment="Product page URL")
    image_url = Column(Text, nullable=True, comment="Product image URL")
    price_range = Column(String(50), nullable=True, comment="Budget, Mid-range, Premium")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    ingredient = relationship("Ingredient", back_populates="products")
    
    def __repr__(self):
        return f"<Product(name={self.name}, brand={self.brand})>"
    
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "ingredient_id": self.ingredient_id,
            "country": self.country,
            "url": self.url,
            "image_url": self.image_url,
            "price_range": self.price_range
        }
