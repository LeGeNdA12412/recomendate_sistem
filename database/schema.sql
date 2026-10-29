-- Schema for Movie Recommender System
-- Target: MySQL 8+

CREATE DATABASE IF NOT EXISTS `movie_recommender_db`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `movie_recommender_db`;

-- 1. Users Table
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `username` VARCHAR(100) NOT NULL UNIQUE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. Movies Table
CREATE TABLE IF NOT EXISTS `movies` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `title` VARCHAR(255) NOT NULL,
    `release_year` INT NULL,
    `genres` VARCHAR(255) NOT NULL,
    `director` VARCHAR(150) NULL,
    `cast` TEXT NULL,
    `description` TEXT NULL,
    `poster_url` VARCHAR(500) NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_title` (`title`),
    INDEX `idx_genres` (`genres`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Ratings Table
CREATE TABLE IF NOT EXISTS `ratings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `movie_id` INT NOT NULL,
    `rating` FLOAT NOT NULL,
    `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_ratings_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ratings_movie` FOREIGN KEY (`movie_id`) REFERENCES `movies` (`id`) ON DELETE CASCADE,
    CONSTRAINT `uq_user_movie_rating` UNIQUE (`user_id`, `movie_id`),
    INDEX `idx_user_movie` (`user_id`, `movie_id`),
    INDEX `idx_rating_value` (`rating`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
