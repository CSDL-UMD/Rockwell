-- Create user if not exists
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'postgres') THEN
      CREATE ROLE postgres LOGIN PASSWORD 'postgres';
   END IF;
END
$$;

-- Set password in case the user already existed
ALTER USER postgres WITH PASSWORD 'postgres';

-- Create database if it doesn't exist
DO
$$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'rockwell') THEN
      CREATE DATABASE rockwell;
   END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE rockwell TO postgres;
