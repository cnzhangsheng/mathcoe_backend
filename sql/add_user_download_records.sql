-- ============================================
-- 新增用户下载记录表 user_download_records
-- ============================================

CREATE TABLE `user_download_records` (
    `id` bigint(20) NOT NULL,
    `user_id` bigint(20) NOT NULL COMMENT '用户ID',
    `exam_paper_id` bigint(20) NOT NULL COMMENT '考卷ID',
    `exam_paper_title` varchar(128) NOT NULL COMMENT '考卷标题',
    `downloaded_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '下载时间',
    `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_user_download_records_user_id` (`user_id`),
    KEY `ix_user_download_records_exam_paper_id` (`exam_paper_id`),
    KEY `ix_user_download_records_downloaded_at` (`downloaded_at` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户下载记录表';