#!/usr/bin/env python3
"""
Relationship Processor for Batman Chatbot
Handles complex relationship queries using all database relationship tables
"""

import sqlite3
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

@dataclass
class RelationshipResult:
    """Result from relationship query."""
    query_type: str
    primary_entity: Dict[str, Any]
    related_data: List[Dict[str, Any]]
    explanation: str
    confidence: float

class RelationshipProcessor:
    """Processes complex relationship queries using all database tables."""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize the relationship processor."""
        self.conn = db_connection
        self.conn.row_factory = sqlite3.Row
    
    def _clean_entity_name(self, name: str) -> str:
        """Clean entity names for display (same as response generator)."""
        if not name:
            return "Unknown"
        
        import urllib.parse
        
        # 1. URL decode to fix %27 → ' issues
        cleaned = urllib.parse.unquote(name)
        
        # 2. Replace underscores with spaces
        cleaned = cleaned.replace('_', ' ')
        
        # 3. Remove parenthetical universe references for cleaner display
        import re
        cleaned = re.sub(r'\s*\([^)]*verse[^)]*\)$', '', cleaned)
        
        # 4. Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned.strip())
        
        return cleaned
        
    def process_weapons_query(self, entity_name: str) -> Optional[RelationshipResult]:
        """Process queries about weapons (What weapons does X have?)."""
        cursor = self.conn.cursor()
        
        # Find the entity first
        entity = self._find_entity(entity_name)
        if not entity:
            return None
        
        if entity['type'] == 'vehicles':
            # Get vehicle weapons
            cursor.execute("""
                SELECT vw.weapon, v.name as vehicle_name
                FROM vehicle_weapons vw 
                JOIN vehicles v ON vw.vehicle_id = v.id 
                WHERE v.id = ?
            """, (entity['id'],))
            
            weapons = cursor.fetchall()
            if weapons:
                weapon_list = [w['weapon'] for w in weapons]
                return RelationshipResult(
                    query_type='weapons',
                    primary_entity=entity,
                    related_data=[dict(w) for w in weapons],
                    explanation=f"{self._clean_entity_name(entity['name'])} is equipped with: {', '.join(weapon_list)}",
                    confidence=1.0
                )
            else:
                # Return helpful response even when no weapons found
                return RelationshipResult(
                    query_type='weapons',
                    primary_entity=entity,
                    related_data=[],
                    explanation=f"No specific weapon data is available for {self._clean_entity_name(entity['name'])} in the current database. The {self._clean_entity_name(entity['name'])} may have weapons not yet catalogued.",
                    confidence=0.6
                )
        
        # Check for character weapons in descriptions
        elif entity['type'] == 'characters':
            # Look for weapon mentions in character description
            description = entity.get('description', '').lower()
            weapon_keywords = ['gun', 'pistol', 'rifle', 'sword', 'knife', 'weapon', 'armed', 'carries']
            found_weapons = [kw for kw in weapon_keywords if kw in description]
            
            if found_weapons:
                return RelationshipResult(
                    query_type='character_weapons',
                    primary_entity=entity,
                    related_data=[],
                    explanation=f"Based on available information, {self._clean_entity_name(entity['name'])} appears to be associated with weapons: {', '.join(found_weapons)}",
                    confidence=0.7
                )
        
        return None
    
    def process_defense_query(self, entity_name: str) -> Optional[RelationshipResult]:
        """Process queries about defensive systems."""
        cursor = self.conn.cursor()
        
        entity = self._find_entity(entity_name)
        if not entity:
            return None
        
        if entity['type'] == 'vehicles':
            # Get vehicle defensive systems
            cursor.execute("""
                SELECT vds.defensive_system, v.name as vehicle_name
                FROM vehicle_defensive_systems vds 
                JOIN vehicles v ON vds.vehicle_id = v.id 
                WHERE v.id = ?
            """, (entity['id'],))
            
            defenses = cursor.fetchall()
            if defenses:
                defense_list = [d['defensive_system'] for d in defenses]
                return RelationshipResult(
                    query_type='defenses',
                    primary_entity=entity,
                    related_data=[dict(d) for d in defenses],
                    explanation=f"{self._clean_entity_name(entity['name'])} has defensive systems: {', '.join(defense_list)}",
                    confidence=1.0
                )
            else:
                return RelationshipResult(
                    query_type='defenses',
                    primary_entity=entity,
                    related_data=[],
                    explanation=f"No specific defensive system data is available for {self._clean_entity_name(entity['name'])} in the current database. The {self._clean_entity_name(entity['name'])} may have defenses not yet catalogued.",
                    confidence=0.6
                )
        
        elif entity['type'] == 'locations':
            # Check for location defenses (table doesn't exist yet, but provide helpful response)
            return RelationshipResult(
                query_type='defenses',
                primary_entity=entity,
                related_data=[],
                explanation=f"Defense information for {self._clean_entity_name(entity['name'])} is not yet available in the current database. As a Batman location, it likely has sophisticated security systems.",
                confidence=0.5
            )
        
        return None
    
    def process_features_query(self, entity_name: str) -> Optional[RelationshipResult]:
        """Process queries about special features."""
        cursor = self.conn.cursor()
        
        entity = self._find_entity(entity_name)
        if not entity:
            return None
        
        if entity['type'] == 'vehicles':
            # Get vehicle special features
            cursor.execute("""
                SELECT vsf.special_feature, v.name as vehicle_name
                FROM vehicle_special_features vsf 
                JOIN vehicles v ON vsf.vehicle_id = v.id 
                WHERE v.id = ?
            """, (entity['id'],))
            
            features = cursor.fetchall()
            if features:
                feature_list = [f['special_feature'] for f in features]
                return RelationshipResult(
                    query_type='features',
                    primary_entity=entity,
                    related_data=[dict(f) for f in features],
                    explanation=f"{self._clean_entity_name(entity['name'])} has special features: {', '.join(feature_list)}",
                    confidence=1.0
                )
            else:
                return RelationshipResult(
                    query_type='features',
                    primary_entity=entity,
                    related_data=[],
                    explanation=f"No specific feature data is available for {self._clean_entity_name(entity['name'])} in the current database. The {self._clean_entity_name(entity['name'])} may have special capabilities not yet catalogued.",
                    confidence=0.6
                )
        
        elif entity['type'] == 'locations':
            # Check for location features (table doesn't exist yet, but provide helpful response)
            return RelationshipResult(
                query_type='features',
                primary_entity=entity,
                related_data=[],
                explanation=f"Feature information for {self._clean_entity_name(entity['name'])} is not yet available in the current database. As a Batman location, it likely has advanced technological features.",
                confidence=0.5
            )
        
        return None
    
    def process_location_query(self, entity_name: str) -> Optional[RelationshipResult]:
        """Process queries about where entities are located."""
        cursor = self.conn.cursor()
        
        entity = self._find_entity(entity_name)
        if not entity:
            return None
        
        if entity['type'] == 'characters':
            # Get character locations
            cursor.execute("""
                SELECT l.*, cl.association_type
                FROM character_locations cl
                JOIN locations l ON cl.location_id = l.id
                WHERE cl.character_id = ?
                ORDER BY l.name
            """, (entity['id'],))
            
            locations = cursor.fetchall()
            if locations:
                location_names = [l['name'].replace('_', ' ') for l in locations]
                primary_location = locations[0]  # Use first as primary
                
                return RelationshipResult(
                    query_type='character_locations',
                    primary_entity=entity,
                    related_data=[dict(l) for l in locations],
                    explanation=f"{entity['name']} is associated with these locations: {', '.join(location_names[:5])}{'...' if len(location_names) > 5 else ''}. Primary location: {primary_location['name'].replace('_', ' ')} - {primary_location['description'][:200]}...",
                    confidence=1.0
                )
        
        return None
    
    def process_specifications_query(self, entity_name: str) -> Optional[RelationshipResult]:
        """Process queries about vehicle specifications."""
        cursor = self.conn.cursor()
        
        entity = self._find_entity(entity_name)
        if not entity or entity['type'] != 'vehicles':
            return None
        
        # Get vehicle specifications
        cursor.execute("""
            SELECT * FROM vehicle_specifications 
            WHERE vehicle_id = ?
        """, (entity['id'],))
        
        specs = cursor.fetchone()
        if specs:
            spec_details = []
            spec_dict = dict(specs)
            
            for key, value in spec_dict.items():
                if key != 'vehicle_id' and value and value.strip():
                    spec_details.append(f"{key.replace('_', ' ')}: {value}")
            
            if spec_details:
                return RelationshipResult(
                    query_type='specifications',
                    primary_entity=entity,
                    related_data=[spec_dict],
                    explanation=f"{entity['name']} specifications: {'; '.join(spec_details)}",
                    confidence=1.0
                )
        
        return None
    
    def process_relationship_query(self, query: str) -> Optional[RelationshipResult]:
        """Process general relationship queries based on patterns."""
        
        # Weapons queries (ordered from most specific to least specific)
        weapons_patterns = [
            r'what weapons does (?:the )?(.+?) have',
            r'what guns does (?:the )?(.+?) have',
            r'what arms does (?:the )?(.+?) have',
            r'what weapons are on (?:the )?(.+)',
            r'what weapons are (?:in|inside|aboard) (?:the )?(.+)',
            r'what are (?:the )?(.+?) weapons',
            r'what is (?:the )?(.+?) armed with',
            r'does (?:the )?(.+?) have weapons',
            r'weapons of (?:the )?(.+)',
            r'weapons on (?:the )?(.+)',
            r'the (.+?) weapons',
            r'(.+?) weapons'  # Most generic pattern last
        ]
        
        for pattern in weapons_patterns:
            match = re.search(pattern, query.lower())
            if match:
                entity_name = match.group(1).strip()
                return self.process_weapons_query(entity_name)
        
        # Defense queries
        defense_patterns = [
            r'what (?:defenses|defense|armor|protection) does (?:the )?(.+?) have',
            r'what (?:defensive systems|defenses) does (?:the )?(.+?) have',
            r'what (?:defenses|defense|armor|protection) are on (?:the )?(.+)',
            r'what (?:defenses|defense|armor|protection) are (?:in|inside) (?:the )?(.+)',
            r'(.+?) (?:defenses|defense|armor|protection)',
            r'(?:defenses|defense|armor|protection) of (?:the )?(.+)',
            r'(?:defenses|defense|armor|protection) on (?:the )?(.+)',
            r'how is (?:the )?(.+?) (?:protected|defended|armored)',
            r'does (?:the )?(.+?) have (?:defenses|armor|protection)'
        ]
        
        for pattern in defense_patterns:
            match = re.search(pattern, query.lower())
            if match:
                entity_name = match.group(1).strip()
                return self.process_defense_query(entity_name)
        
        # Features queries
        features_patterns = [
            r'what (?:features|abilities|systems|capabilities) does (?:the )?(.+?) have',
            r'what (?:special features|features) does (?:the )?(.+?) have',
            r'what (?:features|abilities|systems|capabilities) are on (?:the )?(.+)',
            r'what (?:features|abilities|systems|capabilities) are (?:in|inside) (?:the )?(.+)',
            r'(.+?) (?:features|abilities|systems|capabilities)',
            r'(?:features|abilities|systems) of (?:the )?(.+)',
            r'(?:features|abilities|systems) on (?:the )?(.+)',
            r'what can (?:the )?(.+?) do',
            r'does (?:the )?(.+?) have (?:features|abilities|systems)'
        ]
        
        for pattern in features_patterns:
            match = re.search(pattern, query.lower())
            if match:
                entity_name = match.group(1).strip()
                return self.process_features_query(entity_name)
        
        # Specifications queries
        spec_patterns = [
            r'(?:specs|specifications|details) (?:of|for) (.+?)',
            r'(.+?) (?:specs|specifications|technical details)',
            r'what (?:are|is) (.+?) (?:specs|specifications)'
        ]
        
        for pattern in spec_patterns:
            match = re.search(pattern, query.lower())
            if match:
                entity_name = match.group(1).strip()
                return self.process_specifications_query(entity_name)
        
        # Location queries
        location_patterns = [
            r'where (?:does|do|is|are) (.+?) (?:live|stay|operate|hang out|work)',
            r'(?:location|locations) (?:of|for) (.+?)',
            r'(.+?) (?:location|base|hideout|lair)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, query.lower())
            if match:
                entity_name = match.group(1).strip()
                return self.process_location_query(entity_name)
        
        return None
    
    def _find_entity(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """Find an entity across all tables."""
        cursor = self.conn.cursor()
        
        # Clean entity name for searching
        clean_name = entity_name.strip().replace(' ', '_').title()
        
        tables = ['characters', 'vehicles', 'locations', 'organizations', 'storylines']
        
        for table in tables:
            # Try exact match first
            cursor.execute(f"SELECT *, '{table}' as type FROM {table} WHERE name = ?", (clean_name,))
            result = cursor.fetchone()
            if result:
                return dict(result)
            
            # Try fuzzy match
            cursor.execute(f"SELECT *, '{table}' as type FROM {table} WHERE name LIKE ?", (f"%{clean_name}%",))
            result = cursor.fetchone()
            if result:
                return dict(result)
        
        return None