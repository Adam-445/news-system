DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'newsuser') THEN
        CREATE ROLE newsuser WITH LOGIN PASSWORD 'newspass' NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
END $$;

-- Separate CREATE DATABASE from DO $$ block
SELECT 'CREATE DATABASE newsdb OWNER newsuser'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'newsdb')\gexec
