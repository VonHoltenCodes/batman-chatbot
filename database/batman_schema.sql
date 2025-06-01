-- Batman Universe Database Schema (SQLite)
-- Phase 1.2: Relational Database Structure Design
-- Created: 2025-06-01
-- Purpose: Support 1,056 Batman universe entities for chatbot queries

-- Enable foreign key constraints
PRAGMA foreign_keys = ON;

-- ========================================
-- CORE ENTITY TABLES
-- ========================================

-- Characters table (685 entities)
CREATE TABLE characters (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT UNIQUE,
    description TEXT,
    first_appearance TEXT,
    source_file TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Vehicles table (120 entities)
CREATE TABLE vehicles (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT UNIQUE,
    description TEXT,
    vehicle_type TEXT,
    source_file TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Vehicle specifications (1-to-1 with vehicles)
CREATE TABLE vehicle_specifications (
    vehicle_id TEXT PRIMARY KEY,
    length TEXT,
    width TEXT,
    height TEXT,
    weight TEXT,
    max_speed TEXT,
    engine TEXT,
    armor TEXT,
    crew_capacity TEXT,
    manufacturer TEXT,
    first_appearance TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

-- Locations table (112 entities)
CREATE TABLE locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT UNIQUE,
    description TEXT,
    location_type TEXT,
    source_file TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Storylines table (13 entities)
CREATE TABLE storylines (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT UNIQUE,
    description TEXT,
    complexity_level INTEGER DEFAULT 1,
    simplified_summary TEXT,
    source_file TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Organizations table (126 entities)
CREATE TABLE organizations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT UNIQUE,
    description TEXT,
    organization_type TEXT,
    alignment TEXT, -- good, evil, neutral
    source_file TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ========================================
-- ATTRIBUTE TABLES (Many-to-Many)
-- ========================================

-- Character aliases
CREATE TABLE character_aliases (
    character_id TEXT,
    alias TEXT,
    PRIMARY KEY (character_id, alias),
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- Character powers and abilities
CREATE TABLE character_powers (
    character_id TEXT,
    power_ability TEXT,
    PRIMARY KEY (character_id, power_ability),
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- Vehicle weapons
CREATE TABLE vehicle_weapons (
    vehicle_id TEXT,
    weapon TEXT,
    PRIMARY KEY (vehicle_id, weapon),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

-- Vehicle defensive systems
CREATE TABLE vehicle_defensive_systems (
    vehicle_id TEXT,
    defensive_system TEXT,
    PRIMARY KEY (vehicle_id, defensive_system),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

-- Vehicle special features
CREATE TABLE vehicle_special_features (
    vehicle_id TEXT,
    special_feature TEXT,
    PRIMARY KEY (vehicle_id, special_feature),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

-- Vehicle aliases
CREATE TABLE vehicle_aliases (
    vehicle_id TEXT,
    alias TEXT,
    PRIMARY KEY (vehicle_id, alias),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE
);

-- Vehicle users (who operates the vehicle)
CREATE TABLE vehicle_users (
    vehicle_id TEXT,
    character_id TEXT,
    PRIMARY KEY (vehicle_id, character_id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- ========================================
-- RELATIONSHIP TABLES
-- ========================================

-- Character relationships (allies, enemies, family, etc.)
CREATE TABLE character_relationships (
    character_id TEXT,
    related_character_id TEXT,
    relationship_type TEXT, -- ally, enemy, family, mentor, sidekick, etc.
    PRIMARY KEY (character_id, related_character_id),
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (related_character_id) REFERENCES characters(id) ON DELETE CASCADE
);

-- Character to Location associations
CREATE TABLE character_locations (
    character_id TEXT,
    location_id TEXT,
    association_type TEXT DEFAULT 'associated', -- lives, works, frequent, hideout, etc.
    PRIMARY KEY (character_id, location_id),
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(id) ON DELETE CASCADE
);

-- Character to Organization memberships
CREATE TABLE character_organizations (
    character_id TEXT,
    organization_id TEXT,
    role TEXT, -- leader, member, founder, etc.
    status TEXT DEFAULT 'active', -- active, former, etc.
    PRIMARY KEY (character_id, organization_id),
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

-- Character to Storyline appearances
CREATE TABLE character_storylines (
    character_id TEXT,
    storyline_id TEXT,
    role TEXT, -- protagonist, antagonist, supporting, etc.
    PRIMARY KEY (character_id, storyline_id),
    FOREIGN KEY (character_id) REFERENCES characters(id) ON DELETE CASCADE,
    FOREIGN KEY (storyline_id) REFERENCES storylines(id) ON DELETE CASCADE
);

-- ========================================
-- FULL-TEXT SEARCH VIRTUAL TABLES
-- ========================================

-- Full-text search for characters
CREATE VIRTUAL TABLE characters_fts USING fts5(
    id UNINDEXED,
    name,
    description,
    aliases,
    powers_abilities,
    content='characters'
);

-- Full-text search for vehicles  
CREATE VIRTUAL TABLE vehicles_fts USING fts5(
    id UNINDEXED,
    name,
    description,
    vehicle_type,
    aliases,
    content='vehicles'
);

-- Full-text search for locations
CREATE VIRTUAL TABLE locations_fts USING fts5(
    id UNINDEXED,
    name,
    description,
    location_type,
    content='locations'
);

-- Full-text search for storylines
CREATE VIRTUAL TABLE storylines_fts USING fts5(
    id UNINDEXED,
    name,
    description,
    simplified_summary,
    content='storylines'
);

-- Full-text search for organizations
CREATE VIRTUAL TABLE organizations_fts USING fts5(
    id UNINDEXED,
    name,
    description,
    organization_type,
    content='organizations'
);

-- ========================================
-- INDEXES FOR PERFORMANCE
-- ========================================

-- Character indexes
CREATE INDEX idx_characters_name ON characters(name);
CREATE INDEX idx_characters_source ON characters(source_file);

-- Vehicle indexes
CREATE INDEX idx_vehicles_name ON vehicles(name);
CREATE INDEX idx_vehicles_type ON vehicles(vehicle_type);

-- Location indexes
CREATE INDEX idx_locations_name ON locations(name);
CREATE INDEX idx_locations_type ON locations(location_type);

-- Organization indexes
CREATE INDEX idx_organizations_name ON organizations(name);
CREATE INDEX idx_organizations_type ON organizations(organization_type);
CREATE INDEX idx_organizations_alignment ON organizations(alignment);

-- Relationship indexes
CREATE INDEX idx_char_relationships_from ON character_relationships(character_id);
CREATE INDEX idx_char_relationships_to ON character_relationships(related_character_id);
CREATE INDEX idx_char_locations ON character_locations(character_id);
CREATE INDEX idx_char_orgs ON character_organizations(character_id);
CREATE INDEX idx_char_storylines ON character_storylines(character_id);

-- ========================================
-- TRIGGERS FOR MAINTAINING FTS
-- ========================================

-- Triggers to keep FTS tables synchronized with main tables
CREATE TRIGGER characters_fts_insert AFTER INSERT ON characters BEGIN
    INSERT INTO characters_fts(id, name, description) VALUES (new.id, new.name, new.description);
END;

CREATE TRIGGER characters_fts_update AFTER UPDATE ON characters BEGIN
    UPDATE characters_fts SET name = new.name, description = new.description WHERE id = new.id;
END;

CREATE TRIGGER characters_fts_delete AFTER DELETE ON characters BEGIN
    DELETE FROM characters_fts WHERE id = old.id;
END;

-- Similar triggers for other entities
CREATE TRIGGER vehicles_fts_insert AFTER INSERT ON vehicles BEGIN
    INSERT INTO vehicles_fts(id, name, description, vehicle_type) VALUES (new.id, new.name, new.description, new.vehicle_type);
END;

CREATE TRIGGER vehicles_fts_update AFTER UPDATE ON vehicles BEGIN
    UPDATE vehicles_fts SET name = new.name, description = new.description, vehicle_type = new.vehicle_type WHERE id = new.id;
END;

CREATE TRIGGER vehicles_fts_delete AFTER DELETE ON vehicles BEGIN
    DELETE FROM vehicles_fts WHERE id = old.id;
END;

-- Database metadata for tracking import status
CREATE TABLE database_metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Initial metadata
INSERT INTO database_metadata (key, value) VALUES 
('version', '1.0'),
('schema_created', datetime('now')),
('total_entities', '1056'),
('last_import', ''),
('description', 'Comprehensive Batman Universe Database - 1,056 entities');