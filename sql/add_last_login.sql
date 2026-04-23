-- 添加 last_login_at 字段到 users 表
-- 如果表已存在，执行此语句添加新字段

-- 添加 last_login_at 字段
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP;

-- 添加字段注释
COMMENT ON COLUMN users.last_login_at IS '最后登录时间';

-- 初始化现有用户的 last_login_at 为 created_at（首次登录）
UPDATE users SET last_login_at = created_at WHERE last_login_at IS NULL;