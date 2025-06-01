#!/usr/bin/env python3
"""
Batman Database Importer
Phase 1.2: Import JSON data into SQLite database

Imports the consolidated JSON data (1,056 entities) into the relational SQLite database.
"""

import json
import sqlite3
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

class BatmanDatabaseImporter:
    def __init__(self, db_path: str = "batman_universe.db"):
        """Initialize the database importer."""
        self.db_path = db_path
        self.conn = None
        self.stats = {
            'characters': 0,
            'vehicles': 0,
            'locations': 0,
            'storylines': 0,
            'organizations': 0,
            'relationships': 0,
            'errors': []
        }
        
    def connect_database(self):
        """Connect to SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.execute("PRAGMA foreign_keys = ON")
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def create_schema(self):
        """Create database schema from schema file."""
        try:
            schema_path = os.path.join(os.path.dirname(__file__), 'batman_schema.sql')
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema creation
            self.conn.executescript(schema_sql)
            self.conn.commit()
            print("✅ Database schema created successfully")
            return True
        except Exception as e:
            print(f"❌ Schema creation failed: {e}")
            self.stats['errors'].append(f"Schema creation: {e}")
            return False
    
    def load_master_data(self) -> Dict:
        """Load the master database JSON file."""
        try:
            master_path = "../data_processor/master_database/batman_master_database.json"
            with open(master_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ Loaded master database: {data['metadata']['total_entities']} entities")
            return data
        except Exception as e:
            print(f"❌ Failed to load master database: {e}")
            self.stats['errors'].append(f"Master data load: {e}")
            return {}
    
    def import_characters(self, characters: List[Dict]):
        """Import characters into database."""
        try:
            cursor = self.conn.cursor()
            
            for char in characters:
                # Insert main character record
                cursor.execute("""
                    INSERT INTO characters (id, name, url, description, first_appearance, source_file)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    char['id'],
                    char['name'],
                    char.get('url', ''),
                    char.get('description', ''),
                    char.get('first_appearance', ''),
                    char.get('source_file', '')
                ))
                
                # Insert aliases
                for alias in char.get('aliases', []):
                    if alias:  # Skip empty aliases
                        cursor.execute("""
                            INSERT OR IGNORE INTO character_aliases (character_id, alias)
                            VALUES (?, ?)
                        """, (char['id'], alias))
                
                # Insert powers and abilities
                for power in char.get('powers_abilities', []):
                    if power:  # Skip empty powers
                        cursor.execute("""
                            INSERT OR IGNORE INTO character_powers (character_id, power_ability)
                            VALUES (?, ?)
                        """, (char['id'], power))
                
                self.stats['characters'] += 1
            
            self.conn.commit()
            print(f"✅ Imported {len(characters)} characters")
            
        except Exception as e:
            print(f"❌ Character import failed: {e}")
            self.stats['errors'].append(f"Character import: {e}")
    
    def import_vehicles(self, vehicles: List[Dict]):
        """Import vehicles into database."""
        try:
            cursor = self.conn.cursor()
            
            for vehicle in vehicles:
                # Insert main vehicle record
                cursor.execute("""
                    INSERT INTO vehicles (id, name, url, description, vehicle_type, source_file)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    vehicle['id'],
                    vehicle['name'],
                    vehicle.get('url', ''),
                    vehicle.get('description', ''),
                    vehicle.get('vehicle_type', ''),
                    vehicle.get('source_file', '')
                ))
                
                # Insert vehicle specifications
                specs = vehicle.get('specifications', {})
                cursor.execute("""
                    INSERT INTO vehicle_specifications 
                    (vehicle_id, length, width, height, weight, max_speed, engine, armor, 
                     crew_capacity, manufacturer, first_appearance)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    vehicle['id'],
                    specs.get('length', ''),
                    specs.get('width', ''),
                    specs.get('height', ''),
                    specs.get('weight', ''),
                    specs.get('max_speed', ''),
                    specs.get('engine', ''),
                    specs.get('armor', ''),
                    specs.get('crew_capacity', ''),
                    specs.get('manufacturer', ''),
                    specs.get('first_appearance', '')
                ))
                
                # Insert vehicle attributes
                for weapon in specs.get('weapons', []):
                    if weapon:
                        cursor.execute("""
                            INSERT OR IGNORE INTO vehicle_weapons (vehicle_id, weapon)
                            VALUES (?, ?)
                        """, (vehicle['id'], weapon))
                
                for defense in specs.get('defensive_systems', []):
                    if defense:
                        cursor.execute("""
                            INSERT OR IGNORE INTO vehicle_defensive_systems (vehicle_id, defensive_system)
                            VALUES (?, ?)
                        """, (vehicle['id'], defense))
                
                for feature in specs.get('special_features', []):
                    if feature:
                        cursor.execute("""
                            INSERT OR IGNORE INTO vehicle_special_features (vehicle_id, special_feature)
                            VALUES (?, ?)
                        """, (vehicle['id'], feature))
                
                for alias in vehicle.get('aliases', []):
                    if alias:
                        cursor.execute("""
                            INSERT OR IGNORE INTO vehicle_aliases (vehicle_id, alias)
                            VALUES (?, ?)
                        """, (vehicle['id'], alias))
                
                self.stats['vehicles'] += 1
            
            self.conn.commit()
            print(f"✅ Imported {len(vehicles)} vehicles")
            
        except Exception as e:
            print(f"❌ Vehicle import failed: {e}")
            self.stats['errors'].append(f"Vehicle import: {e}")
    
    def import_locations(self, locations: List[Dict]):
        """Import locations into database."""
        try:
            cursor = self.conn.cursor()
            
            for location in locations:
                cursor.execute("""
                    INSERT INTO locations (id, name, url, description, location_type, source_file)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    location['id'],
                    location['name'],
                    location.get('url', ''),
                    location.get('description', ''),
                    location.get('location_type', ''),
                    location.get('source_file', '')
                ))
                
                self.stats['locations'] += 1
            
            self.conn.commit()
            print(f"✅ Imported {len(locations)} locations")
            
        except Exception as e:
            print(f"❌ Location import failed: {e}")
            self.stats['errors'].append(f"Location import: {e}")
    
    def import_storylines(self, storylines: List[Dict]):
        """Import storylines into database."""
        try:
            cursor = self.conn.cursor()
            
            for storyline in storylines:
                cursor.execute("""
                    INSERT INTO storylines (id, name, url, description, complexity_level, 
                                         simplified_summary, source_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    storyline['id'],
                    storyline['name'],
                    storyline.get('url', ''),
                    storyline.get('description', ''),
                    storyline.get('complexity_level', 1),
                    storyline.get('simplified_summary', ''),
                    storyline.get('source_file', '')
                ))
                
                self.stats['storylines'] += 1
            
            self.conn.commit()
            print(f"✅ Imported {len(storylines)} storylines")
            
        except Exception as e:
            print(f"❌ Storyline import failed: {e}")
            self.stats['errors'].append(f"Storyline import: {e}")
    
    def import_organizations(self, organizations: List[Dict]):
        """Import organizations into database."""
        try:
            cursor = self.conn.cursor()
            
            for org in organizations:
                cursor.execute("""
                    INSERT INTO organizations (id, name, url, description, organization_type, 
                                            alignment, source_file)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    org['id'],
                    org['name'],
                    org.get('url', ''),
                    org.get('description', ''),
                    org.get('organization_type', ''),
                    org.get('alignment', ''),
                    org.get('source_file', '')
                ))
                
                self.stats['organizations'] += 1
            
            self.conn.commit()
            print(f"✅ Imported {len(organizations)} organizations")
            
        except Exception as e:
            print(f"❌ Organization import failed: {e}")
            self.stats['errors'].append(f"Organization import: {e}")
    
    def import_cross_references(self):
        """Import cross-reference relationships."""
        try:
            # Load cross-references file
            cross_ref_path = "../data_processor/master_database/batman_cross_references.json"
            with open(cross_ref_path, 'r', encoding='utf-8') as f:
                cross_refs = json.load(f)
            
            cursor = self.conn.cursor()
            
            # Import character-location relationships
            for char_id, location_ids in cross_refs.get('character_to_locations', {}).items():
                for loc_id in location_ids:
                    cursor.execute("""
                        INSERT OR IGNORE INTO character_locations (character_id, location_id)
                        VALUES (?, ?)
                    """, (char_id, loc_id))
                    self.stats['relationships'] += 1
            
            self.conn.commit()
            print(f"✅ Imported {self.stats['relationships']} cross-reference relationships")
            
        except Exception as e:
            print(f"❌ Cross-reference import failed: {e}")
            self.stats['errors'].append(f"Cross-reference import: {e}")
    
    def update_metadata(self):
        """Update database metadata with import statistics."""
        try:
            cursor = self.conn.cursor()
            
            # Update metadata
            cursor.execute("""
                UPDATE database_metadata SET value = ?, updated_at = datetime('now') 
                WHERE key = 'last_import'
            """, (datetime.now().isoformat(),))
            
            cursor.execute("""
                UPDATE database_metadata SET value = ?, updated_at = datetime('now') 
                WHERE key = 'total_entities'
            """, (str(sum([self.stats['characters'], self.stats['vehicles'], 
                          self.stats['locations'], self.stats['storylines'], 
                          self.stats['organizations']])),))
            
            self.conn.commit()
            print("✅ Database metadata updated")
            
        except Exception as e:
            print(f"❌ Metadata update failed: {e}")
            self.stats['errors'].append(f"Metadata update: {e}")
    
    def run_import(self):
        """Execute the complete import process."""
        print("🦇 Batman Database Import Starting...")
        print("=" * 50)
        
        # Connect and setup
        if not self.connect_database():
            return False
        
        if not self.create_schema():
            return False
        
        # Load master data
        master_data = self.load_master_data()
        if not master_data:
            return False
        
        # Import all entity types
        data = master_data.get('data', {})
        
        print("\n📊 Importing entities...")
        self.import_characters(data.get('characters', []))
        self.import_vehicles(data.get('vehicles', []))
        self.import_locations(data.get('locations', []))
        self.import_storylines(data.get('storylines', []))
        self.import_organizations(data.get('organizations', []))
        
        print("\n🔗 Importing relationships...")
        self.import_cross_references()
        
        print("\n📝 Updating metadata...")
        self.update_metadata()
        
        # Print final statistics
        print("\n" + "=" * 50)
        print("🎯 IMPORT COMPLETE!")
        print(f"Characters: {self.stats['characters']}")
        print(f"Vehicles: {self.stats['vehicles']}")
        print(f"Locations: {self.stats['locations']}")
        print(f"Storylines: {self.stats['storylines']}")
        print(f"Organizations: {self.stats['organizations']}")
        print(f"Relationships: {self.stats['relationships']}")
        print(f"Total Entities: {sum([self.stats['characters'], self.stats['vehicles'], self.stats['locations'], self.stats['storylines'], self.stats['organizations']])}")
        
        if self.stats['errors']:
            print(f"\n⚠️ Errors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"  - {error}")
        else:
            print("\n✅ No errors encountered!")
        
        return True
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

def main():
    """Main execution function."""
    importer = BatmanDatabaseImporter()
    
    try:
        success = importer.run_import()
        if success:
            print("\n🦇 Batman database ready for chatbot queries!")
            return 0
        else:
            print("\n❌ Import failed. Check errors above.")
            return 1
    finally:
        importer.close()

if __name__ == "__main__":
    sys.exit(main())