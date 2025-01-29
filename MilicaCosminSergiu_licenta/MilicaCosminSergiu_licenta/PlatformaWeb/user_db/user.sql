CREATE DATABASE IF NOT EXISTS `user_db`;
USE `user_db`;

CREATE TABLE IF NOT EXISTS user (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(70) NOT NULL UNIQUE,
    type_user ENUM('admin', 'user') NOT NULL,
    phone CHAR(10) NOT NULL UNIQUE CHECK (phone REGEXP '^07[0-9]{8}$'),
    country VARCHAR(50)
);

CREATE INDEX idx_username ON user (username);

REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'cosmin'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON user_db.* TO 'cosmin'@'%';
