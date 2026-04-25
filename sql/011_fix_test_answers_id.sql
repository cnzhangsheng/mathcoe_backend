-- 修改 exam_paper_test_answers 表的 id 列，从自增改为手动生成
-- 移除 GENERATED ALWAYS AS IDENTITY 约束

-- 1. 先删除 identity 约束
ALTER TABLE exam_paper_test_answers ALTER COLUMN id DROP IDENTITY IF EXISTS;

-- 2. 确保 id 列没有默认值，由应用层生成
ALTER TABLE exam_paper_test_answers ALTER COLUMN id SET DEFAULT NULL;