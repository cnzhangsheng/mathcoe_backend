-- Drop redundant JSON columns from exam_paper_tests
-- These fields are now stored in exam_paper_test_answers table

ALTER TABLE exam_paper_tests DROP COLUMN IF EXISTS answers;
ALTER TABLE exam_paper_tests DROP COLUMN IF EXISTS correct_answers;
ALTER TABLE exam_paper_tests DROP COLUMN IF EXISTS wrong_answers;