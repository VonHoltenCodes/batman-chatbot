#!/usr/bin/env python3
"""
Intelligent Search Engine for Batman Chatbot
Creates a comprehensive search system that uses all database capabilities
"""

import sqlite3
import re
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass
from fuzzywuzzy import fuzz

@dataclass
class SearchResult:
    """Comprehensive search result with context."""
    entity_id: str
    entity_type: str
    name: str
    description: str
    confidence: float
    match_type: str
    related_entities: List[Dict] = None
    context: str = ""

class IntelligentSearchEngine:
    """Advanced search engine that uses full database capabilities."""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize the intelligent search engine."""
        self.conn = db_connection
        self.conn.row_factory = sqlite3.Row
        
    def search_multi_entity(self, query: str) -> Dict[str, Any]:
        """Search for multiple entities in a single query (e.g., 'compare A to B')."""
        
        # Extract comparison patterns
        comparison_patterns = [
            r'compare (.+?) (?:to|with|and) (.+?)(?:\?|$)',
            r'(.+?) (?:vs|versus) (.+?)(?:\?|$)',
            r'difference between (.+?) and (.+?)(?:\?|$)',
            r'(.+?) or (.+?)(?:\?|$)'
        ]
        
        for pattern in comparison_patterns:
            match = re.search(pattern, query.lower())
            if match:
                entity1_query = match.group(1).strip()
                entity2_query = match.group(2).strip()
                
                # Search for both entities
                entity1 = self.search_single_entity(entity1_query)
                entity2 = self.search_single_entity(entity2_query)
                
                if entity1 and entity2:
                    return {
                        'type': 'comparison',
                        'entity1': entity1,
                        'entity2': entity2,
                        'comparison_data': self._get_comparison_data(entity1, entity2)
                    }
        
        return {'type': 'single'}
    
    def search_single_entity(self, query: str) -> Optional[SearchResult]:
        """Search for a single entity using all available methods."""
        
        # Try different search approaches in order of precision
        
        # 1. Exact name match
        result = self._exact_name_search(query)
        if result and result.confidence > 0.9:
            return result
        
        # 2. Full-text search
        fts_result = self._full_text_search(query)
        if fts_result and fts_result.confidence > 0.8:
            return fts_result
        
        # 3. Fuzzy name matching
        fuzzy_result = self._fuzzy_name_search(query)
        if fuzzy_result and fuzzy_result.confidence > 0.7:
            return fuzzy_result
        
        # 4. Description search
        desc_result = self._description_search(query)
        if desc_result:
            return desc_result
        
        return result or fts_result or fuzzy_result or desc_result
    
    def search_by_relationship(self, query: str) -> Optional[SearchResult]:
        """Search for entities based on relationships (where does X park, who uses Y)."""
        
        # Location-based queries
        location_patterns = [
            r'where (?:does|do|is) (.+?) (?:park|live|stay|located|based|reside)(?:\?|$)',
            r'(?:where|location) (?:of|for) (.+?)(?:\?|$)',
            r'(.+?) (?:location|base|home|residence)(?:\?|$)',
            r'where (?:does|do) (.+?) (?:hang out|hide|operate)(?:\?|$)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, query.lower())
            if match:
                entity_name = match.group(1).strip()
                return self._find_entity_location(entity_name)
        
        # Usage-based queries
        usage_patterns = [
            r'who (?:uses|drives|operates|pilots) (.+?)(?:\?|$)',
            r'(.+?) (?:user|driver|pilot|operator)(?:\?|$)'
        ]
        
        for pattern in usage_patterns:
            match = re.search(pattern, query.lower())
            if match:
                entity_name = match.group(1).strip()
                return self._find_entity_users(entity_name)
        
        return None
    
    def _exact_name_search(self, query: str) -> Optional[SearchResult]:
        """Search for exact name matches across all tables."""
        cursor = self.conn.cursor()
        
        # Clean query for exact matching
        clean_query = query.replace(' ', '_').title()
        
        tables = ['characters', 'vehicles', 'locations', 'storylines', 'organizations']
        
        for table in tables:
            # First try exact match
            cursor.execute(f"SELECT * FROM {table} WHERE name = ?", (clean_query,))
            result = cursor.fetchone()
            
            if result:
                return SearchResult(
                    entity_id=result['id'],
                    entity_type=table,
                    name=result['name'],
                    description=result['description'] or '',
                    confidence=1.0,
                    match_type='exact'
                )
            
            # Then try exact word match (not substring)
            cursor.execute(f"SELECT * FROM {table} WHERE name = ? OR name = ?", 
                         (query.title(), query.upper()))
            result = cursor.fetchone()
            
            if result:
                return SearchResult(
                    entity_id=result['id'],
                    entity_type=table,
                    name=result['name'],
                    description=result['description'] or '',
                    confidence=1.0,
                    match_type='exact'
                )
        
        return None
    
    def _full_text_search(self, query: str) -> Optional[SearchResult]:
        """Use FTS5 full-text search capabilities."""
        cursor = self.conn.cursor()
        
        # Search each FTS table
        fts_tables = [
            ('characters_fts', 'characters'),
            ('vehicles_fts', 'vehicles'), 
            ('locations_fts', 'locations'),
            ('storylines_fts', 'storylines'),
            ('organizations_fts', 'organizations')
        ]
        
        best_result = None
        best_score = 0
        
        for fts_table, base_table in fts_tables:
            try:
                # Use FTS5 MATCH for intelligent full-text search
                cursor.execute(f"""
                    SELECT {base_table}.*, rank 
                    FROM {fts_table} 
                    JOIN {base_table} ON {fts_table}.rowid = {base_table}.rowid 
                    WHERE {fts_table} MATCH ? 
                    ORDER BY rank 
                    LIMIT 1
                """, (query,))
                
                result = cursor.fetchone()
                if result:
                    # Calculate confidence based on FTS rank (lower rank = better match)
                    confidence = max(0.5, 1.0 - (result['rank'] / 10.0))
                    
                    if confidence > best_score:
                        best_result = SearchResult(
                            entity_id=result['id'],
                            entity_type=base_table,
                            name=result['name'],
                            description=result['description'] or '',
                            confidence=confidence,
                            match_type='full_text'
                        )
                        best_score = confidence
            except sqlite3.OperationalError:
                # FTS table might not exist or query syntax error
                continue
        
        return best_result
    
    def _fuzzy_name_search(self, query: str) -> Optional[SearchResult]:
        """Fuzzy matching on entity names with importance ranking."""
        cursor = self.conn.cursor()
        
        tables = ['characters', 'vehicles', 'locations', 'storylines', 'organizations']
        candidates = []
        
        for table in tables:
            cursor.execute(f"SELECT id, name, description FROM {table}")
            
            for row in cursor.fetchall():
                # Calculate multiple fuzzy match scores
                name_clean = row['name'].replace('_', ' ')
                ratio_score = fuzz.ratio(query.lower(), name_clean.lower()) / 100.0
                partial_score = fuzz.partial_ratio(query.lower(), name_clean.lower()) / 100.0
                token_sort_score = fuzz.token_sort_ratio(query.lower(), name_clean.lower()) / 100.0
                
                # Use the best fuzzy matching method
                fuzzy_score = max(ratio_score, partial_score, token_sort_score)
                
                if fuzzy_score > 0.5:  # Lowered threshold from 0.6 to 0.5
                    # Calculate importance bonus for main characters
                    importance_bonus = self._calculate_importance_bonus(row['name'], table)
                    
                    # Combine fuzzy score with importance
                    final_score = fuzzy_score + importance_bonus
                    
                    candidates.append({
                        'result': SearchResult(
                            entity_id=row['id'],
                            entity_type=table,
                            name=row['name'],
                            description=row['description'] or '',
                            confidence=fuzzy_score,  # Keep original fuzzy score for confidence
                            match_type='fuzzy'
                        ),
                        'final_score': final_score,
                        'fuzzy_score': fuzzy_score,
                        'importance_bonus': importance_bonus
                    })
        
        # Return the candidate with the highest final score
        if candidates:
            best_candidate = max(candidates, key=lambda x: x['final_score'])
            return best_candidate['result']
        
        return None
    
    def _calculate_importance_bonus(self, entity_name: str, table: str) -> float:
        """Calculate importance bonus for main Batman universe entities."""
        name_lower = entity_name.lower()
        
        # Main characters get higher priority
        main_characters = [
            'batman', 'robin', 'joker', 'catwoman', 'penguin', 'riddler', 
            'two_face', 'harvey_dent', 'scarecrow', 'poison_ivy', 'mr_freeze',
            'bane', 'harley_quinn', 'ra_s_al_ghul', 'alfred', 'commissioner_gordon',
            'batgirl', 'nightwing', 'red_hood', 'red_robin'
        ]
        
        # Main locations get priority
        main_locations = [
            'gotham_city', 'arkham_asylum', 'wayne_manor', 'batcave', 
            'gcpd', 'ace_chemicals', 'blackgate_prison'
        ]
        
        # Main vehicles get priority  
        main_vehicles = ['batmobile', 'batplane', 'batwing', 'batboat']
        
        if table == 'characters' and any(main_char in name_lower for main_char in main_characters):
            return 0.2  # 20% bonus for main characters
        elif table == 'locations' and any(main_loc in name_lower for main_loc in main_locations):
            return 0.15  # 15% bonus for main locations
        elif table == 'vehicles' and any(main_veh in name_lower for main_veh in main_vehicles):
            return 0.15  # 15% bonus for main vehicles
        elif len(entity_name.replace('_', ' ').split()) <= 2:
            return 0.05  # Small bonus for shorter/simpler names
        
        return 0.0  # No bonus for minor characters
    
    def _description_search(self, query: str) -> Optional[SearchResult]:
        """Search within entity descriptions."""
        cursor = self.conn.cursor()
        
        tables = ['characters', 'vehicles', 'locations', 'storylines', 'organizations']
        
        for table in tables:
            cursor.execute(f"""
                SELECT id, name, description 
                FROM {table} 
                WHERE description LIKE ? 
                ORDER BY LENGTH(description) ASC
                LIMIT 1
            """, (f"%{query}%",))
            
            result = cursor.fetchone()
            if result:
                return SearchResult(
                    entity_id=result['id'],
                    entity_type=table,
                    name=result['name'],
                    description=result['description'] or '',
                    confidence=0.6,
                    match_type='description'
                )
        
        return None
    
    def _find_entity_location(self, entity_name: str) -> Optional[SearchResult]:
        """Find where an entity is located/parks/lives."""
        cursor = self.conn.cursor()
        
        # First find the entity
        entity = self.search_single_entity(entity_name)
        if not entity:
            return None
        
        # Look for location relationships
        cursor.execute("""
            SELECT l.*, cl.association_type
            FROM character_locations cl
            JOIN locations l ON cl.location_id = l.id
            WHERE cl.character_id = ?
        """, (entity.entity_id,))
        
        location = cursor.fetchone()
        if location:
            return SearchResult(
                entity_id=location['id'],
                entity_type='locations',
                name=location['name'],
                description=location['description'] or '',
                confidence=0.9,
                match_type='relationship',
                context=f"{entity.name} is {location['association_type']} with this location"
            )
        
        # For vehicles, check common parking locations
        if entity.entity_type == 'vehicles' and 'bat' in entity.name.lower():
            # Batcave is the likely location for Bat-vehicles
            cursor.execute("SELECT * FROM locations WHERE name LIKE '%Batcave%' OR name LIKE '%Bat%Cave%'")
            batcave = cursor.fetchone()
            if batcave:
                return SearchResult(
                    entity_id=batcave['id'],
                    entity_type='locations',
                    name=batcave['name'],
                    description=batcave['description'] or '',
                    confidence=0.8,
                    match_type='inference',
                    context=f"{entity.name} likely parks in the Batcave"
                )
        
        # For characters, check common character-location associations
        if entity.entity_type == 'characters':
            location_inferences = {
                'penguin': ['iceberg_lounge', 'arctic_world', 'old_zoo'],
                'joker': ['ace_chemical', 'amusement_mile'],
                'batman': ['batcave', 'wayne_manor'],
                'catwoman': ['museum', 'rooftop']
            }
            
            entity_name_clean = entity.name.lower().replace('_', ' ')
            for char_key, locations in location_inferences.items():
                if char_key in entity_name_clean:
                    # Try to find these locations in the database
                    for loc_name in locations:
                        cursor.execute("SELECT * FROM locations WHERE name LIKE ?", (f"%{loc_name}%",))
                        location = cursor.fetchone()
                        if location:
                            return SearchResult(
                                entity_id=location['id'],
                                entity_type='locations',
                                name=location['name'],
                                description=location['description'] or '',
                                confidence=0.8,
                                match_type='inference',
                                context=f"{entity.name} is associated with {location['name']}"
                            )
        
        return None
    
    def _find_entity_users(self, entity_name: str) -> Optional[SearchResult]:
        """Find who uses/drives/operates an entity."""
        cursor = self.conn.cursor()
        
        # First find the entity
        entity = self.search_single_entity(entity_name)
        if not entity:
            return None
        
        # Look for vehicle users
        if entity.entity_type == 'vehicles':
            cursor.execute("""
                SELECT c.*, vu.character_id
                FROM vehicle_users vu
                JOIN characters c ON vu.character_id = c.id
                WHERE vu.vehicle_id = ?
            """, (entity.entity_id,))
            
            user = cursor.fetchone()
            if user:
                return SearchResult(
                    entity_id=user['id'],
                    entity_type='characters',
                    name=user['name'],
                    description=user['description'] or '',
                    confidence=0.9,
                    match_type='relationship',
                    context=f"User of {entity.name}"
                )
            
            # Inference for Bat-vehicles
            if 'bat' in entity.name.lower():
                cursor.execute("SELECT * FROM characters WHERE name LIKE '%Batman%' LIMIT 1")
                batman = cursor.fetchone()
                if batman:
                    return SearchResult(
                        entity_id=batman['id'],
                        entity_type='characters',
                        name=batman['name'],
                        description=batman['description'] or '',
                        confidence=0.8,
                        match_type='inference',
                        context=f"Batman likely uses {entity.name}"
                    )
        
        return None
    
    def _get_comparison_data(self, entity1: SearchResult, entity2: SearchResult) -> Dict[str, Any]:
        """Get detailed comparison data for two entities."""
        cursor = self.conn.cursor()
        
        comparison = {
            'entity1_details': self._get_entity_details(entity1),
            'entity2_details': self._get_entity_details(entity2),
            'similarities': [],
            'differences': []
        }
        
        # Add type-specific comparisons
        if entity1.entity_type == entity2.entity_type == 'vehicles':
            comparison.update(self._compare_vehicles(entity1.entity_id, entity2.entity_id))
        elif entity1.entity_type == entity2.entity_type == 'characters':
            comparison.update(self._compare_characters(entity1.entity_id, entity2.entity_id))
        
        return comparison
    
    def _get_entity_details(self, entity: SearchResult) -> Dict[str, Any]:
        """Get comprehensive details for an entity."""
        cursor = self.conn.cursor()
        
        details = {
            'basic_info': {
                'name': entity.name,
                'type': entity.entity_type,
                'description': entity.description
            }
        }
        
        # Add type-specific details
        if entity.entity_type == 'vehicles':
            # Get specifications
            cursor.execute("SELECT * FROM vehicle_specifications WHERE vehicle_id = ?", (entity.entity_id,))
            specs = cursor.fetchone()
            if specs:
                details['specifications'] = dict(specs)
            
            # Get weapons
            cursor.execute("SELECT weapon FROM vehicle_weapons WHERE vehicle_id = ?", (entity.entity_id,))
            weapons = [row['weapon'] for row in cursor.fetchall()]
            details['weapons'] = weapons
            
            # Get features
            cursor.execute("SELECT special_feature FROM vehicle_special_features WHERE vehicle_id = ?", (entity.entity_id,))
            features = [row['special_feature'] for row in cursor.fetchall()]
            details['special_features'] = features
        
        elif entity.entity_type == 'characters':
            # Get powers
            cursor.execute("SELECT power_ability FROM character_powers WHERE character_id = ?", (entity.entity_id,))
            powers = [row['power_ability'] for row in cursor.fetchall()]
            details['powers'] = powers
            
            # Get aliases
            cursor.execute("SELECT alias FROM character_aliases WHERE character_id = ?", (entity.entity_id,))
            aliases = [row['alias'] for row in cursor.fetchall()]
            details['aliases'] = aliases
        
        return details
    
    def _compare_vehicles(self, vehicle1_id: str, vehicle2_id: str) -> Dict[str, Any]:
        """Compare two vehicles in detail."""
        cursor = self.conn.cursor()
        
        # Get specifications for both
        cursor.execute("SELECT * FROM vehicle_specifications WHERE vehicle_id IN (?, ?)", 
                      (vehicle1_id, vehicle2_id))
        specs = {row['vehicle_id']: dict(row) for row in cursor.fetchall()}
        
        # Get weapons for both
        cursor.execute("SELECT vehicle_id, weapon FROM vehicle_weapons WHERE vehicle_id IN (?, ?)", 
                      (vehicle1_id, vehicle2_id))
        weapons = {}
        for row in cursor.fetchall():
            if row['vehicle_id'] not in weapons:
                weapons[row['vehicle_id']] = []
            weapons[row['vehicle_id']].append(row['weapon'])
        
        return {
            'specifications_comparison': specs,
            'weapons_comparison': weapons,
            'comparison_type': 'vehicles'
        }
    
    def _compare_characters(self, char1_id: str, char2_id: str) -> Dict[str, Any]:
        """Compare two characters in detail."""
        cursor = self.conn.cursor()
        
        # Get powers for both
        cursor.execute("SELECT character_id, power_ability FROM character_powers WHERE character_id IN (?, ?)", 
                      (char1_id, char2_id))
        powers = {}
        for row in cursor.fetchall():
            if row['character_id'] not in powers:
                powers[row['character_id']] = []
            powers[row['character_id']].append(row['power_ability'])
        
        return {
            'powers_comparison': powers,
            'comparison_type': 'characters'
        }