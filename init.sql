-- Initialize database
CREATE DATABASE IF NOT EXISTS lawyers_db;
CREATE USER IF NOT EXISTS crawler WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE lawyers_db TO crawler;
