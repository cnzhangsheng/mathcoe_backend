-- ============================================================
-- Kangaroo Math Brain - Database Initialization Script
-- Target: MySQL 8.0+
-- ============================================================

CREATE DATABASE IF NOT EXISTS kangaroo_math DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE kangaroo_math;

-- ============================================================
-- 1. 管理员表
-- ============================================================
CREATE TABLE IF NOT EXISTS admins (
    id            BIGINT         NOT NULL AUTO_INCREMENT,
    username      VARCHAR(64)    NOT NULL,
    password_hash VARCHAR(128)   NOT NULL,
    role          VARCHAR(32)    NOT NULL DEFAULT 'admin',
    created_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_admins_username (username),
    INDEX ix_admins_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 2. 用户表（微信小程序用户）
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id               BIGINT         NOT NULL AUTO_INCREMENT,
    openid           VARCHAR(64)    NOT NULL,
    nickname         VARCHAR(64)    DEFAULT NULL,
    avatar_url       VARCHAR(256)   DEFAULT NULL,
    streak_days      INT            NOT NULL DEFAULT 0,
    last_active_date DATE           DEFAULT NULL,
    last_login_at    DATETIME       DEFAULT NULL,
    grade            VARCHAR(2)     NOT NULL DEFAULT 'G1',
    daily_goal       INT            NOT NULL DEFAULT 10,
    difficulty_level INT            NOT NULL DEFAULT 1,
    created_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_users_openid (openid),
    INDEX ix_users_openid (openid)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 3. 专题表
-- ============================================================
CREATE TABLE IF NOT EXISTS topics (
    id           BIGINT         NOT NULL AUTO_INCREMENT,
    title        VARCHAR(64)    NOT NULL,
    description  TEXT           DEFAULT NULL,
    difficulty   VARCHAR(16)    DEFAULT NULL COMMENT 'L1-L2, L2-L3 等',
    icon         VARCHAR(32)    DEFAULT NULL COMMENT '图标标识',
    color        VARCHAR(16)    DEFAULT NULL COMMENT '颜色主题',
    is_high_freq TINYINT(1)     NOT NULL DEFAULT 0 COMMENT '是否高频考点',
    created_at   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 4. 题目表
-- ============================================================
CREATE TABLE IF NOT EXISTS questions (
    id               BIGINT         NOT NULL AUTO_INCREMENT,
    topic_id         BIGINT         DEFAULT NULL,
    title            TEXT           NOT NULL COMMENT '题目标题',
    content          JSON          DEFAULT NULL COMMENT '题目内容（含文本、图片等）',
    question_type    VARCHAR(16)    NOT NULL DEFAULT 'single' COMMENT 'single / multiple',
    options          JSON          DEFAULT NULL COMMENT '选项列表 [{label, content, text, image}]',
    answer           VARCHAR(32)    NOT NULL COMMENT '正确答案',
    explanation      JSON          DEFAULT NULL COMMENT '题目解析',
    difficulty_level INT           DEFAULT NULL COMMENT '难度级别 1-6',
    source_year      INT           DEFAULT NULL COMMENT '来源年份',
    tags             JSON          DEFAULT NULL COMMENT '标签',
    created_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX ix_questions_topic_id (topic_id),
    INDEX ix_questions_difficulty_level (difficulty_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 5. 答题记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS practice_records (
    id            BIGINT       NOT NULL AUTO_INCREMENT,
    user_id       BIGINT       NOT NULL,
    question_id   BIGINT       NOT NULL,
    user_answer   VARCHAR(8)   DEFAULT NULL,
    is_correct    TINYINT(1)   DEFAULT NULL,
    time_spent    INT          DEFAULT NULL COMMENT '用时（秒）',
    is_flagged    TINYINT(1)   NOT NULL DEFAULT 0,
    is_bookmarked TINYINT(1)   NOT NULL DEFAULT 0,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX ix_practice_records_user_id (user_id),
    INDEX ix_practice_records_question_id (question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 6. 收藏表
-- ============================================================
CREATE TABLE IF NOT EXISTS favorites (
    id          BIGINT   NOT NULL AUTO_INCREMENT,
    user_id     BIGINT   NOT NULL,
    question_id BIGINT   NOT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_question_favorite (user_id, question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 7. 错题表
-- ============================================================
CREATE TABLE IF NOT EXISTS wrong_questions (
    id             BIGINT       NOT NULL AUTO_INCREMENT,
    user_id        BIGINT       NOT NULL,
    question_id    BIGINT       NOT NULL,
    retry_count    INT          NOT NULL DEFAULT 0 COMMENT '重试次数',
    last_retry_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    mastered       TINYINT(1)   NOT NULL DEFAULT 0 COMMENT '是否已掌握',
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uk_user_question_wrong (user_id, question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 8. 点赞表
-- ============================================================
CREATE TABLE IF NOT EXISTS likes (
    id          BIGINT   NOT NULL AUTO_INCREMENT,
    user_id     BIGINT   NOT NULL,
    question_id BIGINT   NOT NULL,
    created_at  DATETIME DEFAULT NULL,
    updated_at  DATETIME DEFAULT NULL,
    PRIMARY KEY (id),
    INDEX ix_likes_user_id (user_id),
    INDEX ix_likes_question_id (question_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 9. 考卷表
-- ============================================================
CREATE TABLE IF NOT EXISTS exam_papers (
    id                BIGINT         NOT NULL AUTO_INCREMENT,
    title             VARCHAR(128)   NOT NULL,
    difficulty_level  INT            NOT NULL DEFAULT 1 COMMENT '难度等级 1-6',
    total_questions   INT            NOT NULL DEFAULT 10,
    description       TEXT           DEFAULT NULL,
    paper_type        VARCHAR(16)    NOT NULL DEFAULT 'daily' COMMENT 'daily / mock / topic',
    is_new            TINYINT(1)     NOT NULL DEFAULT 0 COMMENT '是否最新',
    file_path         VARCHAR(256)   DEFAULT NULL COMMENT 'PDF 文件路径',
    created_at        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 10. 考卷题目关联表
-- ============================================================
CREATE TABLE IF NOT EXISTS exam_paper_questions (
    id             BIGINT   NOT NULL AUTO_INCREMENT,
    exam_paper_id  BIGINT   NOT NULL,
    question_id    BIGINT   NOT NULL,
    sort           INT      NOT NULL DEFAULT 1 COMMENT '题目顺序',
    created_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 11. 考卷测试记录表
-- ============================================================
CREATE TABLE IF NOT EXISTS exam_paper_tests (
    id               BIGINT       NOT NULL AUTO_INCREMENT,
    user_id          BIGINT       NOT NULL,
    exam_paper_id    BIGINT       NOT NULL,
    score            INT          DEFAULT NULL COMMENT '得分（满分100）',
    correct_count    INT          DEFAULT NULL COMMENT '正确数量',
    total_questions  INT          NOT NULL COMMENT '总题数',
    time_spent       INT          DEFAULT NULL COMMENT '用时（秒）',
    started_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finished_at      DATETIME     DEFAULT NULL,
    status           VARCHAR(16)  NOT NULL DEFAULT 'in_progress' COMMENT 'in_progress / completed',
    created_at       DATETIME     DEFAULT NULL,
    updated_at       DATETIME     DEFAULT NULL,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- 12. 考卷答题记录表（每题一条）
-- ============================================================
CREATE TABLE IF NOT EXISTS exam_paper_test_answers (
    id              BIGINT       NOT NULL AUTO_INCREMENT,
    test_id         BIGINT       NOT NULL,
    user_id         BIGINT       NOT NULL,
    exam_paper_id   BIGINT       NOT NULL,
    question_index  INT          NOT NULL COMMENT '题目序号',
    question_id     BIGINT       NOT NULL,
    user_answer     VARCHAR(4)   NOT NULL,
    correct_answer  VARCHAR(4)   NOT NULL,
    is_correct      TINYINT(1)   NOT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- Seed Data
-- ============================================================

-- 管理员（默认密码: admin123）
INSERT INTO admins (username, password_hash, role) VALUES
('admin', 'pbkdf2:sha256:600000$salt$hash', 'admin');

-- 专题
INSERT INTO topics (id, title, description, difficulty, icon, color, is_high_freq) VALUES
(1001, '加法与减法',   '掌握基本加减法运算',                  'L1-L2', 'plus',    '#FF6B6B', 1),
(1002, '乘法与除法',   '学习乘除法基础',                      'L2-L3', 'times',   '#4ECDC4', 1),
(1003, '分数与小数',   '理解分数与小数的概念',                'L3-L4', 'divide',  '#45B7D1', 1),
(1004, '几何图形',     '认识基本几何图形及其性质',            'L2-L4', 'shapes',  '#96CEB4', 1),
(1005, '逻辑推理',     '培养逻辑思维与推理能力',              'L3-L5', 'brain',   '#FFEAA7', 1),
(1006, '单位换算',     '掌握常见单位及其换算关系',            'L2-L3', 'ruler',   '#DDA0DD', 0),
(1007, '应用题',       '综合运用数学知识解决实际问题',        'L3-L5', 'pencil',  '#98D8C8', 1),
(1008, '概率与统计',   '初步了解概率与统计概念',              'L4-L6', 'chart',   '#F7DC6F', 0);

-- 题目（加法与减法）
INSERT INTO questions (id, topic_id, title, content, question_type, options, answer, explanation, difficulty_level, tags) VALUES
(2001, 1001, '10以内加法', '{"text": "计算：3 + 5 = ?"}', 'single',
 '[{"label": "A", "content": {"text": "7"}}, {"label": "B", "content": {"text": "8"}}, {"label": "C", "content": {"text": "9"}}, {"label": "D", "content": {"text": "6"}}]',
 'B', '{"text": "3 + 5 = 8，将3和5合并在一起得到8。"}', 1, '["加法", "基础"]'),

(2002, 1001, '凑十法', '{"text": "计算：8 + 6 = ?"}', 'single',
 '[{"label": "A", "content": {"text": "12"}}, {"label": "B", "content": {"text": "13"}}, {"label": "C", "content": {"text": "14"}}, {"label": "D", "content": {"text": "15"}}]',
 'C', '{"text": "8 + 6 = 14。用凑十法：8 + 2 = 10，6 - 2 = 4，10 + 4 = 14。"}', 1, '["加法", "凑十法"]'),

(2003, 1001, '两位数减法', '{"text": "计算：56 - 29 = ?"}', 'single',
 '[{"label": "A", "content": {"text": "27"}}, {"label": "B", "content": {"text": "25"}}, {"label": "C", "content": {"text": "33"}}, {"label": "D", "content": {"text": "37"}}]',
 'A', '{"text": "56 - 29 = 27。先算56 - 20 = 36，再算36 - 9 = 27。"}', 2, '["减法", "退位"]'),

(2004, 1001, '连加运算', '{"text": "计算：12 + 8 + 15 = ?"}', 'single',
 '[{"label": "A", "content": {"text": "30"}}, {"label": "B", "content": {"text": "33"}}, {"label": "C", "content": {"text": "35"}}, {"label": "D", "content": {"text": "37"}}]',
 'C', '{"text": "12 + 8 + 15 = 35。先算12 + 8 = 20，再算20 + 15 = 35。"}', 2, '["加法", "连加"]'),

(2005, 1001, '加减混合', '{"text": "计算：25 + 17 - 13 = ?"}', 'single',
 '[{"label": "A", "content": {"text": "27"}}, {"label": "B", "content": {"text": "29"}}, {"label": "C", "content": {"text": "31"}}, {"label": "D", "content": {"text": "33"}}]',
 'B', '{"text": "25 + 17 - 13 = 29。先算25 + 17 = 42，再算42 - 13 = 29。"}', 2, '["加减混合"]');

-- 题目（乘法与除法）
INSERT INTO questions (id, topic_id, title, content, question_type, options, answer, explanation, difficulty_level, tags) VALUES
(2006, 1002, '乘法口诀', '{"text": "计算：7 × 8 = ?"}', 'single',
 '[{"label": "A", "content": {"text": "48"}}, {"label": "B", "content": {"text": "54"}}, {"label": "C", "content": {"text": "56"}}, {"label": "D", "content": {"text": "63"}}]',
 'C', '{"text": "7 × 8 = 56。乘法口诀：七八五十六。"}', 2, '["乘法", "口诀"]'),

(2007, 1002, '除法基础', '{"text": "计算：72 ÷ 8 = ?"}', 'single',
 '[{"label": "A", "content": {"text": "7"}}, {"label": "B", "content": {"text": "8"}}, {"label": "C", "content": {"text": "9"}}, {"label": "D", "content": {"text": "10"}}]',
 'C', '{"text": "72 ÷ 8 = 9。因为 8 × 9 = 72。"}', 2, '["除法"]'),

(2008, 1002, '带余除法', '{"text": "计算：50 ÷ 6 = ?（商和余数）"}', 'single',
 '[{"label": "A", "content": {"text": "7 余 8"}}, {"label": "B", "content": {"text": "8 余 2"}}, {"label": "C", "content": {"text": "8 余 4"}}, {"label": "D", "content": {"text": "7 余 6"}}]',
 'B', '{"text": "50 ÷ 6 = 8 余 2。因为 6 × 8 = 48，50 - 48 = 2。"}', 3, '["除法", "余数"]'),

(2009, 1002, '乘法应用', '{"text": "一盒铅笔有12支，买4盒一共有多少支铅笔？"}', 'single',
 '[{"label": "A", "content": {"text": "36"}}, {"label": "B", "content": {"text": "40"}}, {"label": "C", "content": {"text": "44"}}, {"label": "D", "content": {"text": "48"}}]',
 'D', '{"text": "12 × 4 = 48。每盒12支，4盒就是4个12相加。"}', 3, '["乘法", "应用题"]');

-- 题目（分数与小数）
INSERT INTO questions (id, topic_id, title, content, question_type, options, answer, explanation, difficulty_level, tags) VALUES
(2010, 1003, '分数比较', '{"text": "比较大小：1/4 和 1/3，哪个更大？"}', 'single',
 '[{"label": "A", "content": {"text": "1/4"}}, {"label": "B", "content": {"text": "1/3"}}, {"label": "C", "content": {"text": "一样大"}}, {"label": "D", "content": {"text": "无法比较"}}]',
 'B', '{"text": "1/3 > 1/4。分子相同，分母越小分数越大。"}', 3, '["分数", "比较"]'),

(2011, 1003, '分数加法', '{"text": "计算：1/5 + 2/5 = ?"}', 'single',
 '[{"label": "A", "content": {"text": "2/5"}}, {"label": "B", "content": {"text": "3/5"}}, {"label": "C", "content": {"text": "3/10"}}, {"label": "D", "content": {"text": "2/10"}}]',
 'B', '{"text": "1/5 + 2/5 = 3/5。分母相同，分子相加。"}', 3, '["分数", "加法"]'),

(2012, 1003, '小数加减', '{"text": "计算：3.6 + 1.8 = ?"}', 'single',
 '[{"label": "A", "content": {"text": "4.4"}}, {"label": "B", "content": {"text": "5.2"}}, {"label": "C", "content": {"text": "5.4"}}, {"label": "D", "content": {"text": "4.8"}}]',
 'C', '{"text": "3.6 + 1.8 = 5.4。对齐小数点相加。"}', 3, '["小数", "加法"]');

-- 题目（几何图形）
INSERT INTO questions (id, topic_id, title, content, question_type, options, answer, explanation, difficulty_level, tags) VALUES
(2013, 1004, '三角形分类', '{"text": "三条边都相等的三角形叫做什么？"}', 'single',
 '[{"label": "A", "content": {"text": "等腰三角形"}}, {"label": "B", "content": {"text": "等边三角形"}}, {"label": "C", "content": {"text": "直角三角形"}}, {"label": "D", "content": {"text": "钝角三角形"}}]',
 'B', '{"text": "三条边都相等的三角形叫做等边三角形。"}', 2, '["几何", "三角形"]'),

(2014, 1004, '周长计算', '{"text": "一个正方形边长为6厘米，它的周长是多少厘米？"}', 'single',
 '[{"label": "A", "content": {"text": "24"}}, {"label": "B", "content": {"text": "36"}}, {"label": "C", "content": {"text": "12"}}, {"label": "D", "content": {"text": "18"}}]',
 'A', '{"text": "正方形周长 = 边长 × 4 = 6 × 4 = 24 厘米。"}', 2, '["几何", "周长"]'),

(2015, 1004, '面积计算', '{"text": "一个长方形长8米，宽5米，面积是多少平方米？"}', 'single',
 '[{"label": "A", "content": {"text": "26"}}, {"label": "B", "content": {"text": "40"}}, {"label": "C", "content": {"text": "35"}}, {"label": "D", "content": {"text": "45"}}]',
 'B', '{"text": "长方形面积 = 长 × 宽 = 8 × 5 = 40 平方米。"}', 3, '["几何", "面积"]');

-- 题目（逻辑推理）
INSERT INTO questions (id, topic_id, title, content, question_type, options, answer, explanation, difficulty_level, tags) VALUES
(2016, 1005, '找规律 - 数列', '{"text": "找规律：2, 4, 6, 8, ?"}', 'single',
 '[{"label": "A", "content": {"text": "9"}}, {"label": "B", "content": {"text": "10"}}, {"label": "C", "content": {"text": "11"}}, {"label": "D", "content": {"text": "12"}}]',
 'B', '{"text": "这是一个等差数列，每次增加2，8 + 2 = 10。"}', 1, '["规律", "数列"]'),

(2017, 1005, '图形推理', '{"text": "△ ○ □ △ ○ ? 请问问号处应该是什么图形？"}', 'single',
 '[{"label": "A", "content": {"text": "△"}}, {"label": "B", "content": {"text": "○"}}, {"label": "C", "content": {"text": "□"}}, {"label": "D", "content": {"text": "☆"}}]',
 'C', '{"text": "图形按 △ → ○ → □ 循环排列，△ ○ □ 之后下一个应该是 □。"}', 2, '["规律", "图形"]'),

(2018, 1005, '逻辑判断', '{"text": "小明比小红高，小红比小刚高，谁最高？"}', 'single',
 '[{"label": "A", "content": {"text": "小明"}}, {"label": "B", "content": {"text": "小红"}}, {"label": "C", "content": {"text": "小刚"}}, {"label": "D", "content": {"text": "一样高"}}]',
 'A', '{"text": "小明 > 小红 > 小刚，所以小明最高。"}', 2, '["逻辑", "比较"]');

-- 题目（单位换算）
INSERT INTO questions (id, topic_id, title, content, question_type, options, answer, explanation, difficulty_level, tags) VALUES
(2019, 1006, '长度换算', '{"text": "1 米 = ? 厘米"}', 'single',
 '[{"label": "A", "content": {"text": "10"}}, {"label": "B", "content": {"text": "50"}}, {"label": "C", "content": {"text": "100"}}, {"label": "D", "content": {"text": "1000"}}]',
 'C', '{"text": "1 米 = 100 厘米。"}', 1, '["单位", "长度"]'),

(2020, 1006, '时间换算', '{"text": "2 小时 30 分钟 = ? 分钟"}', 'single',
 '[{"label": "A", "content": {"text": "130"}}, {"label": "B", "content": {"text": "150"}}, {"label": "C", "content": {"text": "230"}}, {"label": "D", "content": {"text": "120"}}]',
 'B', '{"text": "2 小时 = 120 分钟，120 + 30 = 150 分钟。"}', 2, '["单位", "时间"]'),

(2021, 1006, '重量换算', '{"text": "3 千克 500 克 = ? 克"}', 'single',
 '[{"label": "A", "content": {"text": "350"}}, {"label": "B", "content": {"text": "3500"}}, {"label": "C", "content": {"text": "3050"}}, {"label": "D", "content": {"text": "3005"}}]',
 'B', '{"text": "3 千克 = 3000 克，3000 + 500 = 3500 克。"}', 2, '["单位", "重量"]');

-- 题目（应用题）
INSERT INTO questions (id, topic_id, title, content, question_type, options, answer, explanation, difficulty_level, tags) VALUES
(2022, 1007, '购物问题', '{"text": "小明带了50元去买文具，买了一个书包花了28元，又买了一支笔花了6元，还剩多少钱？"}', 'single',
 '[{"label": "A", "content": {"text": "14"}}, {"label": "B", "content": {"text": "16"}}, {"label": "C", "content": {"text": "18"}}, {"label": "D", "content": {"text": "20"}}]',
 'B', '{"text": "50 - 28 - 6 = 16 元。总共花了 28 + 6 = 34 元，50 - 34 = 16 元。"}', 3, '["应用", "购物"]'),

(2023, 1007, '植树问题', '{"text": "在一条100米长的道路一边每隔5米种一棵树（两端都种），需要种多少棵树？"}', 'single',
 '[{"label": "A", "content": {"text": "19"}}, {"label": "B", "content": {"text": "20"}}, {"label": "C", "content": {"text": "21"}}, {"label": "D", "content": {"text": "22"}}]',
 'C', '{"text": "100 ÷ 5 = 20 个间隔，两端都种则棵数 = 间隔数 + 1 = 21 棵。"}', 4, '["应用", "植树"]'),

(2024, 1007, '年龄问题', '{"text": "爸爸今年36岁，小明今年8岁。几年后爸爸的年龄是小明的3倍？"}', 'single',
 '[{"label": "A", "content": {"text": "4"}}, {"label": "B", "content": {"text": "5"}}, {"label": "C", "content": {"text": "6"}}, {"label": "D", "content": {"text": "7"}}]',
 'C', '{"text": "设x年后，36 + x = 3(8 + x)，解得 x = 6。"}', 5, '["应用", "年龄"]');

-- 题目（概率与统计）
INSERT INTO questions (id, topic_id, title, content, question_type, options, answer, explanation, difficulty_level, tags) VALUES
(2025, 1008, '平均数', '{"text": "一组数据：5, 8, 7, 6, 9，这组数据的平均数是多少？"}', 'single',
 '[{"label": "A", "content": {"text": "6"}}, {"label": "B", "content": {"text": "7"}}, {"label": "C", "content": {"text": "8"}}, {"label": "D", "content": {"text": "9"}}]',
 'B', '{"text": "(5 + 8 + 7 + 6 + 9) ÷ 5 = 35 ÷ 5 = 7。"}', 3, '["统计", "平均数"]'),

(2026, 1008, '概率初步', '{"text": "一个盒子里有3个红球和5个蓝球，随机摸出一个球，摸到红球的概率是多少？"}', 'single',
 '[{"label": "A", "content": {"text": "1/3"}}, {"label": "B", "content": {"text": "3/5"}}, {"label": "C", "content": {"text": "3/8"}}, {"label": "D", "content": {"text": "5/8"}}]',
 'C', '{"text": "红球 3 个，总共 3 + 5 = 8 个球，概率 = 3/8。"}', 4, '["概率"]');

-- 考卷
INSERT INTO exam_papers (id, title, difficulty_level, total_questions, description, paper_type, is_new) VALUES
(3001, '每日一练 - 加减法基础', 1, 5, '适合G1-G2学生的加减法基础练习', 'daily', 1),
(3002, '每日一练 - 乘除法进阶', 2, 5, '适合G2-G3学生的乘除法进阶练习', 'daily', 1),
(3003, '期中模拟测试卷', 3, 5, '覆盖加减法、乘除法、几何图形的综合测试', 'mock', 1),
(3004, '几何图形专项训练', 2, 5, '几何图形知识点集中练习', 'topic', 1);

-- 考卷题目关联
INSERT INTO exam_paper_questions (exam_paper_id, question_id, sort) VALUES
-- 每日一练 - 加减法基础（题型按难度递增）
(3001, 2001, 1),
(3001, 2002, 2),
(3001, 2003, 3),
(3001, 2004, 4),
(3001, 2005, 5),
-- 每日一练 - 乘除法进阶
(3002, 2006, 1),
(3002, 2007, 2),
(3002, 2008, 3),
(3002, 2009, 4),
(3002, 2022, 5),
-- 期中模拟测试卷
(3003, 2003, 1),
(3003, 2006, 2),
(3003, 2011, 3),
(3003, 2013, 4),
(3003, 2014, 5),
-- 几何图形专项训练
(3004, 2013, 1),
(3004, 2014, 2),
(3004, 2015, 3),
(3004, 2017, 4),
(3004, 2023, 5);
