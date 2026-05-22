-- ============================================
-- 索引优化脚本 — mathcoe_db
-- 说明：
-- 1. 删除冗余索引（PK 上的二级索引、被 UNIQUE 覆盖的索引）
-- 2. 删除低选择性单列索引，替换为复合索引
-- 3. 新增核心查询所需的复合索引
-- 4. 新增 UNIQUE 约束（likes 表缺少）
-- ============================================

-- ==================== 1. 删除冗余索引 ====================

-- admins：ix_admins_username 被 UNIQUE KEY 覆盖，ix_admins_id 是 PK 冗余
DROP INDEX `ix_admins_username` ON `admins`;
DROP INDEX `ix_admins_id` ON `admins`;

-- exam_paper_questions：ix_exam_paper_questions_id 是 PK 冗余；ix_exam_paper_questions_exam_paper_id 被 UNIQUE 左前缀覆盖
DROP INDEX `ix_exam_paper_questions_id` ON `exam_paper_questions`;
DROP INDEX `ix_exam_paper_questions_exam_paper_id` ON `exam_paper_questions`;

-- exam_paper_test_answers：ix_exam_paper_test_answers_id 是 PK 冗余
DROP INDEX `ix_exam_paper_test_answers_id` ON `exam_paper_test_answers`;

-- exam_paper_tests：ix_exam_paper_tests_id 是 PK 冗余
DROP INDEX `ix_exam_paper_tests_id` ON `exam_paper_tests`;

-- exam_papers：ix_exam_papers_id 是 PK 冗余
DROP INDEX `ix_exam_papers_id` ON `exam_papers`;

-- favorites：ix_favorites_id 是 PK 冗余；ix_favorites_user_id 被 UNIQUE 左前缀覆盖
DROP INDEX `ix_favorites_id` ON `favorites`;
DROP INDEX `ix_favorites_user_id` ON `favorites`;

-- likes：ix_likes_id 是 PK 冗余
DROP INDEX `ix_likes_id` ON `likes`;

-- practice_records：ix_practice_records_id 是 PK 冗余；ix_is_correct 单列选择性低，替换为复合索引
DROP INDEX `ix_practice_records_id` ON `practice_records`;
DROP INDEX `ix_practice_records_is_correct` ON `practice_records`;

-- questions：ix_questions_id 是 PK 冗余
DROP INDEX `ix_questions_id` ON `questions`;

-- topics：ix_topics_id 是 PK 冗余
DROP INDEX `ix_topics_id` ON `topics`;

-- users：ix_users_id 是 PK 冗余；ix_users_openid 被 UNIQUE 覆盖
DROP INDEX `ix_users_id` ON `users`;
DROP INDEX `ix_users_openid` ON `users`;

-- wrong_questions：ix_wrong_questions_id 是 PK 冗余；ix_wrong_questions_user_id 被 UNIQUE 左前缀覆盖；ix_mastered 低选择性，替换为复合索引
DROP INDEX `ix_wrong_questions_id` ON `wrong_questions`;
DROP INDEX `ix_wrong_questions_user_id` ON `wrong_questions`;
DROP INDEX `ix_wrong_questions_mastered` ON `wrong_questions`;


-- ==================== 2. 新增 UNIQUE 约束 ====================

-- likes：防止重复点赞
ALTER TABLE `likes` ADD UNIQUE KEY `uq_user_question_like` (`user_id`, `question_id`);


-- ==================== 3. 新增复合索引 ====================

-- practice_records
-- 用户答题记录列表（按时间倒序）
ALTER TABLE `practice_records` ADD INDEX `ix_practice_records_user_created` (`user_id`, `created_at` DESC);
-- 用户正确率统计（本周/本月）
ALTER TABLE `practice_records` ADD INDEX `ix_practice_records_user_correct` (`user_id`, `is_correct`, `created_at` DESC);
-- 题目正确率统计
ALTER TABLE `practice_records` ADD INDEX `ix_practice_records_question_correct` (`question_id`, `is_correct`);

-- wrong_questions：用户未掌握错题列表
ALTER TABLE `wrong_questions` ADD INDEX `ix_wrong_questions_user_mastered` (`user_id`, `mastered`);

-- exam_paper_tests：用户考试列表（按状态筛选 + 时间倒序）
ALTER TABLE `exam_paper_tests` ADD INDEX `ix_exam_paper_tests_user_status` (`user_id`, `status`, `created_at` DESC);

-- exam_paper_test_answers：阅卷时按 test_id + 题号查找
ALTER TABLE `exam_paper_test_answers` ADD INDEX `ix_exam_paper_test_answers_test_question` (`test_id`, `question_index`);

-- exam_papers：试卷浏览筛选（状态 + 类型 + 难度）
ALTER TABLE `exam_papers` ADD INDEX `ix_exam_papers_status_type_level` (`status`, `paper_type`, `difficulty_level`);
-- exam_papers：用户生成的试卷
ALTER TABLE `exam_papers` ADD INDEX `ix_exam_papers_user_id` (`user_id`);

-- questions：按专题 + 难度 + 状态筛选题目
ALTER TABLE `questions` ADD INDEX `ix_questions_topic_difficulty_status` (`topic_id`, `difficulty_level`, `status`);
-- questions：状态筛选（管理员端）
ALTER TABLE `questions` ADD INDEX `ix_questions_status` (`status`);

-- favorites：用户收藏列表按时间倒序
ALTER TABLE `favorites` ADD INDEX `ix_favorites_user_created` (`user_id`, `created_at` DESC);

-- users：用户等级筛选 + 连续天数计算
ALTER TABLE `users` ADD INDEX `ix_users_user_tier` (`user_tier`);
ALTER TABLE `users` ADD INDEX `ix_users_last_active` (`last_active_date`);

-- topics：高频考点筛选
ALTER TABLE `topics` ADD INDEX `ix_topics_high_freq` (`is_high_freq`);

-- banners：按位置 + 启用状态 + 排序查询
ALTER TABLE `banners` ADD INDEX `ix_banners_position_active_sort` (`position`, `is_active`, `sort_order`);

-- contents：内容列表按状态筛选 + 时间倒序
ALTER TABLE `contents` ADD INDEX `ix_contents_status_created` (`status`, `created_at` DESC);

-- feedbacks：管理员按状态筛选 + 用户查看自己的反馈
ALTER TABLE `feedbacks` ADD INDEX `ix_feedbacks_status_created` (`status`, `created_at` DESC);
ALTER TABLE `feedbacks` ADD INDEX `ix_feedbacks_user_created` (`user_id`, `created_at` DESC);


-- ==================== 4. 汇总统计 ====================
-- 删除索引：19 个
-- 新增 UNIQUE：1 个
-- 新增索引：18 个
-- 净变动：-1 个索引（36 → 35）