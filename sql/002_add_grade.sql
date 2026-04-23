-- Migration 002: Add grade column to users table
-- Date: 2026-04-23
-- Description: Add grade field for user grade level classification

BEGIN;

-- Add grade column with default value 'G1'
ALTER TABLE users ADD COLUMN grade VARCHAR(2) DEFAULT 'G1' NOT NULL;

-- Update alembic version
UPDATE alembic_version SET version_num='002' WHERE alembic_version.version_num = '001';

COMMIT;

-- Rollback (downgrade):
-- BEGIN;
-- ALTER TABLE users DROP COLUMN grade;
-- UPDATE alembic_version SET version_num='001' WHERE alembic_version.version_num = '002';
-- COMMIT;