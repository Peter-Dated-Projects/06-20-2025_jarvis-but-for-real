#!/bin/bash

# ------------------------------------------------------------------ #
# Check if PostgreSQL 15 is installed via Homebrew
# ------------------------------------------------------------------ #

if ! brew list postgresql@15 &>/dev/null; then
    echo "PostgreSQL 15 is not installed. Installing..."
    brew install postgresql@15
else
    echo "PostgreSQL 15 is already installed."
fi

# Start PostgreSQL service
echo "Starting PostgreSQL service..."
brew services start postgresql@15

# Wait for PostgreSQL to start up
echo "Waiting for PostgreSQL to start..."
sleep 5

# Check if JARVIS user exists
if ! psql postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='JARVIS'" | grep -q 1; then
    echo "Creating JARVIS user..."
    psql postgres -c "CREATE USER \"JARVIS\" WITH PASSWORD 'jarvis_password';"
else
    echo "User JARVIS already exists."
fi

# Check if jarvis_brain database exists
if ! psql postgres -tAc "SELECT 1 FROM pg_database WHERE datname='jarvis_brain'" | grep -q 1; then
    echo "Creating jarvis_brain database..."
    psql postgres -c "CREATE DATABASE jarvis_brain;"
    
    # Grant admin permissions to JARVIS on jarvis_brain
    echo "Granting permissions to JARVIS..."
    psql postgres -c "GRANT ALL PRIVILEGES ON DATABASE jarvis_brain TO \"JARVIS\";"
else
    echo "Database jarvis_brain already exists."
fi

# Connect to jarvis_brain and create messages table
echo "Creating messages table..."
psql -d jarvis_brain -c "CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    message VARCHAR(16392) NOT NULL
);"

# Grant proper permissions to JARVIS user on the messages table
echo "Granting table permissions to JARVIS..."
psql -d jarvis_brain -c "GRANT ALL PRIVILEGES ON TABLE messages TO \"JARVIS\";"
psql -d jarvis_brain -c "GRANT ALL PRIVILEGES ON SEQUENCE messages_id_seq TO \"JARVIS\";"
psql -d jarvis_brain -c "GRANT USAGE ON SCHEMA public TO \"JARVIS\";"

# Set ownership of the messages table to JARVIS
echo "Setting table ownership to JARVIS..."
psql -d jarvis_brain -c "ALTER TABLE messages OWNER TO \"JARVIS\";"
psql -d jarvis_brain -c "ALTER SEQUENCE messages_id_seq OWNER TO \"JARVIS\";"

echo "PostgreSQL setup completed successfully!"


# ------------------------------------------------------------------ #
# run the backend flask server
# ------------------------------------------------------------------ #

source ../.venv/bin/activate
# python main.py