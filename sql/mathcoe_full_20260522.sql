-- MySQL dump 10.13  Distrib 8.0.46, for macos14.8 (x86_64)
--
-- Host: 127.0.0.1    Database: mathcoe_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `admins`
--

DROP TABLE IF EXISTS `admins`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `admins` (
  `id` bigint NOT NULL,
  `username` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `password_hash` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `role` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'admin',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `ix_admins_username` (`username`),
  KEY `ix_admins_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='后台管理员表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `exam_paper_questions`
--

DROP TABLE IF EXISTS `exam_paper_questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exam_paper_questions` (
  `id` bigint NOT NULL,
  `exam_paper_id` bigint NOT NULL,
  `question_id` bigint NOT NULL,
  `sort` int NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_exam_paper_question` (`exam_paper_id`,`question_id`),
  KEY `ix_exam_paper_questions_id` (`id`),
  KEY `ix_exam_paper_questions_exam_paper_id` (`exam_paper_id`),
  KEY `ix_exam_paper_questions_question_id` (`question_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='考卷题目关联表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `exam_paper_test_answers`
--

DROP TABLE IF EXISTS `exam_paper_test_answers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exam_paper_test_answers` (
  `id` bigint NOT NULL,
  `test_id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `exam_paper_id` bigint NOT NULL,
  `question_index` int NOT NULL,
  `question_id` bigint NOT NULL,
  `user_answer` varchar(4) COLLATE utf8mb4_unicode_ci NOT NULL,
  `correct_answer` varchar(4) COLLATE utf8mb4_unicode_ci NOT NULL,
  `is_correct` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_exam_paper_test_answers_id` (`id`),
  KEY `ix_exam_paper_test_answers_test_id` (`test_id`),
  KEY `ix_exam_paper_test_answers_user_id` (`user_id`),
  KEY `ix_exam_paper_test_answers_exam_paper_id` (`exam_paper_id`),
  KEY `ix_exam_paper_test_answers_question_id` (`question_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='考卷答题记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `exam_paper_tests`
--

DROP TABLE IF EXISTS `exam_paper_tests`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exam_paper_tests` (
  `id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `exam_paper_id` bigint NOT NULL,
  `score` int DEFAULT NULL,
  `correct_count` int DEFAULT NULL,
  `total_questions` int NOT NULL,
  `time_spent` int DEFAULT NULL,
  `started_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `finished_at` datetime DEFAULT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'in_progress',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_exam_paper_tests_id` (`id`),
  KEY `ix_exam_paper_tests_user_id` (`user_id`),
  KEY `ix_exam_paper_tests_exam_paper_id` (`exam_paper_id`),
  KEY `ix_exam_paper_tests_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='考卷测试记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `exam_papers`
--

DROP TABLE IF EXISTS `exam_papers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `exam_papers` (
  `id` bigint NOT NULL,
  `title` varchar(128) COLLATE utf8mb4_unicode_ci NOT NULL,
  `difficulty_level` int NOT NULL DEFAULT '1',
  `total_questions` int NOT NULL DEFAULT '10',
  `description` text COLLATE utf8mb4_unicode_ci,
  `paper_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'daily',
  `is_new` tinyint(1) NOT NULL DEFAULT '0',
  `user_id` bigint NOT NULL,
  `generation_config` json NULL,
  `file_path` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `status` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'unpublished' COMMENT '试卷上架状态',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_exam_papers_id` (`id`),
  KEY `ix_exam_papers_difficulty_level` (`difficulty_level`),
  KEY `ix_exam_papers_paper_type` (`paper_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='考卷表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `favorites`
--

DROP TABLE IF EXISTS `favorites`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `favorites` (
  `id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `question_id` bigint NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP, 
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_question_favorite` (`user_id`,`question_id`),
  KEY `ix_favorites_id` (`id`),
  KEY `ix_favorites_user_id` (`user_id`),
  KEY `ix_favorites_question_id` (`question_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户收藏题目表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `likes`
--

DROP TABLE IF EXISTS `likes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `likes` (
  `id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `question_id` bigint NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_likes_id` (`id`),
  KEY `ix_likes_user_id` (`user_id`),
  KEY `ix_likes_question_id` (`question_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='点赞记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `practice_records`
--

DROP TABLE IF EXISTS `practice_records`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `practice_records` (
  `id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `question_id` bigint NOT NULL,
  `user_answer` varchar(8) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_correct` tinyint(1) DEFAULT NULL,
  `time_spent` int DEFAULT NULL,
  `is_flagged` tinyint(1) NOT NULL DEFAULT '0',
  `is_bookmarked` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_practice_records_id` (`id`),
  KEY `ix_practice_records_user_id` (`user_id`),
  KEY `ix_practice_records_question_id` (`question_id`),
  KEY `ix_practice_records_is_correct` (`is_correct`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='答题记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `questions`
--

DROP TABLE IF EXISTS `questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `questions` (
  `id` bigint NOT NULL,
  `topic_id` bigint DEFAULT NULL,
  `title` varchar(200) COLLATE utf8mb4_unicode_ci NOT NULL,
  `content` json DEFAULT NULL,
  `question_type` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'single',
  `options` json DEFAULT NULL,
  `answer` varchar(32) COLLATE utf8mb4_unicode_ci NOT NULL,
  `explanation` json DEFAULT NULL,
  `difficulty_level` int DEFAULT NULL,
  `source_year` int DEFAULT NULL,
  `tags` json DEFAULT (_utf8mb4'[]'),
  `status` VARCHAR(16) NOT NULL DEFAULT 'unpublished',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_questions_id` (`id`),
  KEY `ix_questions_topic_id` (`topic_id`),
  KEY `ix_questions_difficulty_level` (`difficulty_level`),
  KEY `ix_questions_source_year` (`source_year`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='题目表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `topics`
--

DROP TABLE IF EXISTS `topics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `topics` (
  `id` bigint NOT NULL,
  `title` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `difficulty` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `icon` varchar(32) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `color` varchar(16) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `is_high_freq` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_topics_id` (`id`),
  KEY `ix_topics_difficulty` (`difficulty`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='专题训练分类表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` bigint NOT NULL,
  `openid` varchar(64) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nickname` varchar(64) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `avatar_url` varchar(256) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `grade` varchar(2) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'G1',
  `daily_goal` int NOT NULL DEFAULT '10',
  `difficulty_level` int NOT NULL DEFAULT '1',
  `streak_days` int NOT NULL DEFAULT '0',
  `last_active_date` date DEFAULT NULL,
  `last_login_at` datetime DEFAULT NULL,
  `user_tier` varchar(16) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'free',
  `tier_expires_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `openid` (`openid`),
  KEY `ix_users_openid` (`openid`),
  KEY `ix_users_id` (`id`),
  KEY `ix_users_grade` (`grade`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='微信小程序用户表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `wrong_questions`
--

DROP TABLE IF EXISTS `wrong_questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `wrong_questions` (
  `id` bigint NOT NULL,
  `user_id` bigint NOT NULL,
  `question_id` bigint NOT NULL,
  `retry_count` int NOT NULL DEFAULT '0',
  `last_retry_at` datetime DEFAULT NULL,
  `mastered` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_question_wrong` (`user_id`,`question_id`),
  KEY `ix_wrong_questions_id` (`id`),
  KEY `ix_wrong_questions_user_id` (`user_id`),
  KEY `ix_wrong_questions_question_id` (`question_id`),
  KEY `ix_wrong_questions_mastered` (`mastered`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户错题记录表';
/*!40101 SET character_set_client = @saved_cs_client */;

-- contents 表
DROP TABLE IF EXISTS `contents`;
CREATE TABLE `contents` (
    `id` BIGINT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NOT NULL,
    `slug` VARCHAR(128) NOT NULL,
    `status` VARCHAR(16) NOT NULL DEFAULT 'draft',
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    UNIQUE KEY uk_contents_slug (`slug`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='内容表';

-- banners 表
DROP TABLE IF EXISTS `banners`;
CREATE TABLE IF NOT EXISTS `banners` (
    `id` BIGINT NOT NULL,
    `image_url` VARCHAR(512) NOT NULL,
    `link_type` VARCHAR(16) NOT NULL DEFAULT 'content',
    `link_value` VARCHAR(512) NOT NULL DEFAULT '',
    `title` VARCHAR(255) NOT NULL DEFAULT '',
    `position` VARCHAR(32) NOT NULL DEFAULT 'home',
    `sort_order` INT NOT NULL DEFAULT 0,
    `is_active` TINYINT(1) NOT NULL DEFAULT 1,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Banner表';

-- feedbacks 表
DROP TABLE IF EXISTS `feedbacks`;
CREATE TABLE IF NOT EXISTS `feedbacks` (
    `id` BIGINT NOT NULL,
    `user_id` BIGINT NOT NULL,
    `content` TEXT NOT NULL,
    `contact` VARCHAR(64) DEFAULT NULL,
    `status` VARCHAR(16) NOT NULL DEFAULT 'pending',
    `admin_reply` TEXT DEFAULT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    KEY `ix_feedbacks_user_id` (`user_id`),
    CONSTRAINT `fk_feedbacks_user_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户意见反馈表';


--
-- Dumping routines for database 'mathcoe_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-18 11:01:29

-- End of dump
