-- Migration 003: Add level column to questions table
-- Date: 2026-04-23
-- Description: Add level field for question difficulty level (1-6)

BEGIN;

-- Add level column (1-6 levels)
ALTER TABLE questions ADD COLUMN level INTEGER;

-- Update alembic version
UPDATE alembic_version SET version_num='003' WHERE alembic_version.version_num = '002';

COMMIT;

-- Rollback (downgrade):
-- BEGIN;
-- ALTER TABLE questions DROP COLUMN level;
-- UPDATE alembic_version SET version_num='002' WHERE alembic_version.version_num = '003';
-- COMMIT;