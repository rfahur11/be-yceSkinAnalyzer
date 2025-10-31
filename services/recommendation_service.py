"""
Recommendation Service
======================
Service untuk memberikan rekomendasi bahan (ingredients) dan produk
berdasarkan kondisi kulit dan tingkat severity (Poor, Fair, Good).

Flow:
1. Extract ui_score dari Perfect Corp API response
2. Map score ke severity level (0-49=Poor, 50-79=Fair, 80-100=Good)
3. Query condition_ingredients untuk mendapatkan ingredient yang sesuai
4. Fetch products yang mengandung ingredient tersebut
5. Return list recommendations sorted by priority

Author: YCE Development Team
Created: 2025-10-31
"""

import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session, joinedload
from database.models import (
    SeverityLevel,
    Condition,
    Ingredient,
    ConditionIngredient,
    Product
)

logger = logging.getLogger(__name__)


def map_score_to_severity(db: Session, score: int) -> Optional[SeverityLevel]:
    """
    Map numeric score (0-100) ke severity level.
    
    Args:
        db: Database session
        score: Score dari Perfect Corp (0-100)
        
    Returns:
        SeverityLevel object atau None jika tidak ditemukan
        
    Example:
        score=45 → Poor (0-49)
        score=75 → Fair (50-79)
        score=95 → Good (80-100)
    """
    try:
        severity = SeverityLevel.get_severity_by_score(db, score)
        if severity:
            logger.info(f"📊 Score {score} → Severity: {severity.name}")
        else:
            logger.warning(f"⚠️ No severity level found for score: {score}")
        return severity
    except Exception as e:
        logger.error(f"❌ Error mapping score to severity: {str(e)}")
        return None


def get_recommendations_for_condition(
    db: Session,
    condition_name: str,
    score: int,
    limit: int = 5
) -> Dict[str, any]:
    """
    Get ingredient dan product recommendations untuk satu kondisi kulit.
    
    Args:
        db: Database session
        condition_name: Nama kondisi (e.g., 'acne', 'wrinkle')
        score: UI score dari Perfect Corp (0-100)
        limit: Maximum jumlah recommendations (default: 5)
        
    Returns:
        Dict dengan format:
        {
            "condition": "acne",
            "score": 45,
            "severity": "Poor",
            "recommendations": [
                {
                    "ingredient": {
                        "id": 1,
                        "name": "Salicylic Acid",
                        "generic_name": "BHA",
                        "benefit": "...",
                        "warnings": "..."
                    },
                    "suggested_use": "Apply 2x daily",
                    "priority": 1,
                    "products": [
                        {
                            "id": 1,
                            "name": "Acne Solution Serum",
                            "brand": "Brand X",
                            "url": "...",
                            "image_url": "...",
                            "price_range": "Mid-range"
                        }
                    ]
                }
            ]
        }
    """
    try:
        # 1. Get condition
        condition = db.query(Condition).filter(
            Condition.name == condition_name.lower()
        ).first()
        
        if not condition:
            logger.warning(f"⚠️ Condition not found: {condition_name}")
            return {
                "condition": condition_name,
                "score": score,
                "severity": None,
                "recommendations": []
            }
        
        # 2. Map score to severity
        severity = map_score_to_severity(db, score)
        if not severity:
            logger.warning(f"⚠️ No severity level for score: {score}")
            return {
                "condition": condition_name,
                "score": score,
                "severity": None,
                "recommendations": []
            }
        
        # 3. Query condition_ingredients with eager loading
        mappings = db.query(ConditionIngredient).filter(
            ConditionIngredient.condition_id == condition.id,
            ConditionIngredient.severity_id == severity.id
        ).options(
            joinedload(ConditionIngredient.ingredient).joinedload(Ingredient.products)
        ).order_by(
            ConditionIngredient.priority
        ).limit(limit).all()
        
        # 4. Build recommendations
        recommendations = []
        for mapping in mappings:
            ingredient = mapping.ingredient
            products = [prod.to_dict() for prod in ingredient.products]
            
            recommendations.append({
                "ingredient": ingredient.to_dict(),
                "suggested_use": mapping.suggested_use,
                "priority": mapping.priority,
                "products": products
            })
        
        logger.info(
            f"✅ Found {len(recommendations)} recommendations for "
            f"{condition_name} (score={score}, severity={severity.name})"
        )
        
        return {
            "condition": condition_name,
            "score": score,
            "severity": severity.name,
            "severity_description": severity.description,
            "recommendations": recommendations
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting recommendations: {str(e)}")
        return {
            "condition": condition_name,
            "score": score,
            "severity": None,
            "recommendations": [],
            "error": str(e)
        }


def get_all_recommendations(db: Session, score_info: Dict[str, any]) -> List[Dict]:
    """
    Get recommendations untuk semua kondisi dari Perfect Corp response.

    Tolerant terhadap variasi bentuk data dan key non-kondisi.
    - Mengabaikan key seperti: 'all', 'skin_age', dll
    - Menangani value berupa dict ({ui_score, score}) ATAU angka langsung
    - Alias penamaan kondisi: 'age_spot' → 'dark_spot'

    Args:
        db: Database session
        score_info: Dict dari Perfect Corp dengan format beragam, contoh:
            {
                "acne": {"ui_score": 45},
                "wrinkle": {"ui_score": 75},
                "pore": {"ui_score": 82},
                "all": {"score": 77},              # akan di-skip
                "skin_age": 26                       # akan di-skip
            }

    Returns:
        List of recommendation dicts
    """
    try:
        all_recommendations: List[Dict] = []

        # 1) Ambil daftar kondisi valid dari DB
        valid_conditions = {c.name for c in db.query(Condition).all()}

        # 2) Alias untuk menyamakan penamaan antara UI/API dan DB
        aliases = {
            "age_spot": "dark_spot",  # UI pakai age_spot; DB default pakai dark_spot
        }

        # 3) Iterasi semua entry di score_info
        for raw_name, scores in (score_info or {}).items():
            cond_name = (raw_name or "").lower()
            normalized_name = aliases.get(cond_name, cond_name)

            # Skip key yang bukan kondisi (mis. 'all', 'skin_age', dll.)
            if normalized_name not in valid_conditions:
                logger.info(f"⏭️ Skipping non-condition key: {raw_name}")
                continue

            # 4) Ambil skor (mendukung bentuk dict atau angka langsung)
            score_val: int = 0
            if isinstance(scores, dict):
                score_val = int(scores.get("ui_score") or scores.get("score") or 0)
            elif isinstance(scores, (int, float)):
                score_val = int(scores)
            else:
                logger.info(f"⏭️ Skipping {raw_name}: unsupported score format {type(scores)}")
                continue

            # Clamp 0-100
            score_val = max(0, min(100, score_val))

            # Skip jika score 0
            if score_val == 0:
                logger.info(f"⏭️ Skipping {normalized_name} (score=0)")
                continue

            # 5) Get recommendations untuk kondisi ini
            recommendation = get_recommendations_for_condition(
                db=db,
                condition_name=normalized_name,
                score=score_val
            )

            # Hanya tambahkan jika ada recommendations
            if recommendation.get("recommendations"):
                all_recommendations.append(recommendation)

        logger.info(
            f"✅ Generated recommendations for {len(all_recommendations)} conditions"
        )
        return all_recommendations

    except Exception as e:
        logger.error(f"❌ Error getting all recommendations: {str(e)}")
        return []


def get_ingredient_by_id(db: Session, ingredient_id: int) -> Optional[Dict]:
    """
    Get detailed ingredient information by ID.
    
    Args:
        db: Database session
        ingredient_id: ID of ingredient
        
    Returns:
        Ingredient dict atau None
    """
    try:
        ingredient = db.query(Ingredient).filter(
            Ingredient.id == ingredient_id
        ).first()
        
        if ingredient:
            return ingredient.to_dict()
        return None
    except Exception as e:
        logger.error(f"❌ Error getting ingredient: {str(e)}")
        return None


def get_products_by_ingredient(
    db: Session,
    ingredient_id: int,
    country: Optional[str] = None,
    price_range: Optional[str] = None
) -> List[Dict]:
    """
    Get products containing specific ingredient with optional filters.
    
    Args:
        db: Database session
        ingredient_id: ID of ingredient
        country: Filter by country (optional)
        price_range: Filter by price_range (optional)
        
    Returns:
        List of product dicts
    """
    try:
        query = db.query(Product).filter(
            Product.ingredient_id == ingredient_id
        )
        
        if country:
            query = query.filter(Product.country == country)
        
        if price_range:
            query = query.filter(Product.price_range == price_range)
        
        products = query.all()
        return [prod.to_dict() for prod in products]
        
    except Exception as e:
        logger.error(f"❌ Error getting products: {str(e)}")
        return []


def get_severity_info(db: Session) -> List[Dict]:
    """
    Get all severity levels info.
    
    Returns:
        List of severity level dicts:
        [
            {"id": 1, "name": "Poor", "min_score": 0, "max_score": 49, ...},
            {"id": 2, "name": "Fair", "min_score": 50, "max_score": 79, ...},
            {"id": 3, "name": "Good", "min_score": 80, "max_score": 100, ...}
        ]
    """
    try:
        levels = db.query(SeverityLevel).order_by(SeverityLevel.min_score).all()
        return [level.to_dict() for level in levels]
    except Exception as e:
        logger.error(f"❌ Error getting severity info: {str(e)}")
        return []
