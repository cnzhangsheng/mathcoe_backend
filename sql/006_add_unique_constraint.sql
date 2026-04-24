-- ============================================================
-- 为 exam_paper_tests 表添加唯一索引
-- 确保 user_id + exam_paper_id 在 status='in_progress' 时唯一
-- ============================================================

-- 创建部分唯一索引（只对进行中的测试生效）
-- 这样允许用户多次练习同一考卷，但同一时刻只能有一个进行中的测试
CREATE UNIQUE INDEX IF NOT EXISTS uq_user_exam_paper_in_progress
ON exam_paper_tests(user_id, exam_paper_id)
WHERE status = 'in_progress';

-- 添加注释
COMMENT ON INDEX uq_user_exam_paper_in_progress IS
'确保同一用户对同一考卷只能有一条进行中的测试记录，允许多次练习';

-- ============================================================
-- 验证索引创建成功
-- ============================================================
SELECT
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'exam_paper_tests'
AND indexname = 'uq_user_exam_paper_in_progress';