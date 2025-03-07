#!/bin/sh
# Exit immediately if any command fails
set -e

echo "Waiting for PostgreSQL to initialize..."
# Maximum number of attempts to check database readiness
max_retries=30

# Retry counter
retry=0

# Loop until PostgreSQL is ready, or until max_retries is reached
until PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c '\q' >/dev/null 2>&1; do
  retry=$((retry + 1))
  if [ $retry -ge $max_retries ]; then
    echo "Error: PostgreSQL not ready after $max_retries attempts!"
    # Exit with an error iff the database is not ready
    exit 1
  fi
  # Wait for 2 seconds before retrying
  sleep 2
done
echo "PostgreSQL is ready."

# --- User Management ---
# Check if the database user already exists
USER_EXISTS=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='${DB_USER}'" || true)

if [ "$USER_EXISTS" != "1" ]; then
  echo "Creating secure database user: ${DB_USER}"
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres <<-EOSQL
    CREATE USER ${DB_USER} WITH 
      PASSWORD '${DB_PASSWORD}'
      NOCREATEROLE  -- Prevent user from creating other roles
      CONNECTION LIMIT 100;  -- Limit the number of concurrent connections
EOSQL
else
  echo "User ${DB_USER} already exists, skipping creation."
fi

# --- Database Setup ---
# Loop through the main database and the test database
for DB in "${DB_NAME}" "${DB_NAME}_test"; do
  # Check if the database already exists
  # The command returns 1 if the database does not exist
  DB_EXISTS=$(PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='${DB}'" || true)

  if [ "$DB_EXISTS" != "1" ]; then
    echo "Creating database: ${DB}"
    PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c "CREATE DATABASE ${DB} OWNER ${DB_USER};"
  else
    echo "Database ${DB} already exists, skipping creation."
  fi

  # --- Security Configuration ---
  echo "Configuring security for ${DB}"
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d "$DB" <<-EOSQL
    REVOKE CREATE ON SCHEMA public FROM PUBLIC;  -- Restrict public schema modifications
    GRANT USAGE ON SCHEMA public TO ${DB_USER};  -- Allow user to use the schema
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ${DB_USER};  -- Grant default table privileges
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO ${DB_USER};  -- Grant default sequence privileges
EOSQL
done

echo "Applying database migrations..."
# Run database migrations using Alembic
alembic upgrade head

echo "Database initialization complete."
# Execute the command provided as arguments to the script
exec "$@"