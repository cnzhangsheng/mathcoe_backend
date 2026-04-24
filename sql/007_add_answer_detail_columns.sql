-- ============================================================
-- 为 exam_paper_tests 表添加 correct_answers 和 wrong_answers 列
-- ============================================================

-- 删除不带条件的唯一索引（会阻止用户多次练习同一考卷）
DROP INDEX IF EXISTS uq_user_exam_paper;

-- 确保带WHERE条件的唯一索引存在（只限制进行中的测试）
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_exam_paper_in_progress
ON exam_paper_tests(user_id, exam_paper_id)
WHERE status = 'in_progress';

-- 添加 correct_answers 列（答对的题目详情）
ALTER TABLE exam_paper_tests
ADD COLUMN IF NOT EXISTS correct_answers JSONB;

-- 添加 wrong_answers 列（答错的题目详情）
ALTER TABLE exam_paper_tests
ADD COLUMN IF NOT EXISTS wrong_answers JSONB;

-- 添加注释
COMMENT ON COLUMN exam_paper_tests.correct_answers IS
'答对的题目详情，JSON格式: {"1": {"question_id": 123, "user_answer": "A", "correct_answer": "A"}}';

COMMENT ON COLUMN exam_paper_tests.wrong_answers IS
'答错的题目详情，JSON格式: {"2": {"question_id": 124, "user_answer": "A", "correct_answer": "B"}}';

-- ============================================================
-- 验证列添加成功
-- ============================================================
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'exam_paper_tests'
AND column_name IN ('correct_answers', 'wrong_answers');