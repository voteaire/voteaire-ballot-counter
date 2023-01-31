#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- SETUP SQL HERE
    -- CREATE TABLES ETC
    CREATE DATABASE voteaire;
    CREATE DATABASE snapshotter;
EOSQL
