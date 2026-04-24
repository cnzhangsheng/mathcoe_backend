-- ============================================================
-- Kangaroo Math Brain - 完整数据库表结构
-- PostgreSQL 建表 SQL 语句（整合所有迁移）
-- 使用分布式短ID（11-12位纯数字），不使用自增
-- 执行前请先创建数据库: CREATE DATABASE kangaroo_math;
-- ============================================================

-- ============================================
-- 0. 管理员表 (admins)
-- ============================================
CREATE TABLE admins (
    id BIGINT PRIMARY KEY,
    username VARCHAR(64) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    role VARCHAR(32) NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_admins_username ON admins(username);
CREATE INDEX ix_admins_id ON admins(id);

COMMENT ON TABLE admins IS '后台管理员表';
COMMENT ON COLUMN admins.password_hash IS 'bcrypt加密密码';
COMMENT ON COLUMN admins.role IS '角色：admin, super_admin';

-- ============================================
-- 1. 用户表 (users)
-- ============================================
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    openid VARCHAR(64) UNIQUE NOT NULL,
    nickname VARCHAR(64),
    avatar_url VARCHAR(256),
    grade VARCHAR(2) NOT NULL DEFAULT 'G1',         -- 年级 G1-G6
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_active_date DATE,
    last_login_at TIMESTAMP,                        -- 最后登录时间
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_users_openid ON users(openid);
CREATE INDEX ix_users_id ON users(id);

COMMENT ON TABLE users IS '微信小程序用户表';
COMMENT ON COLUMN users.openid IS '微信用户唯一标识';
COMMENT ON COLUMN users.grade IS '年级：G1-G6（一年级到六年级）';
COMMENT ON COLUMN users.streak_days IS '连续打卡天数';
COMMENT ON COLUMN users.last_active_date IS '最后活跃日期';
COMMENT ON COLUMN users.last_login_at IS '最后登录时间';

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
    is_high_freq BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_topics_id ON topics(id);

COMMENT ON TABLE topics IS '专题训练分类表';
COMMENT ON COLUMN topics.difficulty IS '难度等级，如 L1-L2, L2-L3';
COMMENT ON COLUMN topics.is_high_freq IS '是否为高频考点';

-- ============================================
-- 3. 题目表 (questions)
-- ============================================
CREATE TABLE questions (
    id BIGINT PRIMARY KEY,
    topic_id BIGINT REFERENCES topics(id),
    title TEXT NOT NULL,
    content JSONB,                                  -- 题目内容 JSON
    question_type VARCHAR(16) NOT NULL DEFAULT 'single',  -- single/multiple
    options JSONB,                                  -- 选项列表 JSON
    answer VARCHAR(32) NOT NULL,                    -- 单选: A, 多选: A,B,C
    explanation JSONB,                              -- 解析内容 JSON
    difficulty VARCHAR(16),
    level INTEGER,                                  -- 级别 1-6
    source_year INTEGER,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_questions_id ON questions(id);
CREATE INDEX ix_questions_topic_id ON questions(topic_id);
CREATE INDEX ix_questions_difficulty ON questions(difficulty);
CREATE INDEX ix_questions_level ON questions(level);
CREATE INDEX ix_questions_source_year ON questions(source_year);

COMMENT ON TABLE questions IS '题目表';
COMMENT ON COLUMN questions.content IS '题目内容（图片、文字等）JSON格式';
COMMENT ON COLUMN questions.question_type IS '题型：single单选, multiple多选';
COMMENT ON COLUMN questions.options IS '选项列表 [{label:A, text:..., format:html}]';
COMMENT ON COLUMN questions.answer IS '正确答案';
COMMENT ON COLUMN questions.explanation IS '解析内容 JSON格式';
COMMENT ON COLUMN questions.level IS '题目级别 1-6';

-- ============================================
-- 4. 考卷表 (exam_papers)
-- ============================================
CREATE TABLE exam_papers (
    id BIGINT PRIMARY KEY,
    title VARCHAR(128) NOT NULL,                    -- 考卷标题
    level VARCHAR(2) NOT NULL,                      -- 等级 A/B/C/D/E/F
    total_questions INTEGER NOT NULL DEFAULT 10,    -- 题目总数
    description TEXT,                               -- 考卷描述
    paper_type VARCHAR(16) NOT NULL DEFAULT 'daily', -- daily/mock/topic
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_exam_papers_id ON exam_papers(id);
CREATE INDEX ix_exam_papers_level ON exam_papers(level);
CREATE INDEX ix_exam_papers_paper_type ON exam_papers(paper_type);

COMMENT ON TABLE exam_papers IS '考卷表';
COMMENT ON COLUMN exam_papers.level IS '考卷等级：A/B/C/D/E/F';
COMMENT ON COLUMN exam_papers.paper_type IS '考卷类型：daily每日一练, mock模拟卷, topic专项';

-- ============================================
-- 5. 考卷题目关联表 (exam_paper_questions)
-- ============================================
CREATE TABLE exam_paper_questions (
    id BIGINT PRIMARY KEY,
    exam_paper_id BIGINT NOT NULL REFERENCES exam_papers(id),
    question_id BIGINT NOT NULL REFERENCES questions(id),
    sort INTEGER NOT NULL DEFAULT 1,                -- 题目顺序
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_exam_paper_question UNIQUE (exam_paper_id, question_id)
);

CREATE INDEX ix_exam_paper_questions_id ON exam_paper_questions(id);
CREATE INDEX ix_exam_paper_questions_exam_paper_id ON exam_paper_questions(exam_paper_id);

COMMENT ON TABLE exam_paper_questions IS '考卷题目关联表';
COMMENT ON COLUMN exam_paper_questions.sort IS '题目在考卷中的顺序';

-- ============================================
-- 6. 用户进度表 (user_progress)
-- ============================================
CREATE TABLE user_progress (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    topic_id BIGINT NOT NULL REFERENCES topics(id),
    progress INTEGER NOT NULL DEFAULT 0,
    success_rate INTEGER NOT NULL DEFAULT 0,
    questions_done INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_topic UNIQUE (user_id, topic_id)
);

CREATE INDEX ix_user_progress_id ON user_progress(id);
CREATE INDEX ix_user_progress_user_id ON user_progress(user_id);

COMMENT ON TABLE user_progress IS '用户专题进度表';
COMMENT ON COLUMN user_progress.progress IS '完成进度百分比';
COMMENT ON COLUMN user_progress.success_rate IS '准确率百分比';
COMMENT ON COLUMN user_progress.questions_done IS '已练习题目数量';

-- ============================================
-- 7. 答题记录表 (practice_records)
-- ============================================
CREATE TABLE practice_records (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    question_id BIGINT NOT NULL REFERENCES questions(id),
    user_answer VARCHAR(8),
    is_correct BOOLEAN,
    time_spent INTEGER,
    is_flagged BOOLEAN NOT NULL DEFAULT FALSE,
    is_bookmarked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_practice_records_id ON practice_records(id);
CREATE INDEX ix_practice_records_user_id ON practice_records(user_id);
CREATE INDEX ix_practice_records_question_id ON practice_records(question_id);

COMMENT ON TABLE practice_records IS '答题记录表';
COMMENT ON COLUMN practice_records.user_answer IS '用户答案';
COMMENT ON COLUMN practice_records.time_spent IS '答题用时（秒）';
COMMENT ON COLUMN practice_records.is_flagged IS '是否标记待复查';
COMMENT ON COLUMN practice_records.is_bookmarked IS '是否收藏';

-- ============================================
-- 8. 收藏表 (favorites)
-- ============================================
CREATE TABLE favorites (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    question_id BIGINT NOT NULL REFERENCES questions(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_question_favorite UNIQUE (user_id, question_id)
);

CREATE INDEX ix_favorites_id ON favorites(id);
CREATE INDEX ix_favorites_user_id ON favorites(user_id);

COMMENT ON TABLE favorites IS '用户收藏题目表';

-- ============================================
-- 9. 错题表 (wrong_questions)
-- ============================================
CREATE TABLE wrong_questions (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    question_id BIGINT NOT NULL REFERENCES questions(id),
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_retry_at TIMESTAMP,
    mastered BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_question_wrong UNIQUE (user_id, question_id)
);

CREATE INDEX ix_wrong_questions_id ON wrong_questions(id);
CREATE INDEX ix_wrong_questions_user_id ON wrong_questions(user_id);

COMMENT ON TABLE wrong_questions IS '用户错题记录表';
COMMENT ON COLUMN wrong_questions.retry_count IS '重试次数';
COMMENT ON COLUMN wrong_questions.mastered IS '是否已掌握';

-- ============================================
-- Alembic 版本控制表
-- ============================================
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL PRIMARY KEY
);

INSERT INTO alembic_version (version_num) VALUES ('004');

-- ============================================
-- 初始数据插入
-- ============================================

-- 插入默认管理员（用户名：admin，密码：admin）
INSERT INTO admins (id, username, password_hash, role) VALUES
(1000, 'admin', '$2b$12$noy82W8dKcuHz1LnufVCU.WEFMzGRyE43RrBGeUGirqpz8Y0iR2Q.', 'admin');

-- 插入专题数据
INSERT INTO topics (id, title, description, difficulty, icon, color, is_high_freq) VALUES
(1001, '算术与计数', '掌握快速心算、单位换算以及基本的排列组合。', 'L1-L2', 'Calculator', 'blue', TRUE),
(1002, '逻辑与推理', '袋鼠数学的核心，包含间接推理、真假判断等。', 'L2-L3', 'Brain', 'purple', TRUE),
(1003, '几何与空间', '图形拆解、旋转观察及周长面积的趣味应用。', 'L1-L3', 'Columns', 'emerald', FALSE),
(1004, '规律与观察', '发现视觉序列中的隐藏模式，锻炼敏锐洞察力。', 'L1-L2', 'Eye', 'amber', FALSE),
(1005, '综合应用题', '将数学引入生活场景，考察阅读理解与模型构建。', 'L3-L4', 'ShoppingBag', 'rose', TRUE);

-- ============================================
-- 删除表语句（如需重建，按顺序执行）
-- ============================================
-- DROP TABLE IF EXISTS alembic_version;
-- DROP TABLE IF EXISTS wrong_questions CASCADE;
-- DROP TABLE IF EXISTS favorites CASCADE;
-- DROP TABLE IF EXISTS practice_records CASCADE;
-- DROP TABLE IF EXISTS user_progress CASCADE;
-- DROP TABLE IF EXISTS exam_paper_questions CASCADE;
-- DROP TABLE IF EXISTS exam_papers CASCADE;
-- DROP TABLE IF EXISTS questions CASCADE;
-- DROP TABLE IF EXISTS topics CASCADE;
-- DROP TABLE IF EXISTS users CASCADE;
-- DROP TABLE IF EXISTS admins CASCADE;