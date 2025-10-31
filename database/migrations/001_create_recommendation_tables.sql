-- Migration: Create Recommendation System Tables
-- Created: 2025-10-31
-- Purpose: Store ingredients, conditions, severity levels, and product recommendations

-- 1. Severity Levels Table
CREATE TABLE IF NOT EXISTS severity_levels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    min_score INTEGER NOT NULL,
    max_score INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT check_score_range CHECK (min_score >= 0 AND max_score <= 100 AND min_score < max_score)
);

-- Create index on score range for fast lookup
CREATE INDEX idx_severity_score_range ON severity_levels(min_score, max_score);

COMMENT ON TABLE severity_levels IS 'Defines severity levels (Poor, Fair, Good) with score ranges';
COMMENT ON COLUMN severity_levels.name IS 'Level name: Poor, Fair, Good';
COMMENT ON COLUMN severity_levels.min_score IS 'Minimum score for this level (inclusive)';
COMMENT ON COLUMN severity_levels.max_score IS 'Maximum score for this level (inclusive)';

-- 2. Conditions Table
CREATE TABLE IF NOT EXISTS conditions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conditions_name ON conditions(name);

COMMENT ON TABLE conditions IS 'Skin conditions detected by AI (acne, wrinkle, pore, etc)';
COMMENT ON COLUMN conditions.name IS 'Condition name matching Perfect Corp API categories';

-- 3. Ingredients Table
CREATE TABLE IF NOT EXISTS ingredients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    generic_name VARCHAR(255),
    benefit TEXT NOT NULL,
    warnings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ingredients_name ON ingredients(name);
CREATE INDEX idx_ingredients_generic_name ON ingredients(generic_name);

COMMENT ON TABLE ingredients IS 'Active ingredients for treating skin conditions';
COMMENT ON COLUMN ingredients.name IS 'Brand/commercial name of ingredient';
COMMENT ON COLUMN ingredients.generic_name IS 'Generic/scientific name (e.g., Salicylic Acid)';
COMMENT ON COLUMN ingredients.benefit IS 'Description of benefits';
COMMENT ON COLUMN ingredients.warnings IS 'Usage warnings or side effects';

-- 4. Condition Ingredients Mapping Table
CREATE TABLE IF NOT EXISTS condition_ingredients (
    id SERIAL PRIMARY KEY,
    condition_id INTEGER NOT NULL REFERENCES conditions(id) ON DELETE CASCADE,
    severity_id INTEGER NOT NULL REFERENCES severity_levels(id) ON DELETE CASCADE,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    suggested_use TEXT,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_condition_severity_ingredient UNIQUE (condition_id, severity_id, ingredient_id)
);

CREATE INDEX idx_condition_ingredients_lookup ON condition_ingredients(condition_id, severity_id);
CREATE INDEX idx_condition_ingredients_priority ON condition_ingredients(priority);

COMMENT ON TABLE condition_ingredients IS 'Maps conditions and severity to recommended ingredients';
COMMENT ON COLUMN condition_ingredients.priority IS 'Higher priority = more recommended (1=highest)';
COMMENT ON COLUMN condition_ingredients.suggested_use IS 'How to use this ingredient for this condition';

-- 5. Products Table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(255) NOT NULL,
    ingredient_id INTEGER NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
    country VARCHAR(100),
    url TEXT,
    image_url TEXT,
    price_range VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_products_ingredient ON products(ingredient_id);
CREATE INDEX idx_products_brand ON products(brand);
CREATE INDEX idx_products_country ON products(country);

COMMENT ON TABLE products IS 'Commercial products containing recommended ingredients';
COMMENT ON COLUMN products.url IS 'Link to product page (e.g., e-commerce)';
COMMENT ON COLUMN products.price_range IS 'Price category: Budget, Mid-range, Premium';

-- Insert default severity levels
INSERT INTO severity_levels (name, description, min_score, max_score) VALUES
    ('Poor', 'Kondisi kulit kurang baik, memerlukan perawatan intensif', 0, 49),
    ('Fair', 'Kondisi kulit sedang, perlu perawatan rutin', 50, 79),
    ('Good', 'Kondisi kulit baik, perawatan preventif', 80, 100)
ON CONFLICT (name) DO NOTHING;

-- Insert default conditions (matching Perfect Corp categories)
INSERT INTO conditions (name, description) VALUES
    ('acne', 'Jerawat dan komedo pada kulit'),
    ('wrinkle', 'Garis halus dan kerutan'),
    ('pore', 'Pori-pori membesar'),
    ('texture', 'Tekstur kulit tidak rata'),
    ('dark_spot', 'Noda hitam dan hiperpigmentasi'),
    ('dark_circle', 'Lingkaran hitam di bawah mata'),
    ('eye_bag', 'Kantung mata'),
    ('redness', 'Kemerahan pada kulit'),
    ('oiliness', 'Kulit berminyak'),
    ('firmness', 'Kekencangan kulit')
ON CONFLICT (name) DO NOTHING;

-- Success message
DO $$
BEGIN
    RAISE NOTICE 'Migration completed successfully!';
    RAISE NOTICE 'Created tables: severity_levels, conditions, ingredients, condition_ingredients, products';
    RAISE NOTICE 'Inserted default severity levels and conditions';
END $$;
