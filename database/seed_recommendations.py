"""
Seed Data untuk Recommendation System
======================================
Script untuk populate database dengan data:
- Ingredients (bahan aktif skincare)
- Condition Ingredients (mapping kondisi → ingredient)
- Products (produk komersial)

Usage:
    python -m database.seed_recommendations

Author: YCE Development Team
Created: 2025-10-31
"""

import sys
import logging
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database.connection import get_db, engine
from database.models import (
    Base,
    SeverityLevel,
    Condition,
    Ingredient,
    ConditionIngredient,
    Product
)
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def ensure_default_severity_levels(db: Session):
    """Ensure default severity levels exist (Poor, Fair, Good)."""
    logger.info("🔧 Ensuring default severity levels exist...")
    defaults = [
        {
            "name": "Poor",
            "description": "Kondisi kulit kurang baik, memerlukan perawatan intensif",
            "min_score": 0,
            "max_score": 49,
        },
        {
            "name": "Fair",
            "description": "Kondisi kulit sedang, perlu perawatan rutin",
            "min_score": 50,
            "max_score": 79,
        },
        {
            "name": "Good",
            "description": "Kondisi kulit baik, perawatan preventif",
            "min_score": 80,
            "max_score": 100,
        },
    ]

    added = 0
    for item in defaults:
        exists = db.query(SeverityLevel).filter(SeverityLevel.name == item["name"]).first()
        if not exists:
            level = SeverityLevel(**item)
            db.add(level)
            added += 1
    if added:
        db.commit()
        logger.info(f"  ✓ Added {added} severity levels")
    else:
        logger.info("  → Severity levels already present")


def ensure_default_conditions(db: Session):
    """Ensure default skin conditions exist (matching Perfect Corp categories)."""
    logger.info("🔧 Ensuring default skin conditions exist...")
    defaults = [
        {"name": "acne", "description": "Jerawat dan komedo pada kulit"},
        {"name": "wrinkle", "description": "Garis halus dan kerutan"},
        {"name": "pore", "description": "Pori-pori membesar"},
        {"name": "texture", "description": "Tekstur kulit tidak rata"},
        {"name": "dark_spot", "description": "Noda hitam dan hiperpigmentasi"},
        {"name": "dark_circle", "description": "Lingkaran hitam di bawah mata"},
        {"name": "eye_bag", "description": "Kantung mata"},
        {"name": "redness", "description": "Kemerahan pada kulit"},
        {"name": "oiliness", "description": "Kulit berminyak"},
        {"name": "firmness", "description": "Kekencangan kulit"},
    ]

    added = 0
    for item in defaults:
        exists = db.query(Condition).filter(Condition.name == item["name"]).first()
        if not exists:
            cond = Condition(**item)
            db.add(cond)
            added += 1
    if added:
        db.commit()
        logger.info(f"  ✓ Added {added} conditions")
    else:
        logger.info("  → Conditions already present")


def seed_ingredients(db: Session):
    """Populate ingredients table dengan bahan aktif skincare"""
    logger.info("🌱 Seeding ingredients...")
    
    ingredients_data = [
        # ACNE TREATMENTS
        {
            "name": "Salicylic Acid",
            "generic_name": "BHA (Beta Hydroxy Acid)",
            "benefit": "Exfoliates inside pores, reduces acne and blackheads, oil-soluble penetration",
            "warnings": "Can cause dryness, start with low concentration (0.5-2%). Avoid if pregnant."
        },
        {
            "name": "Benzoyl Peroxide",
            "generic_name": "BP",
            "benefit": "Kills acne-causing bacteria, reduces inflammation, prevents new breakouts",
            "warnings": "Can bleach fabrics, may cause irritation. Start with 2.5% concentration."
        },
        {
            "name": "Niacinamide",
            "generic_name": "Vitamin B3",
            "benefit": "Reduces sebum production, minimizes pores, brightens skin, anti-inflammatory",
            "warnings": "Generally safe, rare allergic reactions. Use 2-10% concentration."
        },
        {
            "name": "Tea Tree Oil",
            "generic_name": "Melaleuca Alternifolia Oil",
            "benefit": "Natural antibacterial, reduces acne, soothes inflammation",
            "warnings": "Must be diluted (2-5%), can cause irritation if used undiluted."
        },
        
        # ANTI-AGING (WRINKLES)
        {
            "name": "Retinol",
            "generic_name": "Vitamin A",
            "benefit": "Stimulates collagen, reduces fine lines, improves texture, increases cell turnover",
            "warnings": "Photosensitive, use at night. Start slow, can cause purging. Not for pregnancy."
        },
        {
            "name": "Peptides",
            "generic_name": "Collagen Peptides",
            "benefit": "Stimulates collagen production, improves firmness, reduces wrinkles",
            "warnings": "Generally safe, expensive. Look for Matrixyl, Argireline."
        },
        {
            "name": "Vitamin C",
            "generic_name": "L-Ascorbic Acid",
            "benefit": "Antioxidant, brightens, stimulates collagen, protects from free radicals",
            "warnings": "Oxidizes quickly, store properly. Use 10-20% concentration."
        },
        {
            "name": "Hyaluronic Acid",
            "generic_name": "HA",
            "benefit": "Intense hydration, plumps skin, reduces appearance of fine lines",
            "warnings": "Safe for all skin types, use on damp skin for best results."
        },
        
        # PORE CARE
        {
            "name": "Niacinamide",  # Duplicate but effective for multiple conditions
            "generic_name": "Vitamin B3",
            "benefit": "Minimizes pore appearance, regulates sebum, improves texture",
            "warnings": "Generally safe, rare allergic reactions. Use 2-10% concentration."
        },
        {
            "name": "AHA",
            "generic_name": "Alpha Hydroxy Acids (Glycolic, Lactic)",
            "benefit": "Exfoliates surface, refines pores, improves texture, brightens",
            "warnings": "Photosensitive, use sunscreen. Start with low concentration (5-10%)."
        },
        
        # BRIGHTENING (DARK SPOTS)
        {
            "name": "Vitamin C",  # Already added, effective for brightening
            "generic_name": "L-Ascorbic Acid",
            "benefit": "Fades dark spots, brightens, evens tone, antioxidant protection",
            "warnings": "Oxidizes quickly, store properly. Use 10-20% concentration."
        },
        {
            "name": "Tranexamic Acid",
            "generic_name": "TXA",
            "benefit": "Reduces hyperpigmentation, fades melasma, brightens stubborn spots",
            "warnings": "Safe for most skin types, use 2-5% concentration."
        },
        {
            "name": "Alpha Arbutin",
            "generic_name": "Arbutin",
            "benefit": "Gentle brightening, inhibits melanin, safe for sensitive skin",
            "warnings": "Safe alternative to hydroquinone, use 1-2% concentration."
        },
        
        # HYDRATION & TEXTURE
        {
            "name": "Ceramides",
            "generic_name": "Ceramide 1, 3, 6-II",
            "benefit": "Repairs skin barrier, locks moisture, improves texture",
            "warnings": "Safe for all skin types, especially good for dry/sensitive skin."
        },
        {
            "name": "Centella Asiatica",
            "generic_name": "Cica, Tiger Grass",
            "benefit": "Soothes irritation, repairs barrier, anti-inflammatory",
            "warnings": "Very safe, suitable for sensitive skin."
        },
        
        # REDNESS & SENSITIVITY
        {
            "name": "Azelaic Acid",
            "generic_name": "AzA",
            "benefit": "Reduces redness, treats rosacea, brightens, mild exfoliation",
            "warnings": "May cause tingling, start with 10% concentration."
        },
        {
            "name": "Centella Asiatica",  # Already added, multi-purpose
            "generic_name": "Cica",
            "benefit": "Calms redness, soothes inflammation, repairs barrier",
            "warnings": "Very safe, suitable for sensitive skin."
        }
    ]
    
    # Insert ingredients (skip duplicates)
    added_ingredients = {}
    for ing_data in ingredients_data:
        # Check if already exists
        existing = db.query(Ingredient).filter(
            Ingredient.name == ing_data["name"],
            Ingredient.generic_name == ing_data["generic_name"]
        ).first()
        
        if not existing:
            ingredient = Ingredient(**ing_data)
            db.add(ingredient)
            db.flush()  # Get ID immediately
            added_ingredients[ing_data["name"]] = ingredient.id
            logger.info(f"  ✓ Added: {ing_data['name']} ({ing_data['generic_name']})")
        else:
            added_ingredients[ing_data["name"]] = existing.id
            logger.info(f"  → Exists: {ing_data['name']}")
    
    db.commit()
    logger.info(f"✅ Ingredients seeded: {len(added_ingredients)}")
    return added_ingredients


def seed_condition_ingredients(db: Session, ingredient_ids: dict):
    """Map conditions to ingredients based on severity"""
    logger.info("🌱 Seeding condition → ingredient mappings...")
    
    # Ensure severities exist then get severity IDs
    poor = db.query(SeverityLevel).filter(SeverityLevel.name == "Poor").first()
    fair = db.query(SeverityLevel).filter(SeverityLevel.name == "Fair").first()
    good = db.query(SeverityLevel).filter(SeverityLevel.name == "Good").first()
    if not (poor and fair and good):
        logger.warning("⚠️ Severity levels not found. Creating defaults...")
        ensure_default_severity_levels(db)
        poor = db.query(SeverityLevel).filter(SeverityLevel.name == "Poor").first()
        fair = db.query(SeverityLevel).filter(SeverityLevel.name == "Fair").first()
        good = db.query(SeverityLevel).filter(SeverityLevel.name == "Good").first()
    
    # Ensure conditions exist then get condition IDs
    conditions_list = db.query(Condition).all()
    if not conditions_list:
        logger.warning("⚠️ Conditions not found. Creating defaults...")
        ensure_default_conditions(db)
        conditions_list = db.query(Condition).all()
    conditions = {c.name: c.id for c in conditions_list}
    
    mappings = [
        # ACNE
        # Poor acne (0-49): Strong treatments
        {"condition": "acne", "severity": poor.id, "ingredient": "Benzoyl Peroxide", 
         "suggested_use": "Apply 2.5% BP gel to affected areas at night. Start 2x/week.", "priority": 1},
        {"condition": "acne", "severity": poor.id, "ingredient": "Salicylic Acid", 
         "suggested_use": "Use 2% SA cleanser daily, follow with moisturizer.", "priority": 2},
        {"condition": "acne", "severity": poor.id, "ingredient": "Niacinamide", 
         "suggested_use": "Apply 5-10% niacinamide serum morning and night.", "priority": 3},
        
        # Fair acne (50-79): Moderate treatments
        {"condition": "acne", "severity": fair.id, "ingredient": "Salicylic Acid", 
         "suggested_use": "Use 1-2% SA toner/serum daily.", "priority": 1},
        {"condition": "acne", "severity": fair.id, "ingredient": "Niacinamide", 
         "suggested_use": "Apply 5% niacinamide serum twice daily.", "priority": 2},
        {"condition": "acne", "severity": fair.id, "ingredient": "Tea Tree Oil", 
         "suggested_use": "Spot treat with 5% tea tree oil solution.", "priority": 3},
        
        # Good acne (80-100): Preventive care
        {"condition": "acne", "severity": good.id, "ingredient": "Niacinamide", 
         "suggested_use": "Maintain with 2-5% niacinamide serum.", "priority": 1},
        {"condition": "acne", "severity": good.id, "ingredient": "Tea Tree Oil", 
         "suggested_use": "Optional: Use tea tree cleanser 2-3x/week.", "priority": 2},
        
        # WRINKLE
        # Poor wrinkles (0-49): Intensive anti-aging
        {"condition": "wrinkle", "severity": poor.id, "ingredient": "Retinol", 
         "suggested_use": "Start with 0.25% retinol 2x/week at night, gradually increase.", "priority": 1},
        {"condition": "wrinkle", "severity": poor.id, "ingredient": "Peptides", 
         "suggested_use": "Apply peptide serum morning and night under moisturizer.", "priority": 2},
        {"condition": "wrinkle", "severity": poor.id, "ingredient": "Vitamin C", 
         "suggested_use": "Use 15-20% Vitamin C serum every morning.", "priority": 3},
        
        # Fair wrinkles (50-79): Moderate anti-aging
        {"condition": "wrinkle", "severity": fair.id, "ingredient": "Retinol", 
         "suggested_use": "Use 0.5% retinol 3x/week at night.", "priority": 1},
        {"condition": "wrinkle", "severity": fair.id, "ingredient": "Hyaluronic Acid", 
         "suggested_use": "Apply HA serum on damp skin morning and night.", "priority": 2},
        {"condition": "wrinkle", "severity": fair.id, "ingredient": "Vitamin C", 
         "suggested_use": "Use 10-15% Vitamin C serum every morning.", "priority": 3},
        
        # Good wrinkles (80-100): Preventive
        {"condition": "wrinkle", "severity": good.id, "ingredient": "Vitamin C", 
         "suggested_use": "Maintain with 10% Vitamin C serum daily.", "priority": 1},
        {"condition": "wrinkle", "severity": good.id, "ingredient": "Hyaluronic Acid", 
         "suggested_use": "Use HA serum for hydration and plumpness.", "priority": 2},
        
        # PORE
        # Poor pores (0-49): Intensive pore care
        {"condition": "pore", "severity": poor.id, "ingredient": "Niacinamide", 
         "suggested_use": "Apply 10% niacinamide serum twice daily.", "priority": 1},
        {"condition": "pore", "severity": poor.id, "ingredient": "Salicylic Acid", 
         "suggested_use": "Use 2% SA toner/serum daily to clean pores.", "priority": 2},
        {"condition": "pore", "severity": poor.id, "ingredient": "AHA", 
         "suggested_use": "Apply 10% glycolic acid toner 3x/week at night.", "priority": 3},
        
        # Fair pores (50-79): Moderate care
        {"condition": "pore", "severity": fair.id, "ingredient": "Niacinamide", 
         "suggested_use": "Use 5% niacinamide serum twice daily.", "priority": 1},
        {"condition": "pore", "severity": fair.id, "ingredient": "AHA", 
         "suggested_use": "Use 5% AHA toner 2-3x/week.", "priority": 2},
        
        # Good pores (80-100): Maintenance
        {"condition": "pore", "severity": good.id, "ingredient": "Niacinamide", 
         "suggested_use": "Maintain with 2-5% niacinamide daily.", "priority": 1},
        
        # DARK SPOT
        # Poor dark spots (0-49): Intensive brightening
        {"condition": "dark_spot", "severity": poor.id, "ingredient": "Tranexamic Acid", 
         "suggested_use": "Apply 5% TXA serum twice daily.", "priority": 1},
        {"condition": "dark_spot", "severity": poor.id, "ingredient": "Vitamin C", 
         "suggested_use": "Use 20% Vitamin C serum every morning.", "priority": 2},
        {"condition": "dark_spot", "severity": poor.id, "ingredient": "Alpha Arbutin", 
         "suggested_use": "Apply 2% arbutin serum at night.", "priority": 3},
        
        # Fair dark spots (50-79): Moderate brightening
        {"condition": "dark_spot", "severity": fair.id, "ingredient": "Vitamin C", 
         "suggested_use": "Use 15% Vitamin C serum daily.", "priority": 1},
        {"condition": "dark_spot", "severity": fair.id, "ingredient": "Tranexamic Acid", 
         "suggested_use": "Apply 3% TXA serum daily.", "priority": 2},
        
        # Good dark spots (80-100): Preventive
        {"condition": "dark_spot", "severity": good.id, "ingredient": "Vitamin C", 
         "suggested_use": "Maintain with 10% Vitamin C serum.", "priority": 1},
        
        # REDNESS
        # Poor redness (0-49): Intensive calming
        {"condition": "redness", "severity": poor.id, "ingredient": "Azelaic Acid", 
         "suggested_use": "Apply 10-20% azelaic acid serum at night.", "priority": 1},
        {"condition": "redness", "severity": poor.id, "ingredient": "Centella Asiatica", 
         "suggested_use": "Use centella toner and serum twice daily.", "priority": 2},
        
        # Fair redness (50-79): Moderate calming
        {"condition": "redness", "severity": fair.id, "ingredient": "Centella Asiatica", 
         "suggested_use": "Apply centella serum twice daily.", "priority": 1},
        {"condition": "redness", "severity": fair.id, "ingredient": "Azelaic Acid", 
         "suggested_use": "Use 10% azelaic acid 3-4x/week.", "priority": 2},
        
        # Good redness (80-100): Maintenance
        {"condition": "redness", "severity": good.id, "ingredient": "Centella Asiatica", 
         "suggested_use": "Use centella products as needed.", "priority": 1},
        
        # TEXTURE
        # Poor texture (0-49): Intensive exfoliation
        {"condition": "texture", "severity": poor.id, "ingredient": "AHA", 
         "suggested_use": "Use 10% glycolic acid toner 3-4x/week.", "priority": 1},
        {"condition": "texture", "severity": poor.id, "ingredient": "Retinol", 
         "suggested_use": "Apply 0.5% retinol 3x/week to resurface skin.", "priority": 2},
        
        # Fair texture (50-79): Moderate exfoliation
        {"condition": "texture", "severity": fair.id, "ingredient": "AHA", 
         "suggested_use": "Use 5-10% AHA toner 2-3x/week.", "priority": 1},
        
        # Good texture (80-100): Maintenance
        {"condition": "texture", "severity": good.id, "ingredient": "AHA", 
         "suggested_use": "Use gentle AHA 1-2x/week.", "priority": 1},
    ]
    
    added_count = 0
    for mapping in mappings:
        condition_id = conditions.get(mapping["condition"])
        ingredient_id = ingredient_ids.get(mapping["ingredient"])
        
        if not condition_id or not ingredient_id:
            logger.warning(f"  ⚠️ Skip: {mapping['condition']} → {mapping['ingredient']}")
            continue
        
        # Check if already exists
        existing = db.query(ConditionIngredient).filter(
            ConditionIngredient.condition_id == condition_id,
            ConditionIngredient.severity_id == mapping["severity"],
            ConditionIngredient.ingredient_id == ingredient_id
        ).first()
        
        if not existing:
            ci = ConditionIngredient(
                condition_id=condition_id,
                severity_id=mapping["severity"],
                ingredient_id=ingredient_id,
                suggested_use=mapping["suggested_use"],
                priority=mapping["priority"]
            )
            db.add(ci)
            added_count += 1
    
    db.commit()
    logger.info(f"✅ Condition-Ingredient mappings seeded: {added_count}")


def seed_products(db: Session, ingredient_ids: dict):
    """Populate products table dengan produk komersial"""
    logger.info("🌱 Seeding products...")
    
    products_data = [
        # SALICYLIC ACID PRODUCTS
        {"name": "BHA Blackhead Power Liquid", "brand": "COSRX", "ingredient": "Salicylic Acid", 
         "country": "South Korea", "url": "https://example.com/cosrx-bha", "price_range": "Mid-range"},
        {"name": "Oil-Free Acne Wash", "brand": "Neutrogena", "ingredient": "Salicylic Acid", 
         "country": "USA", "url": "https://example.com/neutrogena-acne", "price_range": "Budget"},
        
        # NIACINAMIDE PRODUCTS
        {"name": "Niacinamide 10% + Zinc 1%", "brand": "The Ordinary", "ingredient": "Niacinamide", 
         "country": "Canada", "url": "https://example.com/to-niacinamide", "price_range": "Budget"},
        {"name": "Galacto Niacin 97 Power Essence", "brand": "PURITO", "ingredient": "Niacinamide", 
         "country": "South Korea", "url": "https://example.com/purito-niacin", "price_range": "Mid-range"},
        
        # RETINOL PRODUCTS
        {"name": "Retinol 0.5% in Squalane", "brand": "The Ordinary", "ingredient": "Retinol", 
         "country": "Canada", "url": "https://example.com/to-retinol", "price_range": "Budget"},
        {"name": "Advanced Night Repair", "brand": "Estée Lauder", "ingredient": "Retinol", 
         "country": "USA", "url": "https://example.com/esteelauder-anr", "price_range": "Premium"},
        
        # VITAMIN C PRODUCTS
        {"name": "Vitamin C Suspension 23%", "brand": "The Ordinary", "ingredient": "Vitamin C", 
         "country": "Canada", "url": "https://example.com/to-vitc", "price_range": "Budget"},
        {"name": "Freshly Juiced Vitamin Drop", "brand": "KLAIRS", "ingredient": "Vitamin C", 
         "country": "South Korea", "url": "https://example.com/klairs-vitc", "price_range": "Mid-range"},
        
        # HYALURONIC ACID PRODUCTS
        {"name": "Hyaluronic Acid 2% + B5", "brand": "The Ordinary", "ingredient": "Hyaluronic Acid", 
         "country": "Canada", "url": "https://example.com/to-ha", "price_range": "Budget"},
        {"name": "Hydrium Synergy Serum", "brand": "COSRX", "ingredient": "Hyaluronic Acid", 
         "country": "South Korea", "url": "https://example.com/cosrx-hydrium", "price_range": "Mid-range"},
        
        # CENTELLA PRODUCTS
        {"name": "Centella Asiatica 100 Ampoule", "brand": "PURITO", "ingredient": "Centella Asiatica", 
         "country": "South Korea", "url": "https://example.com/purito-centella", "price_range": "Mid-range"},
        {"name": "Cica Sleeping Mask", "brand": "Laneige", "ingredient": "Centella Asiatica", 
         "country": "South Korea", "url": "https://example.com/laneige-cica", "price_range": "Premium"},
        
        # AHA PRODUCTS
        {"name": "AHA 7 Whitehead Power Liquid", "brand": "COSRX", "ingredient": "AHA", 
         "country": "South Korea", "url": "https://example.com/cosrx-aha", "price_range": "Mid-range"},
        {"name": "Glycolic Acid 7% Toning Solution", "brand": "The Ordinary", "ingredient": "AHA", 
         "country": "Canada", "url": "https://example.com/to-aha", "price_range": "Budget"},
        
        # AZELAIC ACID PRODUCTS
        {"name": "Azelaic Acid Suspension 10%", "brand": "The Ordinary", "ingredient": "Azelaic Acid", 
         "country": "Canada", "url": "https://example.com/to-azelaic", "price_range": "Budget"},
        {"name": "Azclear Action Cream", "brand": "Ego", "ingredient": "Azelaic Acid", 
         "country": "Australia", "url": "https://example.com/ego-azclear", "price_range": "Mid-range"},
    ]
    
    added_count = 0
    for prod_data in products_data:
        ingredient_id = ingredient_ids.get(prod_data["ingredient"])
        if not ingredient_id:
            logger.warning(f"  ⚠️ Skip product: {prod_data['name']} (ingredient not found)")
            continue
        
        # Check if already exists
        existing = db.query(Product).filter(
            Product.name == prod_data["name"],
            Product.brand == prod_data["brand"]
        ).first()
        
        if not existing:
            product = Product(
                name=prod_data["name"],
                brand=prod_data["brand"],
                ingredient_id=ingredient_id,
                country=prod_data["country"],
                url=prod_data["url"],
                price_range=prod_data["price_range"]
            )
            db.add(product)
            added_count += 1
            logger.info(f"  ✓ Added: {prod_data['brand']} - {prod_data['name']}")
        else:
            logger.info(f"  → Exists: {prod_data['name']}")
    
    db.commit()
    logger.info(f"✅ Products seeded: {added_count}")


def main():
    """Run seeding process"""
    logger.info("=" * 80)
    logger.info("🌱 STARTING RECOMMENDATION SYSTEM SEED DATA")
    logger.info("=" * 80)
    
    # Create tables if not exists
    Base.metadata.create_all(bind=engine)
    
    # Get database session
    db = next(get_db())
    
    try:
        # 0. Ensure default master data (severity levels & conditions)
        ensure_default_severity_levels(db)
        ensure_default_conditions(db)
        
        # 1. Seed ingredients
        ingredient_ids = seed_ingredients(db)
        
        # 2. Seed condition → ingredient mappings
        seed_condition_ingredients(db, ingredient_ids)
        
        # 3. Seed products
        seed_products(db, ingredient_ids)
        
        logger.info("=" * 80)
        logger.info("✅ SEEDING COMPLETED SUCCESSFULLY!")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ SEEDING FAILED: {e}", exc_info=True)
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    main()
