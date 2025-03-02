#!/bin/sh
set -e

echo "Waiting for PostgreSQL to initialize..."
max_retries=30
retry=0

until PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c '\q' >/dev/null 2>&1; do
  retry=$((retry + 1))
  if [ $retry -ge $max_retries ]; then
    echo "Error: PostgreSQL not ready after $max_retries attempts!"
    exit 1
  fi
  sleep 2
done
echo "PostgreSQL is ready."

# User Management
USER_EXISTS=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" || true)
if [ "$USER_EXISTS" != "1" ]; then
  echo "Creating secure database user: ${DB_USER}"
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres <<-EOSQL
    CREATE USER ${DB_USER} WITH 
      PASSWORD '${DB_PASSWORD}'
      NOCREATEROLE
      CONNECTION LIMIT 100;
EOSQL
else
  echo "User ${DB_USER} already exists, skipping creation."
fi

# Database Setup
for DB in "${DB_NAME}" "${DB_NAME}_test"; do
  # Database Creation
  DB_EXISTS=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB}'" || true)
  if [ "$DB_EXISTS" != "1" ]; then
    echo "Creating database: ${DB}"
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c "CREATE DATABASE ${DB} OWNER ${DB_USER};"
  else
    echo "Database ${DB} already exists, skipping creation."
  fi

  # Security Configuration
  echo "Configuring security for ${DB}"
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d "$DB" <<-EOSQL
    REVOKE CREATE ON SCHEMA public FROM PUBLIC;
    GRANT USAGE ON SCHEMA public TO ${DB_USER};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${DB_USER};
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO ${DB_USER};
EOSQL
done

echo "Applying database migrations..."
alembic upgrade head

echo "Production database initialization complete."
exec "$@"