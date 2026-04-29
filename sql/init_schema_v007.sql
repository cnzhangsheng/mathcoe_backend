-- ============================================================
-- Kangaroo Math Brain - 完整数据库初始化脚本
-- MySQL 数据库表结构 + 初始数据
-- 版本: 010 (对齐Alembic)
-- 使用分布式短ID（11-12位纯数字），不使用自增
-- 无外键约束，应用层维护数据一致性
-- 执行前请先创建数据库: CREATE DATABASE kangaroo_math CHARACTER SET utf8mb4;
-- ============================================================

-- ============================================
-- 0. 管理员表 (admins)
-- ============================================
CREATE TABLE admins (
    id BIGINT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'admin',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='后台管理员表';

CREATE INDEX ix_admins_username ON admins(username);
CREATE INDEX ix_admins_id ON admins(id);

-- ============================================
-- 1. 用户表 (users)
-- ============================================
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    openid VARCHAR(64) UNIQUE NOT NULL,
    nickname VARCHAR(64),
    avatar_url VARCHAR(256),
    grade VARCHAR(2) NOT NULL DEFAULT 'G1',
    daily_goal INTEGER NOT NULL DEFAULT 10,
    difficulty_level INTEGER NOT NULL DEFAULT 1,
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_active_date DATE,
    last_login_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='微信小程序用户表';

CREATE INDEX ix_users_openid ON users(openid);
CREATE INDEX ix_users_id ON users(id);
CREATE INDEX ix_users_grade ON users(grade);

-- ============================================
-- 2. 专题表 (topics)
-- ============================================
CREATE TABLE topics (
    id BIGINT PRIMARY KEY,
    title VARCHAR(64) NOT NULL,
    description TEXT,
    difficulty VARCHAR(16),
    icon VARCHAR(32),
    color VARCHAR(16),
    is_high_freq TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='专题训练分类表';

CREATE INDEX ix_topics_id ON topics(id);
CREATE INDEX ix_topics_difficulty ON topics(difficulty);

-- ============================================
-- 3. 题目表 (questions)
-- ============================================
CREATE TABLE questions (
    id BIGINT PRIMARY KEY,
    topic_id BIGINT,
    title TEXT NOT NULL,
    content JSON,
    question_type VARCHAR(16) NOT NULL DEFAULT 'single',
    options JSON,
    answer VARCHAR(32) NOT NULL,
    explanation JSON,
    difficulty_level INTEGER,
    source_year INTEGER,
    tags JSON DEFAULT ('[]'),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='题目表';

CREATE INDEX ix_questions_id ON questions(id);
CREATE INDEX ix_questions_topic_id ON questions(topic_id);
CREATE INDEX ix_questions_difficulty_level ON questions(difficulty_level);
CREATE INDEX ix_questions_source_year ON questions(source_year);

-- ============================================
-- 4. 考卷表 (exam_papers)
-- ============================================
CREATE TABLE exam_papers (
    id BIGINT PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    difficulty_level INTEGER NOT NULL DEFAULT 1,
    total_questions INTEGER NOT NULL DEFAULT 10,
    description TEXT,
    paper_type VARCHAR(16) NOT NULL DEFAULT 'daily',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='考卷表';

CREATE INDEX ix_exam_papers_id ON exam_papers(id);
CREATE INDEX ix_exam_papers_difficulty_level ON exam_papers(difficulty_level);
CREATE INDEX ix_exam_papers_paper_type ON exam_papers(paper_type);

-- ============================================
-- 5. 考卷题目关联表 (exam_paper_questions)
-- ============================================
CREATE TABLE exam_paper_questions (
    id BIGINT PRIMARY KEY,
    exam_paper_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    sort INTEGER NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_exam_paper_question UNIQUE (exam_paper_id, question_id)
) COMMENT='考卷题目关联表';

CREATE INDEX ix_exam_paper_questions_id ON exam_paper_questions(id);
CREATE INDEX ix_exam_paper_questions_exam_paper_id ON exam_paper_questions(exam_paper_id);
CREATE INDEX ix_exam_paper_questions_question_id ON exam_paper_questions(question_id);

-- ============================================
-- 6. 考卷测试记录表 (exam_paper_tests)
-- ============================================
CREATE TABLE exam_paper_tests (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    exam_paper_id BIGINT NOT NULL,
    score INTEGER,
    correct_count INTEGER,
    total_questions INTEGER NOT NULL,
    time_spent INTEGER,
    started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at DATETIME,
    status VARCHAR(16) NOT NULL DEFAULT 'in_progress',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='考卷测试记录表';

CREATE INDEX ix_exam_paper_tests_id ON exam_paper_tests(id);
CREATE INDEX ix_exam_paper_tests_user_id ON exam_paper_tests(user_id);
CREATE INDEX ix_exam_paper_tests_exam_paper_id ON exam_paper_tests(exam_paper_id);
CREATE INDEX ix_exam_paper_tests_status ON exam_paper_tests(status);

-- ============================================
-- 7. 考卷答题记录表 (exam_paper_test_answers)
-- ============================================
CREATE TABLE exam_paper_test_answers (
    id BIGINT PRIMARY KEY,
    test_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    exam_paper_id BIGINT NOT NULL,
    question_index INTEGER NOT NULL,
    question_id BIGINT NOT NULL,
    user_answer VARCHAR(4) NOT NULL,
    correct_answer VARCHAR(4) NOT NULL,
    is_correct TINYINT(1) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='考卷答题记录表';

CREATE INDEX ix_exam_paper_test_answers_id ON exam_paper_test_answers(id);
CREATE INDEX ix_exam_paper_test_answers_test_id ON exam_paper_test_answers(test_id);
CREATE INDEX ix_exam_paper_test_answers_user_id ON exam_paper_test_answers(user_id);
CREATE INDEX ix_exam_paper_test_answers_exam_paper_id ON exam_paper_test_answers(exam_paper_id);
CREATE INDEX ix_exam_paper_test_answers_question_id ON exam_paper_test_answers(question_id);

-- ============================================
-- 8. 答题记录表 (practice_records)
-- ============================================
CREATE TABLE practice_records (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    user_answer VARCHAR(8),
    is_correct TINYINT(1),
    time_spent INTEGER,
    is_flagged TINYINT(1) NOT NULL DEFAULT 0,
    is_bookmarked TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='答题记录表';

CREATE INDEX ix_practice_records_id ON practice_records(id);
CREATE INDEX ix_practice_records_user_id ON practice_records(user_id);
CREATE INDEX ix_practice_records_question_id ON practice_records(question_id);
CREATE INDEX ix_practice_records_is_correct ON practice_records(is_correct);

-- ============================================
-- 9. 点赞表 (likes)
-- ============================================
CREATE TABLE likes (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='点赞记录表';

CREATE INDEX ix_likes_id ON likes(id);
CREATE INDEX ix_likes_user_id ON likes(user_id);
CREATE INDEX ix_likes_question_id ON likes(question_id);

-- ============================================
-- 10. 收藏表 (favorites)
-- ============================================
CREATE TABLE favorites (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_question_favorite UNIQUE (user_id, question_id)
) COMMENT='用户收藏题目表';

CREATE INDEX ix_favorites_id ON favorites(id);
CREATE INDEX ix_favorites_user_id ON favorites(user_id);
CREATE INDEX ix_favorites_question_id ON favorites(question_id);

-- ============================================
-- 11. 错题表 (wrong_questions)
-- ============================================
CREATE TABLE wrong_questions (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    question_id BIGINT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_retry_at DATETIME,
    mastered TINYINT(1) NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_question_wrong UNIQUE (user_id, question_id)
) COMMENT='用户错题记录表';

CREATE INDEX ix_wrong_questions_id ON wrong_questions(id);
CREATE INDEX ix_wrong_questions_user_id ON wrong_questions(user_id);
CREATE INDEX ix_wrong_questions_question_id ON wrong_questions(question_id);
CREATE INDEX ix_wrong_questions_mastered ON wrong_questions(mastered);

-- ============================================
-- 12. Alembic 版本控制表
-- ============================================
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

INSERT INTO alembic_version (version_num) VALUES ('010');


-- ============================================================
-- 初始数据插入
-- ============================================================

-- ============================================
-- 管理员初始数据
-- ============================================
INSERT INTO admins (id, username, password_hash, role) VALUES
(1000, 'admin', '$2b$12$noy82W8dKcuHz1LnufVCU.WEFMzGRyE43RrBGeUGirqpz8Y0iR2Q.', 'admin');

-- ============================================
-- 专题初始数据
-- ============================================
INSERT INTO topics (id, title, description, difficulty, icon, color, is_high_freq) VALUES
(1001, '计算与代数', '掌握快速心算、单位换算以及基本的排列组合。', 'L1-L2', 'Calculator', 'blue', 1),
(1002, '逻辑与观察', '袋鼠数学的核心，包含间接推理、真假判断等。', 'L2-L3', 'Brain', 'purple', 1),
(1003, '几何与空间', '图形拆解、旋转观察及周长面积的趣味应用。', 'L1-L3', 'Columns', 'emerald', 0),
(1004, '数论与规律', '发现视觉序列中的隐藏模式，锻炼敏锐洞察力。', 'L1-L2', 'Eye', 'amber', 0),
(1005, '应用与组合', '将数学引入生活场景，考察阅读理解与模型构建。', 'L3-L4', 'ShoppingBag', 'rose', 1);

-- ============================================
-- 考卷初始数据
-- ============================================
INSERT INTO exam_papers (id, title, difficulty_level, total_questions, description, paper_type) VALUES
(2001, 'Level 1 每日练习', 1, 10, '适合1-2年级，基础算术与图形认知', 'daily'),
(2002, 'Level 2 每日练习', 2, 10, '适合3-4年级，逻辑推理入门', 'daily'),
(2003, 'Level 3 每日练习', 3, 10, '适合5-6年级，综合能力提升', 'daily'),
(2004, 'Level 1 模拟考试', 1, 10, '2024年Level 1真题模拟', 'mock'),
(2005, 'Level 2 模拟考试', 2, 10, '2024年Level 2真题模拟', 'mock'),
(2006, '算术专项训练', 1, 10, '算术与计数专题强化', 'topic'),
(2007, '逻辑专项训练', 2, 10, '逻辑与推理专题强化', 'topic');

-- ============================================
-- 题目示例数据
-- ============================================
INSERT INTO questions (id, topic_id, title, content, question_type, options, answer, explanation, difficulty_level, source_year, tags) VALUES
(3001, 1001, '加法运算', '{"text": "<p>小明有5个苹果，妈妈又给了他3个苹果，小明现在有多少个苹果？</p>", "format": "html"}', 'single',
 '[{"label": "A", "text": "7个"}, {"label": "B", "text": "8个"}, {"label": "C", "text": "9个"}, {"label": "D", "text": "10个"}]',
 'B', '{"text": "<p>5 + 3 = 8，所以小明现在有8个苹果。</p>", "format": "html"}',
 1, 2024, '["加法", "基础"]'),

(3002, 1001, '减法运算', '{"text": "<p>篮子里有10个橘子，小明吃了4个，还剩多少个？</p>", "format": "html"}', 'single',
 '[{"label": "A", "text": "5个"}, {"label": "B", "text": "6个"}, {"label": "C", "text": "7个"}, {"label": "D", "text": "4个"}]',
 'B', '{"text": "<p>10 - 4 = 6，所以还剩6个橘子。</p>", "format": "html"}',
 1, 2024, '["减法", "基础"]'),

(3003, 1001, '乘法入门', '{"text": "<p>每盒有6支铅笔，3盒共有多少支铅笔？</p>", "format": "html"}', 'single',
 '[{"label": "A", "text": "15支"}, {"label": "B", "text": "18支"}, {"label": "C", "text": "20支"}, {"label": "D", "text": "12支"}]',
 'B', '{"text": "<p>6 × 3 = 18，所以共有18支铅笔。</p>", "format": "html"}',
 2, 2023, '["乘法", "基础"]'),

(3004, 1002, '简单推理', '{"text": "<p>如果所有的猫都会爬树，小花是只猫，那么小花会爬树吗？</p>", "format": "html"}', 'single',
 '[{"label": "A", "text": "会"}, {"label": "B", "text": "不会"}, {"label": "C", "text": "不确定"}, {"label": "D", "text": "有时候会"}]',
 'A', '{"text": "<p>因为所有猫都会爬树，小花是猫，所以小花会爬树。</p>", "format": "html"}',
 2, 2024, '["推理", "逻辑"]'),

(3005, 1002, '真假判断', '{"text": "<p>小明说：我比小红大。小红说：我比小刚小。小刚说：我比小明小。请判断谁最大？</p>", "format": "html"}', 'single',
 '[{"label": "A", "text": "小明"}, {"label": "B", "text": "小红"}, {"label": "C", "text": "小刚"}, {"label": "D", "text": "不确定"}]',
 'A', '{"text": "<p>小明 > 小红，小红 < 小刚（即小刚 > 小红），小刚 < 小明。综合得出：小明 > 小刚 > 小红。</p>", "format": "html"}',
 3, 2023, '["推理", "比较"]'),

(3006, 1003, '图形计数', '{"text": "<p>下图中有多少个三角形？</p>", "format": "html"}', 'single',
 '[{"label": "A", "text": "3个"}, {"label": "B", "text": "4个"}, {"label": "C", "text": "5个"}, {"label": "D", "text": "6个"}]',
 'C', '{"text": "<p>仔细观察，图中有5个三角形（包括大三角形和内部的小三角形）。</p>", "format": "html"}',
 1, 2024, '["图形", "计数"]'),

(3007, 1003, '周长计算', '{"text": "<p>一个正方形的边长是4厘米，它的周长是多少厘米？</p>", "format": "html"}', 'single',
 '[{"label": "A", "text": "8厘米"}, {"label": "B", "text": "12厘米"}, {"label": "C", "text": "16厘米"}, {"label": "D", "text": "20厘米"}]',
 'C', '{"text": "<p>正方形周长 = 边长 × 4 = 4 × 4 = 16厘米。</p>", "format": "html"}',
 2, 2023, '["周长", "正方形"]'),

(3008, 1004, '数字规律', '{"text": "<p>找规律填数：2, 4, 6, 8, ___</p>", "format": "html"}', 'single',
 '[{"label": "A", "text": "9"}, {"label": "B", "text": "10"}, {"label": "C", "text": "11"}, {"label": "D", "text": "12"}]',
 'B', '{"text": "<p>规律是每次加2：2→4→6→8→10，所以填10。</p>", "format": "html"}',
 1, 2024, '["规律", "数列"]'),

(3009, 1004, '图形规律', '{"text": "<p>观察图形序列：○□○□○□，下一个图形是什么？</p>", "format": "html"}', 'single',
 '[{"label": "A", "text": "○"}, {"label": "B", "text": "□"}, {"label": "C", "text": "△"}, {"label": "D", "text": "☆"}]',
 'A', '{"text": "<p>规律是圆形和方形交替出现，○□○□○□○，所以下一个是○。</p>", "format": "html"}',
 1, 2024, '["规律", "图形"]'),

(3010, 1005, '购物计算', '{"text": "<p>小明去超市买了3瓶牛奶，每瓶5元，还买了2包饼干，每包8元。小明一共花了多少钱？</p>", "format": "html"}', 'single',
 '[{"label": "A", "text": "15元"}, {"label": "B", "text": "16元"}, {"label": "C", "text": "31元"}, {"label": "D", "text": "23元"}]',
 'C', '{"text": "<p>牛奶：3×5=15元，饼干：2×8=16元，总共：15+16=31元。</p>", "format": "html"}',
 3, 2023, '["应用", "购物"]');


-- ============================================
-- 考卷题目关联示例数据
-- ============================================
INSERT INTO exam_paper_questions (id, exam_paper_id, question_id, sort) VALUES
(4001, 2001, 3001, 1),
(4002, 2001, 3002, 2),
(4003, 2001, 3006, 3),
(4004, 2001, 3008, 4),
(4005, 2001, 3009, 5),

(4006, 2002, 3003, 1),
(4007, 2002, 3004, 2),
(4008, 2002, 3007, 3),
(4009, 2002, 3010, 4),

(4010, 2004, 3001, 1),
(4011, 2004, 3002, 2),
(4012, 2004, 3006, 3),
(4013, 2004, 3008, 4),
(4014, 2004, 3009, 5),

(4015, 2006, 3001, 1),
(4016, 2006, 3002, 2),
(4017, 2006, 3003, 3),

(4018, 2007, 3004, 1),
(4019, 2007, 3005, 2);


-- ============================================================
-- 数据库验证查询
-- ============================================================
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = DATABASE()
ORDER BY table_name, ordinal_position;

SELECT 'admins' as table_name, COUNT(*) as count FROM admins
UNION ALL SELECT 'topics', COUNT(*) FROM topics
UNION ALL SELECT 'exam_papers', COUNT(*) FROM exam_papers
UNION ALL SELECT 'questions', COUNT(*) FROM questions
UNION ALL SELECT 'exam_paper_questions', COUNT(*) FROM exam_paper_questions;


-- ============================================================
-- 删除表语句（如需重建，按此顺序执行）
-- ============================================================
/*
DROP TABLE IF EXISTS alembic_version;
DROP TABLE IF EXISTS wrong_questions;
DROP TABLE IF EXISTS likes;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS practice_records;
DROP TABLE IF EXISTS exam_paper_test_answers;
DROP TABLE IF EXISTS exam_paper_tests;
DROP TABLE IF EXISTS exam_paper_questions;
DROP TABLE IF EXISTS exam_papers;
DROP TABLE IF EXISTS questions;
DROP TABLE IF EXISTS topics;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS admins;
*/
