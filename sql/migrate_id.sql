-- 数据迁移脚本：从 SERIAL 自增ID迁移到分布式短ID
-- 适用于已有数据的数据库迁移

-- ============================================
-- 注意事项：
-- 1. 执行前请备份所有数据
-- 2. 外键关联需要重建
-- 3. 迁移后ID会变化，需要同步更新关联表
-- ============================================

-- Step 1: 创建临时表存储旧数据

-- 用户表备份
CREATE TABLE users_backup AS SELECT * FROM users;

-- 专题表备份
CREATE TABLE topics_backup AS SELECT * FROM topics;

-- 题目表备份
CREATE TABLE questions_backup AS SELECT * FROM questions;

-- 用户进度表备份
CREATE TABLE user_progress_backup AS SELECT * FROM user_progress;

-- 答题记录表备份
CREATE TABLE practice_records_backup AS SELECT * FROM practice_records;

-- 收藏表备份
CREATE TABLE favorites_backup AS SELECT * FROM favorites;

-- 错题表备份
CREATE TABLE wrong_questions_backup AS SELECT * FROM wrong_questions;

-- Step 2: 删除原表（按依赖顺序）
DROP TABLE IF EXISTS wrong_questions CASCADE;
DROP TABLE IF EXISTS favorites CASCADE;
DROP TABLE IF EXISTS practice_records CASCADE;
DROP TABLE IF EXISTS user_progress CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS topics CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- Step 3: 创建新表结构（使用 BIGINT）
-- 执行 init_schema.sql 中的 CREATE TABLE 语句
-- 或手动执行以下：

-- 用户表
CREATE TABLE users (
    id BIGINT PRIMARY KEY,
    openid VARCHAR(64) UNIQUE NOT NULL,
    nickname VARCHAR(64),
    avatar_url VARCHAR(256),
    streak_days INTEGER NOT NULL DEFAULT 0,
    last_active_date DATE,
    last_login_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 专题表
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

-- 题目表
CREATE TABLE questions (
    id BIGINT PRIMARY KEY,
    topic_id BIGINT REFERENCES topics(id),
    title TEXT NOT NULL,
    content JSONB,
    answer VARCHAR(8) NOT NULL,
    explanation TEXT,
    difficulty VARCHAR(16),
    source_year INTEGER,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 用户进度表
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

-- 答题记录表
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

-- 收藏表
CREATE TABLE favorites (
    id BIGINT PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    question_id BIGINT NOT NULL REFERENCES questions(id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_user_question_favorite UNIQUE (user_id, question_id)
);

-- 错题表
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

-- Step 4: 迁移数据（生成新ID并映射）
-- 注意：这里使用简单映射，实际应用中需要使用后端生成的短ID

-- 创建ID映射表
CREATE TABLE id_mapping (
    old_id INTEGER,
    new_id BIGINT,
    table_name VARCHAR(32)
);

-- 迁移用户数据（使用新的短ID）
INSERT INTO users (id, openid, nickname, avatar_url, streak_days, last_active_date, last_login_at, created_at, updated_at)
SELECT
    old_id * 1000000 + old_id AS new_id,  -- 简单生成新ID（实际应使用后端生成）
    openid, nickname, avatar_url, streak_days, last_active_date, last_login_at, created_at, updated_at
FROM users_backup;

-- 记录映射
INSERT INTO id_mapping (old_id, new_id, table_name)
SELECT id, id, 'users' FROM users;

-- 迁移专题数据
INSERT INTO topics (id, title, description, difficulty, icon, color, is_high_freq, created_at, updated_at)
SELECT
    old_id * 1000000 + old_id AS new_id,
    title, description, difficulty, icon, color, is_high_freq, created_at, updated_at
FROM topics_backup;

-- 迁移题目数据（更新外键）
INSERT INTO questions (id, topic_id, title, content, answer, explanation, difficulty, source_year, tags, created_at, updated_at)
SELECT
    q.old_id * 1000000 + q.old_id AS new_id,
    t.id AS new_topic_id,
    q.title, q.content, q.answer, q.explanation, q.difficulty, q.source_year, q.tags, q.created_at, q.updated_at
FROM questions_backup q
JOIN topics t ON t.title = (SELECT title FROM topics_backup WHERE id = q.topic_id);

-- 类似迁移其他表...

-- Step 5: 清理备份表（可选，建议保留一段时间）
-- DROP TABLE IF EXISTS users_backup;
-- DROP TABLE IF EXISTS topics_backup;
-- DROP TABLE IF EXISTS questions_backup;
-- DROP TABLE IF EXISTS user_progress_backup;
-- DROP TABLE IF EXISTS practice_records_backup;
-- DROP TABLE IF EXISTS favorites_backup;
-- DROP TABLE IF EXISTS wrong_questions_backup;
-- DROP TABLE IF EXISTS id_mapping;