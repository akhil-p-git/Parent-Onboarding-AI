-- Initialize Triggers API Database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schema for better organization
CREATE SCHEMA IF NOT EXISTS triggers;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA triggers TO postgres;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'Triggers API database initialized successfully';
END $$;
