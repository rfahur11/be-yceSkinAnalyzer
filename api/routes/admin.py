"""
API routes untuk admin panel - CRUD operations untuk semua tabel
"""
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from database.connection import get_db
from database.models import (
    SeverityLevel,
    Condition,
    Ingredient,
    ConditionIngredient,
    Product,
    SkinAnalysisHistory
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v2/admin",
    tags=["Admin"]
)


# ==================== SEVERITY LEVELS ====================

@router.get("/severity-levels")
async def get_severity_levels(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Get all severity levels"""
    try:
        items = db.query(SeverityLevel).offset(skip).limit(limit).all()
        total = db.query(SeverityLevel).count()
        
        return {
            "status": "success",
            "data": [item.to_dict() for item in items],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching severity levels: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/severity-levels/{id}")
async def get_severity_level(id: int, db: Session = Depends(get_db)):
    """Get severity level by ID"""
    try:
        item = db.query(SeverityLevel).filter(SeverityLevel.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Severity level not found")
        
        return {
            "status": "success",
            "data": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching severity level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/severity-levels")
async def create_severity_level(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Create new severity level"""
    try:
        item = SeverityLevel(
            name=payload.get("name"),
            min_score=payload.get("min_score"),
            max_score=payload.get("max_score"),
            description=payload.get("description")
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "message": "Severity level created successfully",
            "data": item.to_dict()
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating severity level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/severity-levels/{id}")
async def update_severity_level(
    id: int,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Update severity level"""
    try:
        item = db.query(SeverityLevel).filter(SeverityLevel.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Severity level not found")
        
        if "name" in payload:
            item.name = payload["name"]
        if "min_score" in payload:
            item.min_score = payload["min_score"]
        if "max_score" in payload:
            item.max_score = payload["max_score"]
        if "description" in payload:
            item.description = payload["description"]
        
        item.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "message": "Severity level updated successfully",
            "data": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating severity level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/severity-levels/{id}")
async def delete_severity_level(id: int, db: Session = Depends(get_db)):
    """Delete severity level"""
    try:
        item = db.query(SeverityLevel).filter(SeverityLevel.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Severity level not found")
        
        db.delete(item)
        db.commit()
        
        return {
            "status": "success",
            "message": "Severity level deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting severity level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONDITIONS ====================

@router.get("/conditions")
async def get_conditions(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """Get all conditions"""
    try:
        items = db.query(Condition).offset(skip).limit(limit).all()
        total = db.query(Condition).count()
        
        return {
            "status": "success",
            "data": [item.to_dict() for item in items],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching conditions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conditions/{id}")
async def get_condition(id: int, db: Session = Depends(get_db)):
    """Get condition by ID"""
    try:
        item = db.query(Condition).filter(Condition.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Condition not found")
        
        return {
            "status": "success",
            "data": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/conditions")
async def create_condition(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Create new condition"""
    try:
        item = Condition(
            name=payload.get("name"),
            display_name=payload.get("display_name"),
            description=payload.get("description")
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "message": "Condition created successfully",
            "data": item.to_dict()
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/conditions/{id}")
async def update_condition(
    id: int,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Update condition"""
    try:
        item = db.query(Condition).filter(Condition.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Condition not found")
        
        if "name" in payload:
            item.name = payload["name"]
        if "display_name" in payload:
            item.display_name = payload["display_name"]
        if "description" in payload:
            item.description = payload["description"]
        
        item.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "message": "Condition updated successfully",
            "data": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/conditions/{id}")
async def delete_condition(id: int, db: Session = Depends(get_db)):
    """Delete condition"""
    try:
        item = db.query(Condition).filter(Condition.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Condition not found")
        # Remove related condition-ingredient mappings first to avoid FK issues
        db.query(ConditionIngredient).filter(ConditionIngredient.condition_id == id).delete(synchronize_session=False)
        db.delete(item)
        db.commit()
        
        return {
            "status": "success",
            "message": "Condition deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting condition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== INGREDIENTS ====================

@router.get("/ingredients")
async def get_ingredients(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None)
):
    """Get all ingredients with optional search"""
    try:
        query = db.query(Ingredient)
        
        if search:
            query = query.filter(
                (Ingredient.name.ilike(f"%{search}%")) |
                (Ingredient.generic_name.ilike(f"%{search}%"))
            )
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return {
            "status": "success",
            "data": [item.to_dict() for item in items],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching ingredients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ingredients/{id}")
async def get_ingredient(id: int, db: Session = Depends(get_db)):
    """Get ingredient by ID"""
    try:
        item = db.query(Ingredient).filter(Ingredient.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        return {
            "status": "success",
            "data": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching ingredient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingredients")
async def create_ingredient(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Create new ingredient"""
    try:
        item = Ingredient(
            name=payload.get("name"),
            generic_name=payload.get("generic_name"),
            benefit=payload.get("benefit"),
            warnings=payload.get("warnings")
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "message": "Ingredient created successfully",
            "data": item.to_dict()
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating ingredient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/ingredients/{id}")
async def update_ingredient(
    id: int,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Update ingredient"""
    try:
        item = db.query(Ingredient).filter(Ingredient.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        
        if "name" in payload:
            item.name = payload["name"]
        if "generic_name" in payload:
            item.generic_name = payload["generic_name"]
        if "benefit" in payload:
            item.benefit = payload["benefit"]
        if "warnings" in payload:
            item.warnings = payload["warnings"]
        
        item.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "message": "Ingredient updated successfully",
            "data": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating ingredient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/ingredients/{id}")
async def delete_ingredient(id: int, db: Session = Depends(get_db)):
    """Delete ingredient"""
    try:
        item = db.query(Ingredient).filter(Ingredient.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Ingredient not found")
        # Delete related products and condition-ingredient mappings first to avoid FK constraint errors
        db.query(Product).filter(Product.ingredient_id == id).delete(synchronize_session=False)
        db.query(ConditionIngredient).filter(ConditionIngredient.ingredient_id == id).delete(synchronize_session=False)
        db.delete(item)
        db.commit()
        
        return {
            "status": "success",
            "message": "Ingredient deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting ingredient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PRODUCTS ====================

@router.get("/products")
async def get_products(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    search: Optional[str] = Query(None),
    ingredient_id: Optional[int] = Query(None)
):
    """Get all products with optional search and filter"""
    try:
        query = db.query(Product)
        
        if search:
            query = query.filter(
                (Product.name.ilike(f"%{search}%")) |
                (Product.brand.ilike(f"%{search}%"))
            )
        
        if ingredient_id:
            query = query.filter(Product.ingredient_id == ingredient_id)
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return {
            "status": "success",
            "data": [item.to_dict() for item in items],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/products/{id}")
async def get_product(id: int, db: Session = Depends(get_db)):
    """Get product by ID"""
    try:
        item = db.query(Product).filter(Product.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "status": "success",
            "data": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/products")
async def create_product(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Create new product"""
    try:
        item = Product(
            ingredient_id=payload.get("ingredient_id"),
            name=payload.get("name"),
            brand=payload.get("brand"),
            country=payload.get("country"),
            price_range=payload.get("price_range"),
            url=payload.get("url"),
            image_url=payload.get("image_url")
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "message": "Product created successfully",
            "data": item.to_dict()
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/products/{id}")
async def update_product(
    id: int,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Update product"""
    try:
        item = db.query(Product).filter(Product.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Product not found")
        
        if "ingredient_id" in payload:
            item.ingredient_id = payload["ingredient_id"]
        if "name" in payload:
            item.name = payload["name"]
        if "brand" in payload:
            item.brand = payload["brand"]
        if "country" in payload:
            item.country = payload["country"]
        if "price_range" in payload:
            item.price_range = payload["price_range"]
        if "url" in payload:
            item.url = payload["url"]
        if "image_url" in payload:
            item.image_url = payload["image_url"]
        
        item.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "message": "Product updated successfully",
            "data": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/products/{id}")
async def delete_product(id: int, db: Session = Depends(get_db)):
    """Delete product"""
    try:
        item = db.query(Product).filter(Product.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Product not found")
        
        db.delete(item)
        db.commit()
        
        return {
            "status": "success",
            "message": "Product deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting product: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== CONDITION INGREDIENTS ====================

@router.get("/condition-ingredients")
async def get_condition_ingredients(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    condition_id: Optional[int] = Query(None),
    severity_id: Optional[int] = Query(None)
):
    """Get all condition-ingredient mappings with optional filters"""
    try:
        query = db.query(ConditionIngredient)
        
        if condition_id:
            query = query.filter(ConditionIngredient.condition_id == condition_id)
        
        if severity_id:
            query = query.filter(ConditionIngredient.severity_id == severity_id)
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        return {
            "status": "success",
            "data": [item.to_dict() for item in items],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching condition ingredients: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/condition-ingredients/{id}")
async def get_condition_ingredient(id: int, db: Session = Depends(get_db)):
    """Get condition ingredient by ID"""
    try:
        item = db.query(ConditionIngredient).filter(ConditionIngredient.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Condition ingredient not found")
        
        return {
            "status": "success",
            "data": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching condition ingredient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/condition-ingredients")
async def create_condition_ingredient(
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Create new condition-ingredient mapping"""
    try:
        item = ConditionIngredient(
            condition_id=payload.get("condition_id"),
            severity_id=payload.get("severity_id"),
            ingredient_id=payload.get("ingredient_id"),
            suggested_use=payload.get("suggested_use"),
            priority=payload.get("priority", 1)
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "message": "Condition ingredient created successfully",
            "data": item.to_dict()
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating condition ingredient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/condition-ingredients/{id}")
async def update_condition_ingredient(
    id: int,
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db)
):
    """Update condition-ingredient mapping"""
    try:
        item = db.query(ConditionIngredient).filter(ConditionIngredient.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Condition ingredient not found")
        
        if "condition_id" in payload:
            item.condition_id = payload["condition_id"]
        if "severity_id" in payload:
            item.severity_id = payload["severity_id"]
        if "ingredient_id" in payload:
            item.ingredient_id = payload["ingredient_id"]
        if "suggested_use" in payload:
            item.suggested_use = payload["suggested_use"]
        if "priority" in payload:
            item.priority = payload["priority"]
        
        item.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(item)
        
        return {
            "status": "success",
            "message": "Condition ingredient updated successfully",
            "data": item.to_dict()
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating condition ingredient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/condition-ingredients/{id}")
async def delete_condition_ingredient(id: int, db: Session = Depends(get_db)):
    """Delete condition-ingredient mapping"""
    try:
        item = db.query(ConditionIngredient).filter(ConditionIngredient.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Condition ingredient not found")
        
        db.delete(item)
        db.commit()
        
        return {
            "status": "success",
            "message": "Condition ingredient deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting condition ingredient: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ANALYSIS HISTORY ====================

@router.get("/analysis-history")
async def get_analysis_history(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: Optional[str] = Query(None)
):
    """Get all analysis history with optional user filter"""
    try:
        query = db.query(SkinAnalysisHistory)
        
        if user_id:
            query = query.filter(SkinAnalysisHistory.user_id == user_id)
        
        query = query.order_by(SkinAnalysisHistory.created_at.desc())
        
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        
        # Build response, extract score_info from result_json when available
        def _score_summary_from_item(item):
            try:
                if item.result_json and isinstance(item.result_json, dict):
                    # Prefer score_info if present
                    score_info = item.result_json.get("score_info") or {}
                    return score_info
            except Exception:
                pass
            return None

        return {
            "status": "success",
            "data": [
                {
                    "id": str(item.id),
                    "task_id": item.task_id,
                    "user_id": item.user_id,
                    "image_path": item.image_path,
                    "overlay_path": item.overlay_path,
                    "created_at": item.created_at.isoformat() if item.created_at else None,
                    "score_summary": _score_summary_from_item(item)
                }
                for item in items
            ],
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error fetching analysis history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/analysis-history/{id}")
async def delete_analysis_history(id: str, db: Session = Depends(get_db)):
    """Delete analysis history record"""
    try:
        item = db.query(SkinAnalysisHistory).filter(SkinAnalysisHistory.id == id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Analysis history not found")
        
        db.delete(item)
        db.commit()
        
        return {
            "status": "success",
            "message": "Analysis history deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting analysis history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATS & DASHBOARD ====================

@router.get("/stats")
async def get_admin_stats(db: Session = Depends(get_db)):
    """Get statistics for admin dashboard"""
    try:
        stats = {
            "severity_levels": db.query(SeverityLevel).count(),
            "conditions": db.query(Condition).count(),
            "ingredients": db.query(Ingredient).count(),
            "products": db.query(Product).count(),
            "condition_ingredients": db.query(ConditionIngredient).count(),
            "analysis_history": db.query(SkinAnalysisHistory).count()
        }
        
        return {
            "status": "success",
            "data": stats
        }
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
