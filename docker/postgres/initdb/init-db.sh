#!/bin/sh
set -eu

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c '\q' 2>/dev/null; do
  sleep 2
done
echo "PostgreSQL is ready!"

# Ensure the user exists
if ! PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -tc "SELECT 1 FROM pg_roles WHERE rolname = '${DB_USER}'" | grep -q 1; then
  echo "Creating user ${DB_USER}..."
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c "CREATE USER ${DB_USER} WITH ENCRYPTED PASSWORD '${DB_PASSWORD}'"
  echo "User ${DB_USER} created."
fi

# Ensure main database exists and is owned by DB_USER
if ! PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}'" | grep -q 1; then
  echo "Creating database ${DB_NAME}..."
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER}"
  echo "Database ${DB_NAME} created."
fi

# Ensure test database exists and is owned by DB_USER
if ! PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -tc "SELECT 1 FROM pg_database WHERE datname = '${DB_NAME}_test'" | grep -q 1; then
  echo "Creating test database ${DB_NAME}_test..."
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c "CREATE DATABASE ${DB_NAME}_test OWNER ${DB_USER}"
  echo "Test database ${DB_NAME}_test created."
fi

# Grant database privileges
echo "Ensuring ${DB_USER} has privileges on ${DB_NAME} and ${DB_NAME}_test..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c "ALTER DATABASE ${DB_NAME} OWNER TO ${DB_USER};"
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d postgres -c "ALTER DATABASE ${DB_NAME}_test OWNER TO ${DB_USER};"

# Grant schema-level privileges
for DB in ${DB_NAME} ${DB_NAME}_test; do
  echo "Granting schema privileges to ${DB_USER} on ${DB}..."
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d "$DB" -c "GRANT ALL PRIVILEGES ON SCHEMA public TO ${DB_USER};"
  PGPASSWORD="${POSTGRES_PASSWORD}" psql -h db -U "${POSTGRES_USER}" -d "$DB" -c "ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};"
done
echo "Schema privileges granted."

# Apply Alembic migrations
echo "Applying database migrations..."
alembic upgrade head
echo "Migrations applied successfully."

exec "$@"
