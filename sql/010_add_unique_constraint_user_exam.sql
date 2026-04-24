-- Add unique constraint for user_id + exam_paper_id in exam_paper_tests
-- This ensures each user can only have one test record per exam paper

-- Drop old unique constraint if exists (the one with WHERE clause for in_progress)
DROP INDEX IF EXISTS uq_user_exam_paper_in_progress;

-- Add new unique constraint (without WHERE clause, covers all records)
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_exam_paper ON exam_paper_tests (user_id, exam_paper_id);