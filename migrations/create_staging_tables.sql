-- Create staging tables for ProvenPick staging system
-- Run with: psql -U provenpick -d provenpick -f migrations/create_staging_tables.sql

-- 1. Staging Product Table
CREATE TABLE IF NOT EXISTS staging.staging_product (
    staging_product_id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    brand VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price FLOAT NOT NULL,
    description TEXT NOT NULL,
    image_url TEXT NOT NULL,
    specs JSONB DEFAULT '{}',
    affiliate_links JSONB DEFAULT '{}',
    staging_article_id INTEGER,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2. Staging Article Table
CREATE TABLE IF NOT EXISTS staging.staging_article (
    staging_article_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    author_name VARCHAR(100),
    top_pick_staging_id INTEGER NOT NULL,
    runner_up_staging_id INTEGER,
    budget_pick_staging_id INTEGER,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    reviewer_comments TEXT,
    submitted_at TIMESTAMP NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    reviewer_token VARCHAR(100),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP
);

-- 3. Staging Article Image Table
CREATE TABLE IF NOT EXISTS staging.staging_article_image (
    staging_article_image_id SERIAL PRIMARY KEY,
    staging_article_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    alt_text VARCHAR(255),
    image_type VARCHAR(50) NOT NULL,
    sequence_order INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 4. Staging Article Text Table
CREATE TABLE IF NOT EXISTS staging.staging_article_text (
    staging_article_text_id SERIAL PRIMARY KEY,
    staging_article_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    section_type VARCHAR(50) NOT NULL,
    sequence_order INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 5. Staging Product Image Table
CREATE TABLE IF NOT EXISTS staging.staging_product_image (
    staging_product_image_id SERIAL PRIMARY KEY,
    staging_product_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    alt_text VARCHAR(255),
    sequence_order INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 6. Staging Product Text Table
CREATE TABLE IF NOT EXISTS staging.staging_product_text (
    staging_product_text_id SERIAL PRIMARY KEY,
    staging_product_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    heading VARCHAR(255),
    sequence_order INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 7. Rejection Queue Table
CREATE TABLE IF NOT EXISTS staging.rejection_queue (
    rejection_id SERIAL PRIMARY KEY,
    staging_article_id INTEGER NOT NULL,
    article_data JSONB NOT NULL,
    reviewer_comments TEXT NOT NULL,
    rejected_at TIMESTAMP NOT NULL DEFAULT NOW(),
    processed_by_pipeline BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMP
);

-- 8. Archive Table
CREATE TABLE IF NOT EXISTS staging.archive (
    archive_id SERIAL PRIMARY KEY,
    staging_article_id INTEGER NOT NULL,
    action VARCHAR(20) NOT NULL,
    article_data JSONB NOT NULL,
    reviewer_comments TEXT,
    archived_at TIMESTAMP NOT NULL DEFAULT NOW(),
    retention_until TIMESTAMP NOT NULL
);

-- Create indices for better performance
CREATE INDEX IF NOT EXISTS idx_staging_article_status ON staging.staging_article(status);
CREATE INDEX IF NOT EXISTS idx_staging_article_submitted ON staging.staging_article(submitted_at);
CREATE INDEX IF NOT EXISTS idx_rejection_queue_processed ON staging.rejection_queue(processed_by_pipeline);
CREATE INDEX IF NOT EXISTS idx_archive_retention ON staging.archive(retention_until);

-- Success message
SELECT 'Staging tables created successfully!' AS status;
