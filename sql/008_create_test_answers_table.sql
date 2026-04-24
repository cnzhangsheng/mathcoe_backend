-- ============================================================
-- 创建考卷答题记录表 exam_paper_test_answers
-- 每题一条记录，便于统计分析
-- ============================================================

-- 创建表
CREATE TABLE IF NOT EXISTS exam_paper_test_answers (
    id BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    test_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    exam_paper_id BIGINT NOT NULL,
    question_index INT NOT NULL,
    question_id BIGINT NOT NULL,
    user_answer VARCHAR(4) NOT NULL,
    correct_answer VARCHAR(4) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加注释
COMMENT ON TABLE exam_paper_test_answers IS '考卷答题记录表，每题一条记录';
COMMENT ON COLUMN exam_paper_test_answers.test_id IS '关联 exam_paper_tests.id';
COMMENT ON COLUMN exam_paper_test_answers.user_id IS '用户ID';
COMMENT ON COLUMN exam_paper_test_answers.exam_paper_id IS '考卷ID';
COMMENT ON COLUMN exam_paper_test_answers.question_index IS '题目序号（1-N）';
COMMENT ON COLUMN exam_paper_test_answers.question_id IS '关联 questions.id';
COMMENT ON COLUMN exam_paper_test_answers.user_answer IS '用户答案（A/B/C/D）';
COMMENT ON COLUMN exam_paper_test_answers.correct_answer IS '正确答案';
COMMENT ON COLUMN exam_paper_test_answers.is_correct IS '是否正确';

-- 创建索引
-- 查询某次测试的所有答题记录
CREATE INDEX IF NOT EXISTS ix_test_answers_test_id
ON exam_paper_test_answers(test_id);

-- 查询用户的所有答题记录
CREATE INDEX IF NOT EXISTS ix_test_answers_user_id
ON exam_paper_test_answers(user_id);

-- 查询用户的错题/正确题
CREATE INDEX IF NOT EXISTS ix_test_answers_user_correct
ON exam_paper_test_answers(user_id, is_correct);

-- 查询某题的正确/错误统计
CREATE INDEX IF NOT EXISTS ix_test_answers_question_correct
ON exam_paper_test_answers(question_id, is_correct);

-- 查询用户对某题的答题历史
CREATE INDEX IF NOT EXISTS ix_test_answers_user_question
ON exam_paper_test_answers(user_id, question_id);

-- 查询考卷的答题统计
CREATE INDEX IF NOT EXISTS ix_test_answers_exam_paper
ON exam_paper_test_answers(exam_paper_id);

-- ============================================================
-- 验证表和索引创建成功
-- ============================================================
SELECT table_name FROM information_schema.tables WHERE table_name = 'exam_paper_test_answers';

SELECT indexname, indexdef FROM pg_indexes WHERE tablename = 'exam_paper_test_answers';