-- Script to create PostgreSQL database for PneuShop
-- Run this script as postgres user: psql -U postgres -f create_database.sql

-- Create database
CREATE DATABASE pneushop_db;

-- Create user (optional, you can use existing postgres user)
CREATE USER pneushop_user WITH PASSWORD 'pneushop_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE pneushop_db TO pneushop_user;

-- Connect to the database
\c pneushop_db;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO pneushop_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pneushop_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pneushop_user;

-- Display success message
SELECT 'Database pneushop_db created successfully!' as message;
