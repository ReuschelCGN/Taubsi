SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+01:00";


CREATE TABLE IF NOT EXISTS `users` (
  `user_id` bigint(20) NOT NULL,
  `level` int(10),
  `team_id` int(10),
  `friendcode` varchar(12),
  `name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `ingame_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `raids` (
  `channel_id` bigint(20) NOT NULL,
  `message_id` bigint(20) NOT NULL,
  `init_message_id` bigint(20) NOT NULL,
  `gym_id` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_time` datetime NOT NULL,
  `mon_id` int(11) DEFAULT NULL,
  `mon_form` int(10) DEFAULT NULL,
  `raid_level` int(10) DEFAULT 0,
  `raid_start` datetime DEFAULT NULL,
  `raid_end` datetime DEFAULT NULL,
  `role_id` bigint(20) DEFAULT NULL,
  PRIMARY KEY (`message_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `raidmembers` (
  `message_id` bigint(20) NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `amount` int(10) DEFAULT NULL,
  `is_late` tinyint(1) DEFAULT 0,
  `is_remote` tinyint(1) DEFAULT 0,
  `is_invite` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`message_id`, `user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4;