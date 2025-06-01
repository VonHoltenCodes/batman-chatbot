#!/usr/bin/env python3
"""
Conversation Intelligence for Batman Chatbot
Phase 3: Advanced query handling, comparisons, and relationships
"""

import sqlite3
import re
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
try:
    from .query_processor import AdvancedQueryProcessor, EntityMatch
    from .enhanced_comparisons import EnhancedComparisonEngine
except ImportError:
    from query_processor import AdvancedQueryProcessor, EntityMatch
    from enhanced_comparisons import EnhancedComparisonEngine

@dataclass
class ComparisonResult:
    """Result of comparing two entities."""
    entity1: Dict[str, Any]
    entity2: Dict[str, Any]
    comparison_type: str
    winner: Optional[str]
    explanation: str
    confidence: float

@dataclass
class RelationshipResult:
    """Result of a relationship query."""
    primary_entity: Dict[str, Any]
    related_entities: List[Dict[str, Any]]
    relationship_type: str
    explanation: str
    confidence: float

class ConversationIntelligence:
    """Advanced conversation intelligence for complex Batman queries."""
    
    def __init__(self, db_connection: sqlite3.Connection, query_processor: AdvancedQueryProcessor):
        """Initialize conversation intelligence."""
        self.conn = db_connection
        self.query_processor = query_processor
        self.enhanced_comparisons = EnhancedComparisonEngine(db_connection)
        
        # Comparison keywords and their types
        self.comparison_patterns = {
            'speed': {
                'keywords': ['faster', 'speed', 'quick', 'swift'],
                'attributes': ['max_speed', 'speed', 'velocity'],
                'winner_logic': 'higher_numeric'
            },
            'strength': {
                'keywords': ['stronger', 'strength', 'power', 'tough'],
                'attributes': ['strength', 'power_level'],
                'winner_logic': 'subjective_analysis'
            },
            'intelligence': {
                'keywords': ['smarter', 'intelligent', 'clever', 'genius'],
                'attributes': ['intelligence', 'iq'],
                'winner_logic': 'subjective_analysis'
            },
            'size': {
                'keywords': ['bigger', 'larger', 'size', 'massive'],
                'attributes': ['length', 'width', 'height', 'size'],
                'winner_logic': 'higher_numeric'
            },
            'armor': {
                'keywords': ['armored', 'protected', 'defensive', 'armor'],
                'attributes': ['armor', 'defensive_systems'],
                'winner_logic': 'count_features'
            }
        }
        
        # Relationship patterns
        self.relationship_patterns = {
            'allies': {
                'keywords': ['allies', 'friends', 'partners', 'team'],
                'relationship_types': ['ally', 'partner', 'friend', 'teammate']
            },
            'enemies': {
                'keywords': ['enemies', 'villains', 'foes', 'against'],
                'relationship_types': ['enemy', 'rival', 'nemesis', 'villain']
            },
            'family': {
                'keywords': ['family', 'relatives', 'father', 'son', 'daughter'],
                'relationship_types': ['family', 'father', 'son', 'daughter', 'parent', 'child']
            },
            'mentors': {
                'keywords': ['mentor', 'teacher', 'trainer', 'master'],
                'relationship_types': ['mentor', 'teacher', 'trainer', 'master']
            }
        }
        
        # Multi-entity query patterns
        self.multi_entity_patterns = {
            'list_all': {
                'keywords': ['all', 'list', 'every', 'show me'],
                'modifiers': ['vehicles', 'characters', 'locations', 'villains']
            },
            'category': {
                'keywords': ['vehicles', 'cars', 'planes', 'locations', 'places'],
                'entity_types': ['vehicles', 'locations', 'characters', 'organizations']
            }
        }
    
    def handle_comparative_query(self, query: str) -> Optional[ComparisonResult]:
        """
        Handle comparative queries like 'Who is faster: Batman or Nightwing?'
        
        Args:
            query: User's comparative query
            
        Returns:
            ComparisonResult or None if not a comparative query
        """
        # Extract comparison type and entities
        comparison_info = self._parse_comparison_query(query)
        if not comparison_info:
            return None
        
        comparison_type, entity1_name, entity2_name = comparison_info
        
        # Find the entities
        entity1_match = self.query_processor.find_best_entity_match(entity1_name, threshold=70)
        entity2_match = self.query_processor.find_best_entity_match(entity2_name, threshold=70)
        
        if not entity1_match or not entity2_match:
            return None
        
        # Get full entity data
        entity1 = self._get_entity_by_id(entity1_match.entity_id, entity1_match.entity_type)
        entity2 = self._get_entity_by_id(entity2_match.entity_id, entity2_match.entity_type)
        
        if not entity1 or not entity2:
            return None
        
        # Perform enhanced comparison
        return self._enhanced_compare_entities(entity1, entity2, entity1_match.entity_type, entity2_match.entity_type, comparison_type)
    
    def handle_relationship_query(self, query: str) -> Optional[RelationshipResult]:
        """
        Handle relationship queries like 'Who are Batman's allies?'
        
        Args:
            query: User's relationship query
            
        Returns:
            RelationshipResult or None
        """
        # Parse relationship query
        relationship_info = self._parse_relationship_query(query)
        if not relationship_info:
            return None
        
        entity_name, relationship_type = relationship_info
        
        # Find the primary entity
        entity_match = self.query_processor.find_best_entity_match(entity_name, threshold=70)
        if not entity_match:
            return None
        
        primary_entity = self._get_entity_by_id(entity_match.entity_id, entity_match.entity_type)
        if not primary_entity:
            return None
        
        # Find related entities
        related_entities = self._find_related_entities(entity_match.entity_id, entity_match.entity_type, relationship_type)
        
        if not related_entities:
            return None
        
        explanation = self._generate_relationship_explanation(primary_entity, related_entities, relationship_type)
        
        return RelationshipResult(
            primary_entity=primary_entity,
            related_entities=related_entities,
            relationship_type=relationship_type,
            explanation=explanation,
            confidence=0.8
        )
    
    def handle_multi_entity_query(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Handle multi-entity queries like 'Tell me about all of Batman's vehicles'
        
        Args:
            query: User's multi-entity query
            
        Returns:
            Dictionary with entities and metadata
        """
        # Parse multi-entity query
        query_info = self._parse_multi_entity_query(query)
        if not query_info:
            return None
        
        query_type, entity_type, filters = query_info
        
        # Get entities based on query type
        if query_type == 'list_all':
            entities = self._get_all_entities_of_type(entity_type, filters)
        elif query_type == 'character_related':
            # Find character first, then their related entities
            character_name = filters.get('character')
            if character_name:
                character_match = self.query_processor.find_best_entity_match(character_name, entity_type='characters', threshold=70)
                if character_match:
                    entities = self._get_character_related_entities(character_match.entity_id, entity_type)
                else:
                    return None
            else:
                return None
        else:
            return None
        
        if not entities:
            return None
        
        return {
            'query_type': query_type,
            'entity_type': entity_type,
            'entities': entities[:10],  # Limit to 10 for readability
            'total_count': len(entities),
            'explanation': self._generate_multi_entity_explanation(query_type, entity_type, len(entities))
        }
    
    def _parse_comparison_query(self, query: str) -> Optional[Tuple[str, str, str]]:
        """Parse comparative query to extract comparison type and entities."""
        query_lower = query.lower()
        
        # Look for comparison patterns
        comparison_type = None
        for comp_type, info in self.comparison_patterns.items():
            if any(keyword in query_lower for keyword in info['keywords']):
                comparison_type = comp_type
                break
        
        if not comparison_type:
            return None
        
        # Look for "vs", "versus", "or" patterns
        vs_patterns = [
            r'(.+?)\s+(?:vs|versus|against)\s+(.+?)(?:\?|$)',
            r'who.*(?:faster|stronger|smarter|bigger).*?:\s*(.+?)\s+or\s+(.+?)(?:\?|$)',
            r'(?:faster|stronger|smarter|bigger).*?:\s*(.+?)\s+(?:vs|versus|or)\s+(.+?)(?:\?|$)'
        ]
        
        for pattern in vs_patterns:
            match = re.search(pattern, query_lower)
            if match:
                entity1 = match.group(1).strip()
                entity2 = match.group(2).strip()
                return comparison_type, entity1, entity2
        
        return None
    
    def _parse_relationship_query(self, query: str) -> Optional[Tuple[str, str]]:
        """Parse relationship query to extract entity and relationship type."""
        query_lower = query.lower()
        
        # Enhanced relationship patterns
        if any(word in query_lower for word in ['enemies', 'villains', 'foes', 'rogues']):
            relationship_type = 'enemies'
        elif any(word in query_lower for word in ['allies', 'friends', 'partners', 'helpers']):
            relationship_type = 'allies'
        elif any(word in query_lower for word in ['family', 'relatives']):
            relationship_type = 'family'
        else:
            return None
        
        # Enhanced entity extraction patterns
        patterns = [
            r'who\s+(?:are|is)\s+(.+?)(?:\'s|s)\s+(?:allies|enemies|family|villains|friends)',
            r'(.+?)(?:\'s|s)\s+(?:allies|enemies|family|villains|friends)',
            r'(?:allies|enemies|family|villains|friends).*?(?:of|for)\s+(.+?)(?:\?|$)',
            r'what\s+(?:are|is)\s+(.+?)(?:\'s|s)\s+(?:allies|enemies)',
            r'list.*?(.+?)(?:\'s|s)\s+(?:enemies|allies)',
            r'who.*?(?:helps|fights)\s+(.+?)(?:\?|$)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query_lower)
            if match:
                entity_name = match.group(1).strip()
                # Clean up common articles
                entity_name = entity_name.replace('the ', '').strip()
                return entity_name, relationship_type
        
        return None
    
    def _parse_multi_entity_query(self, query: str) -> Optional[Tuple[str, str, Dict]]:
        """Parse multi-entity query to extract type and filters."""
        query_lower = query.lower()
        
        # Look for "all" or "list" queries or specific Batman context
        if any(word in query_lower for word in ['all', 'list', 'every', 'show']) or 'vehicles does batman' in query_lower or 'batman vehicles' in query_lower:
            # Determine entity type
            if any(word in query_lower for word in ['vehicle', 'car', 'plane', 'boat']) or 'vehicles does batman' in query_lower:
                entity_type = 'vehicles'
            elif any(word in query_lower for word in ['location', 'place', 'building']):
                entity_type = 'locations'
            elif any(word in query_lower for word in ['character', 'people', 'person', 'family', 'members']):
                entity_type = 'characters'
            elif any(word in query_lower for word in ['organization', 'group', 'team']):
                entity_type = 'organizations'
            else:
                return None
            
            # Check if it's character-related
            character_patterns = [
                r'(?:all|every).*?(?:of\s+|for\s+)?(.+?)(?:\'s|s)\s+',
                r'(.+?)(?:\'s|s)\s+(?:all|every)',
                r'tell.*?about.*?(.+?)(?:\'s|s)\s+'
            ]
            
            for pattern in character_patterns:
                match = re.search(pattern, query_lower)
                if match:
                    character_name = match.group(1).strip()
                    return 'character_related', entity_type, {'character': character_name}
            
            return 'list_all', entity_type, {}
        
        return None
    
    def _enhanced_compare_entities(self, entity1: Dict, entity2: Dict, type1: str, type2: str, comparison_type: str) -> ComparisonResult:
        """Enhanced entity comparison using the new comparison engine."""
        
        # Use enhanced comparison engine for character comparisons
        if type1 == 'characters' and type2 == 'characters':
            result = self.enhanced_comparisons.enhanced_character_comparison(
                entity1['name'], entity2['name'], comparison_type
            )
            
            return ComparisonResult(
                entity1=entity1,
                entity2=entity2,
                comparison_type=comparison_type,
                winner=result['winner'],
                explanation=result['explanation'],
                confidence=result['confidence']
            )
        
        # Use enhanced comparison engine for vehicle comparisons
        elif type1 == 'vehicles' and type2 == 'vehicles':
            result = self.enhanced_comparisons.enhanced_vehicle_comparison(
                entity1['name'], entity2['name'], comparison_type
            )
            
            return ComparisonResult(
                entity1=entity1,
                entity2=entity2,
                comparison_type=comparison_type,
                winner=result['winner'],
                explanation=result['explanation'],
                confidence=result['confidence']
            )
        
        # Fallback to original comparison logic for mixed types
        else:
            return self._compare_entities_fallback(entity1, entity2, type1, type2, comparison_type)
    
    def _compare_entities_fallback(self, entity1: Dict, entity2: Dict, type1: str, type2: str, comparison_type: str) -> ComparisonResult:
        """Compare two entities based on comparison type."""
        comparison_info = self.comparison_patterns[comparison_type]
        winner = None
        explanation = ""
        
        if comparison_type == 'speed' and type1 == 'vehicles' and type2 == 'vehicles':
            # Compare vehicle speeds
            speed1 = self._extract_speed_from_vehicle(entity1['id'])
            speed2 = self._extract_speed_from_vehicle(entity2['id'])
            
            if speed1 and speed2:
                try:
                    # Extract numeric values
                    num1 = float(re.search(r'(\d+)', speed1).group(1))
                    num2 = float(re.search(r'(\d+)', speed2).group(1))
                    
                    if num1 > num2:
                        winner = entity1['name']
                        explanation = f"The {entity1['name']} is faster with a top speed of {speed1} compared to the {entity2['name']}'s {speed2}."
                    elif num2 > num1:
                        winner = entity2['name']
                        explanation = f"The {entity2['name']} is faster with a top speed of {speed2} compared to the {entity1['name']}'s {speed1}."
                    else:
                        explanation = f"Both the {entity1['name']} and {entity2['name']} have similar speeds of {speed1} and {speed2} respectively."
                except:
                    explanation = f"Both vehicles have speed specifications: {entity1['name']} ({speed1}) vs {entity2['name']} ({speed2}), but exact comparison is difficult."
            else:
                explanation = f"Speed comparison between {entity1['name']} and {entity2['name']} is not available in the current data."
        
        elif comparison_type == 'strength' and type1 == 'characters' and type2 == 'characters':
            # Character strength comparison (subjective)
            explanation = self._compare_character_strength(entity1, entity2)
            winner = self._determine_strength_winner(entity1, entity2)
        
        elif comparison_type == 'intelligence' and type1 == 'characters' and type2 == 'characters':
            # Character intelligence comparison
            explanation = self._compare_character_intelligence(entity1, entity2)
            winner = self._determine_intelligence_winner(entity1, entity2)
        
        elif comparison_type == 'armor' and type1 == 'vehicles' and type2 == 'vehicles':
            # Vehicle armor comparison
            armor1 = self._get_vehicle_armor_info(entity1['id'])
            armor2 = self._get_vehicle_armor_info(entity2['id'])
            
            if armor1['count'] > armor2['count']:
                winner = entity1['name']
                explanation = f"The {entity1['name']} has more defensive systems ({armor1['count']}) compared to the {entity2['name']} ({armor2['count']})."
            elif armor2['count'] > armor1['count']:
                winner = entity2['name']
                explanation = f"The {entity2['name']} has more defensive systems ({armor2['count']}) compared to the {entity1['name']} ({armor1['count']})."
            else:
                explanation = f"Both vehicles have similar defensive capabilities with {armor1['count']} and {armor2['count']} systems respectively."
        
        else:
            explanation = f"Comparison of {comparison_type} between {entity1['name']} and {entity2['name']} is not currently supported."
        
        return ComparisonResult(
            entity1=entity1,
            entity2=entity2,
            comparison_type=comparison_type,
            winner=winner,
            explanation=explanation,
            confidence=0.7 if winner else 0.5
        )
    
    def _compare_character_strength(self, char1: Dict, char2: Dict) -> str:
        """Compare character strength based on descriptions and powers."""
        name1, name2 = char1['name'], char2['name']
        
        # Get character powers
        powers1 = self._get_character_powers(char1['id'])
        powers2 = self._get_character_powers(char2['id'])
        
        # Simple heuristic based on known characters
        strength_rankings = {
            'batman': 7, 'superman': 10, 'bane': 9, 'joker': 3, 
            'nightwing': 6, 'robin': 5, 'catwoman': 5, 'two-face': 4
        }
        
        char1_lower = name1.lower().replace('_', ' ')
        char2_lower = name2.lower().replace('_', ' ')
        
        score1 = 5  # Default
        score2 = 5  # Default
        
        for char, score in strength_rankings.items():
            if char in char1_lower:
                score1 = score
            if char in char2_lower:
                score2 = score
        
        # Adjust based on powers
        if powers1:
            if any('super' in power.lower() or 'enhanced' in power.lower() for power in powers1):
                score1 += 2
        
        if powers2:
            if any('super' in power.lower() or 'enhanced' in power.lower() for power in powers2):
                score2 += 2
        
        if score1 > score2:
            return f"Based on their abilities and background, {name1} appears to be stronger than {name2}."
        elif score2 > score1:
            return f"Based on their abilities and background, {name2} appears to be stronger than {name1}."
        else:
            return f"{name1} and {name2} appear to have similar strength levels."
    
    def _determine_strength_winner(self, char1: Dict, char2: Dict) -> Optional[str]:
        """Determine strength winner using simple heuristics."""
        strength_rankings = {
            'batman': 7, 'superman': 10, 'bane': 9, 'joker': 3,
            'nightwing': 6, 'robin': 5, 'catwoman': 5, 'two-face': 4
        }
        
        name1_lower = char1['name'].lower().replace('_', ' ')
        name2_lower = char2['name'].lower().replace('_', ' ')
        
        score1 = score2 = 5
        
        for char, score in strength_rankings.items():
            if char in name1_lower:
                score1 = score
            if char in name2_lower:
                score2 = score
        
        if score1 > score2:
            return char1['name']
        elif score2 > score1:
            return char2['name']
        
        return None
    
    def _compare_character_intelligence(self, char1: Dict, char2: Dict) -> str:
        """Compare character intelligence."""
        intelligence_rankings = {
            'batman': 10, 'lex luthor': 9, 'riddler': 8, 'joker': 7,
            'nightwing': 7, 'robin': 6, 'catwoman': 6, 'two-face': 5
        }
        
        name1_lower = char1['name'].lower().replace('_', ' ')
        name2_lower = char2['name'].lower().replace('_', ' ')
        
        score1 = score2 = 5
        
        for char, score in intelligence_rankings.items():
            if char in name1_lower:
                score1 = score
            if char in name2_lower:
                score2 = score
        
        if score1 > score2:
            return f"{char1['name']} is generally considered more intelligent than {char2['name']} in the Batman universe."
        elif score2 > score1:
            return f"{char2['name']} is generally considered more intelligent than {char1['name']} in the Batman universe."
        else:
            return f"Both {char1['name']} and {char2['name']} are considered highly intelligent in their own ways."
    
    def _determine_intelligence_winner(self, char1: Dict, char2: Dict) -> Optional[str]:
        """Determine intelligence winner."""
        intelligence_rankings = {
            'batman': 10, 'lex luthor': 9, 'riddler': 8, 'joker': 7,
            'nightwing': 7, 'robin': 6, 'catwoman': 6, 'two-face': 5
        }
        
        name1_lower = char1['name'].lower().replace('_', ' ')
        name2_lower = char2['name'].lower().replace('_', ' ')
        
        score1 = score2 = 5
        
        for char, score in intelligence_rankings.items():
            if char in name1_lower:
                score1 = score
            if char in name2_lower:
                score2 = score
        
        if score1 > score2:
            return char1['name']
        elif score2 > score1:
            return char2['name']
        
        return None
    
    def _extract_speed_from_vehicle(self, vehicle_id: str) -> Optional[str]:
        """Extract speed information from vehicle specifications."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT max_speed FROM vehicle_specifications WHERE vehicle_id = ?", (vehicle_id,))
            result = cursor.fetchone()
            return result[0] if result and result[0] else None
        except:
            return None
    
    def _get_vehicle_armor_info(self, vehicle_id: str) -> Dict[str, Any]:
        """Get vehicle armor and defensive systems information."""
        try:
            cursor = self.conn.cursor()
            
            # Get armor description
            cursor.execute("SELECT armor FROM vehicle_specifications WHERE vehicle_id = ?", (vehicle_id,))
            armor_result = cursor.fetchone()
            armor = armor_result[0] if armor_result and armor_result[0] else ""
            
            # Get defensive systems count
            cursor.execute("SELECT COUNT(*) FROM vehicle_defensive_systems WHERE vehicle_id = ?", (vehicle_id,))
            defensive_count = cursor.fetchone()[0]
            
            return {
                'armor': armor,
                'count': defensive_count,
                'total_score': len(armor) + defensive_count * 10
            }
        except:
            return {'armor': '', 'count': 0, 'total_score': 0}
    
    def _get_character_powers(self, character_id: str) -> List[str]:
        """Get character powers and abilities."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT power_ability FROM character_powers WHERE character_id = ?", (character_id,))
            return [row[0] for row in cursor.fetchall()]
        except:
            return []
    
    def _find_related_entities(self, entity_id: str, entity_type: str, relationship_type: str) -> List[Dict]:
        """Find entities related to the given entity with enhanced logic."""
        related = []
        
        try:
            cursor = self.conn.cursor()
            
            if entity_type == 'characters':
                # Try database relationships first
                cursor.execute("""
                    SELECT c.id, c.name, c.description, cr.relationship_type
                    FROM characters c
                    JOIN character_relationships cr ON c.id = cr.related_character_id
                    WHERE cr.character_id = ?
                    LIMIT 10
                """, (entity_id,))
                
                for row in cursor.fetchall():
                    related.append({
                        'id': row[0],
                        'name': row[1],
                        'description': row[2],
                        'relationship': row[3],
                        'type': 'character'
                    })
                
                # If no database relationships, use predefined knowledge
                if not related:
                    related = self._get_predefined_relationships(entity_id, relationship_type)
            
            return related
        except:
            return self._get_predefined_relationships(entity_id, relationship_type)
    
    def _get_predefined_relationships(self, entity_id: str, relationship_type: str) -> List[Dict]:
        """Get predefined relationships when database relationships are sparse."""
        # Get entity name first
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name FROM characters WHERE id = ?", (entity_id,))
            result = cursor.fetchone()
            if not result:
                return []
            
            entity_name = result[0].lower().replace('_', ' ')
            
            # Predefined Batman universe relationships
            batman_relationships = {
                'allies': ['Robin', 'Nightwing', 'Batgirl', 'Alfred_Pennyworth', 'Commissioner_Gordon', 'Oracle', 'Red_Robin', 'Catwoman'],
                'enemies': ['Joker', 'Two-Face', 'Penguin', 'Riddler', 'Bane', 'Scarecrow', 'Poison_Ivy', 'Mr_Freeze', 'Harley_Quinn', 'Ra\'s_al_Ghul']
            }
            
            joker_relationships = {
                'allies': ['Harley_Quinn', 'Penguin'],
                'enemies': ['Batman', 'Robin', 'Nightwing', 'Batgirl']
            }
            
            # Determine which character and get their relationships
            if 'batman' in entity_name or 'bruce wayne' in entity_name:
                target_list = batman_relationships.get(relationship_type, [])
            elif 'joker' in entity_name:
                target_list = joker_relationships.get(relationship_type, [])
            else:
                # For other characters, provide general relationships
                if relationship_type == 'enemies':
                    target_list = ['Batman'] if 'batman' not in entity_name else []
                else:
                    target_list = []
            
            # Convert names to database entities
            related = []
            for name in target_list[:8]:  # Limit to 8 relationships
                try:
                    cursor.execute("SELECT id, name, description FROM characters WHERE LOWER(name) LIKE LOWER(?)", (f"%{name}%",))
                    char_result = cursor.fetchone()
                    if char_result:
                        related.append({
                            'id': char_result[0],
                            'name': char_result[1],
                            'description': char_result[2][:100] + "..." if len(char_result[2]) > 100 else char_result[2],
                            'relationship': relationship_type[:-1],  # Remove 's' from 'allies'/'enemies'
                            'type': 'character'
                        })
                except:
                    continue
            
            return related
            
        except:
            return []
    
    def _get_all_entities_of_type(self, entity_type: str, filters: Dict) -> List[Dict]:
        """Get all entities of a specific type."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT id, name, description FROM {entity_type} LIMIT 20")
            
            entities = []
            for row in cursor.fetchall():
                entities.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2][:100] + "..." if len(row[2]) > 100 else row[2],
                    'type': entity_type
                })
            
            return entities
        except:
            return []
    
    def _get_character_related_entities(self, character_id: str, entity_type: str) -> List[Dict]:
        """Get entities related to a specific character."""
        try:
            cursor = self.conn.cursor()
            
            if entity_type == 'vehicles':
                # Get vehicles used by character
                cursor.execute("""
                    SELECT v.id, v.name, v.description
                    FROM vehicles v
                    JOIN vehicle_users vu ON v.id = vu.vehicle_id
                    WHERE vu.character_id = ?
                """, (character_id,))
            elif entity_type == 'locations':
                # Get locations associated with character
                cursor.execute("""
                    SELECT l.id, l.name, l.description
                    FROM locations l
                    JOIN character_locations cl ON l.id = cl.location_id
                    WHERE cl.character_id = ?
                """, (character_id,))
            else:
                return []
            
            entities = []
            for row in cursor.fetchall():
                entities.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2][:100] + "..." if len(row[2]) > 100 else row[2],
                    'type': entity_type
                })
            
            return entities
        except:
            return []
    
    def _generate_relationship_explanation(self, primary: Dict, related: List[Dict], rel_type: str) -> str:
        """Generate explanation for relationship query."""
        if not related:
            return f"No {rel_type} found for {primary['name']} in the current database."
        
        if len(related) == 1:
            return f"{primary['name']}'s {rel_type[:-1]} is {related[0]['name']}."
        else:
            names = [entity['name'] for entity in related[:5]]
            if len(related) > 5:
                return f"{primary['name']}'s {rel_type} include {', '.join(names[:-1])}, {names[-1]}, and {len(related)-5} others."
            else:
                return f"{primary['name']}'s {rel_type} include {', '.join(names[:-1])} and {names[-1]}."
    
    def _generate_multi_entity_explanation(self, query_type: str, entity_type: str, count: int) -> str:
        """Generate explanation for multi-entity query."""
        if query_type == 'list_all':
            return f"I found {count} {entity_type} in the Batman universe database."
        elif query_type == 'character_related':
            return f"Here are {count} {entity_type} associated with this character."
        else:
            return f"Found {count} matching {entity_type}."
    
    def _get_entity_by_id(self, entity_id: str, entity_type: str) -> Optional[Dict]:
        """Get entity by ID from database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT * FROM {entity_type} WHERE id = ?", (entity_id,))
            result = cursor.fetchone()
            
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            
            return None
        except:
            return None

def test_conversation_intelligence():
    """Test conversation intelligence features."""
    import sqlite3
    from query_processor import AdvancedQueryProcessor
    
    # Connect to database
    db_path = "../../database/batman_universe.db"
    conn = sqlite3.connect(db_path)
    
    # Initialize processors
    query_processor = AdvancedQueryProcessor(conn)
    conv_intel = ConversationIntelligence(conn, query_processor)
    
    print("🧠 Testing Conversation Intelligence")
    print("=" * 50)
    
    # Test comparative queries
    test_queries = [
        "Who is faster: Batman or Nightwing?",
        "Which is more armored: Batmobile or Batwing?",
        "Who is smarter: Batman or Joker?",
        "Who are Batman's allies?",
        "Tell me about all of Batman's vehicles"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Try comparative query
        comp_result = conv_intel.handle_comparative_query(query)
        if comp_result:
            print(f"✅ Comparison: {comp_result.explanation}")
            continue
        
        # Try relationship query
        rel_result = conv_intel.handle_relationship_query(query)
        if rel_result:
            print(f"✅ Relationship: {rel_result.explanation}")
            continue
        
        # Try multi-entity query
        multi_result = conv_intel.handle_multi_entity_query(query)
        if multi_result:
            print(f"✅ Multi-entity: {multi_result['explanation']}")
            continue
        
        print("❌ Not recognized as advanced query")
    
    conn.close()

if __name__ == "__main__":
    test_conversation_intelligence()