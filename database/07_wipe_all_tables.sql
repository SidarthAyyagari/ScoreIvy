-- Wipe All Tables Script
-- This script deletes all data from all tables
-- Use with caution - this will delete ALL data!

-- Disable foreign key checks temporarily (PostgreSQL doesn't need this, but being explicit)
-- Delete in reverse order of dependencies to avoid foreign key violations

-- Delete data from tables with foreign keys first
DELETE FROM question_attempts;
DELETE FROM test_attempts;
DELETE FROM test_questions;
DELETE FROM test_sections;
DELETE FROM user_packages;
DELETE FROM tests;
DELETE FROM questions;
DELETE FROM packages;
DELETE FROM sections;
DELETE FROM users;

-- Reset all sequences to start from 1
ALTER SEQUENCE users_id_seq RESTART WITH 1;
ALTER SEQUENCE sections_id_seq RESTART WITH 1;
ALTER SEQUENCE questions_id_seq RESTART WITH 1;
ALTER SEQUENCE packages_id_seq RESTART WITH 1;
ALTER SEQUENCE user_packages_id_seq RESTART WITH 1;
ALTER SEQUENCE tests_id_seq RESTART WITH 1;
ALTER SEQUENCE test_sections_id_seq RESTART WITH 1;
ALTER SEQUENCE test_questions_id_seq RESTART WITH 1;
ALTER SEQUENCE test_attempts_id_seq RESTART WITH 1;
ALTER SEQUENCE question_attempts_id_seq RESTART WITH 1;

-- Alternatively, use TRUNCATE CASCADE (more efficient, but also drops dependent data)
-- Uncomment the following lines to use TRUNCATE instead of DELETE:
-- TRUNCATE TABLE question_attempts CASCADE;
-- TRUNCATE TABLE test_attempts CASCADE;
-- TRUNCATE TABLE test_questions CASCADE;
-- TRUNCATE TABLE test_sections CASCADE;
-- TRUNCATE TABLE user_packages CASCADE;
-- TRUNCATE TABLE tests CASCADE;
-- TRUNCATE TABLE questions CASCADE;
-- TRUNCATE TABLE packages CASCADE;
-- TRUNCATE TABLE sections CASCADE;
-- TRUNCATE TABLE users CASCADE;

