-- Migration 004: Add exam_papers and exam_paper_questions tables
-- Date: 2026-04-23
-- Description: Create exam paper management tables

BEGIN;

-- exam_papers table
CREATE TABLE exam_papers (
    id BIGINT NOT NULL,
    title VARCHAR(128) NOT NULL,
    level VARCHAR(2) NOT NULL,
    total_questions INTEGER DEFAULT 10 NOT NULL,
    description TEXT,
    paper_type VARCHAR(16) DEFAULT 'daily' NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

-- exam_paper_questions table
CREATE TABLE exam_paper_questions (
    id BIGINT NOT NULL,
    exam_paper_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    sort INTEGER DEFAULT 1 NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    FOREIGN KEY (exam_paper_id) REFERENCES exam_papers (id),
    FOREIGN KEY (question_id) REFERENCES questions (id)
);

-- Update alembic version
UPDATE alembic_version SET version_num='004' WHERE alembic_version.version_num = '003';

COMMIT;

-- Rollback (downgrade):
-- BEGIN;
-- DROP TABLE exam_paper_questions;
-- DROP TABLE exam_papers;
-- UPDATE alembic_version SET version_num='003' WHERE alembic_version.version_num = '004';
-- COMMIT;