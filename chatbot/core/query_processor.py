#!/usr/bin/env python3
"""
Advanced Query Processor for Batman Chatbot
Phase 2.2: Enhanced query processing with fuzzy matching and semantic search
"""

import sqlite3
import re
from typing import Dict, List, Optional, Tuple, Any
from fuzzywuzzy import fuzz, process
from dataclasses import dataclass

@dataclass
class EntityMatch:
    """Represents a matched entity with confidence score."""
    entity_id: str
    entity_type: str
    name: str
    confidence: float
    match_type: str  # exact, fuzzy, alias, description

class AdvancedQueryProcessor:
    """Advanced query processing with fuzzy matching and semantic search."""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize the advanced query processor."""
        self.conn = db_connection
        # Ensure thread safety for database operations
        if hasattr(self.conn, 'check_same_thread'):
            self.conn.check_same_thread = False
        self.entity_cache = self._build_entity_cache()
        
    def _build_entity_cache(self) -> Dict[str, List[Dict]]:
        """Build in-memory cache of all entities for fast fuzzy matching."""
        cache = {
            'characters': [],
            'vehicles': [], 
            'locations': [],
            'storylines': [],
            'organizations': []
        }
        
        cursor = self.conn.cursor()
        
        # Cache characters
        cursor.execute("SELECT id, name, description FROM characters")
        for row in cursor.fetchall():
            cache['characters'].append({
                'id': row[0], 
                'name': row[1], 
                'description': row[2] or ''
            })
        
        # Cache character aliases
        cursor.execute("""
            SELECT c.id, c.name, ca.alias 
            FROM characters c 
            JOIN character_aliases ca ON c.id = ca.character_id
        """)
        for row in cursor.fetchall():
            cache['characters'].append({
                'id': row[0],
                'name': row[2],  # Use alias as name for matching
                'description': '',
                'is_alias': True,
                'real_name': row[1]
            })
        
        # Cache vehicles
        cursor.execute("SELECT id, name, description FROM vehicles")
        for row in cursor.fetchall():
            cache['vehicles'].append({
                'id': row[0],
                'name': row[1],
                'description': row[2] or ''
            })
        
        # Cache locations
        cursor.execute("SELECT id, name, description FROM locations")
        for row in cursor.fetchall():
            cache['locations'].append({
                'id': row[0],
                'name': row[1], 
                'description': row[2] or ''
            })
        
        # Cache storylines
        cursor.execute("SELECT id, name, description FROM storylines")
        for row in cursor.fetchall():
            cache['storylines'].append({
                'id': row[0],
                'name': row[1],
                'description': row[2] or ''
            })
        
        # Cache organizations
        cursor.execute("SELECT id, name, description FROM organizations")
        for row in cursor.fetchall():
            cache['organizations'].append({
                'id': row[0],
                'name': row[1],
                'description': row[2] or ''
            })
        
        print(f"🧠 Entity cache built: {sum(len(entities) for entities in cache.values())} total entities")
        return cache
    
    def find_best_entity_match(self, query: str, entity_type: str = None, threshold: int = 70) -> Optional[EntityMatch]:
        """
        Find the best matching entity using advanced fuzzy matching.
        
        Args:
            query: User's search query
            entity_type: Specific entity type to search (optional)
            threshold: Minimum confidence threshold (0-100)
            
        Returns:
            Best matching entity or None
        """
        # Clean the query
        clean_query = self._clean_query_for_matching(query)
        
        # Determine which entity types to search
        search_types = [entity_type] if entity_type else ['characters', 'vehicles', 'locations', 'storylines', 'organizations']
        
        best_match = None
        best_score = 0
        
        for etype in search_types:
            if etype not in self.entity_cache:
                continue
                
            # Get all entity names for this type
            entity_names = [(entity['name'], entity) for entity in self.entity_cache[etype]]
            
            if not entity_names:
                continue
                
            # Use fuzzywuzzy to find best matches
            matches = process.extract(clean_query, [name for name, _ in entity_names], limit=5)
            
            # Create candidates with importance scoring
            candidates = []
            for match_name, score in matches:
                if score >= max(threshold, 50):  # Lower threshold to consider more candidates
                    # Find the corresponding entity
                    matched_entity = next(entity for name, entity in entity_names if name == match_name)
                    
                    # Calculate importance bonus
                    importance_bonus = self._calculate_importance_bonus(matched_entity['name'], etype)
                    final_score = score + (importance_bonus * 100)  # Scale bonus to score range
                    
                    candidates.append({
                        'entity': EntityMatch(
                            entity_id=matched_entity['id'],
                            entity_type=etype,
                            name=matched_entity.get('real_name', matched_entity['name']),
                            confidence=score / 100.0,  # Keep original fuzzy score for confidence
                            match_type='alias' if matched_entity.get('is_alias') else 'fuzzy'
                        ),
                        'final_score': final_score,
                        'original_score': score,
                        'importance_bonus': importance_bonus
                    })
            
            # Find the best candidate by final score
            for candidate in candidates:
                if candidate['final_score'] > best_score:
                    best_match = candidate['entity']
                    best_score = candidate['final_score']
        
        return best_match
    
    def find_multiple_entities(self, query: str, max_results: int = 5, threshold: int = 60) -> List[EntityMatch]:
        """Find multiple potential entity matches with intelligent ranking."""
        clean_query = self._clean_query_for_matching(query)
        matches = []
        
        # Entity importance rankings (higher = more important)
        entity_importance = {
            'Batman': 100, 'Joker': 95, 'Robin_(Dick_Grayson)': 90, 'Robin_(Tim_Drake)': 85,
            'Robin_(Damian_Wayne)': 80, 'Alfred_Pennyworth': 85, 'Commissioner_Gordon': 80,
            'Nightwing': 80, 'Batgirl': 75, 'Catwoman': 80, 'Two-Face': 70, 'Penguin': 70,
            'Riddler': 70, 'Bane': 75, 'Scarecrow': 65, 'Harley_Quinn': 70, 'Poison_Ivy': 65,
            'Batmobile': 90, 'Batwing': 80, 'Wayne_Manor': 80, 'Gotham_City': 90, 'Arkham_Asylum': 75
        }
        
        for entity_type in ['characters', 'vehicles', 'locations', 'storylines', 'organizations']:
            entity_names = [(entity['name'], entity) for entity in self.entity_cache[entity_type]]
            
            if not entity_names:
                continue
                
            fuzzy_matches = process.extract(clean_query, [name for name, _ in entity_names], limit=8)
            
            for match_name, score in fuzzy_matches:
                if score >= threshold:
                    matched_entity = next(entity for name, entity in entity_names if name == match_name)
                    
                    # Calculate boosted score based on importance
                    importance_boost = entity_importance.get(matched_entity['name'], 0)
                    boosted_score = score + (importance_boost * 0.1)  # Up to 10 point boost
                    
                    match = EntityMatch(
                        entity_id=matched_entity['id'],
                        entity_type=entity_type,
                        name=matched_entity.get('real_name', matched_entity['name']),
                        confidence=min(boosted_score / 100.0, 1.0),  # Cap at 1.0
                        match_type='alias' if matched_entity.get('is_alias') else 'fuzzy'
                    )
                    matches.append(match)
        
        # Sort by boosted confidence, then by original confidence
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches[:max_results]
    
    def semantic_search(self, query: str, entity_type: str = None, max_results: int = 5) -> List[EntityMatch]:
        """
        Perform semantic search across entity descriptions.
        
        Args:
            query: Search query
            entity_type: Specific entity type (optional)
            max_results: Maximum number of results
            
        Returns:
            List of matching entities
        """
        search_types = [entity_type] if entity_type else ['characters', 'vehicles', 'locations', 'storylines', 'organizations']
        matches = []
        
        # Extract keywords from query
        keywords = self._extract_keywords(query)
        
        for etype in search_types:
            if etype not in self.entity_cache:
                continue
                
            for entity in self.entity_cache[etype]:
                description = entity['description'].lower()
                name = entity['name'].lower()
                
                # Calculate relevance score based on keyword matches
                score = 0
                
                # Name matches get higher score
                for keyword in keywords:
                    if keyword in name:
                        score += 20
                    elif keyword in description:
                        score += 10
                
                # Bonus for multiple keyword matches
                keyword_matches = sum(1 for keyword in keywords if keyword in description or keyword in name)
                if keyword_matches > 1:
                    score += keyword_matches * 5
                
                if score > 0:
                    match = EntityMatch(
                        entity_id=entity['id'],
                        entity_type=etype,
                        name=entity['name'],
                        confidence=min(score / 100.0, 1.0),  # Normalize to 0-1
                        match_type='description'
                    )
                    matches.append(match)
        
        # Sort by confidence and return top results
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches[:max_results]
    
    def handle_ambiguous_query(self, query: str) -> Dict[str, Any]:
        """
        Handle ambiguous queries by finding multiple potential matches.
        
        Returns:
            Dictionary with potential matches and suggestions
        """
        # Find multiple potential matches
        potential_matches = self.find_multiple_entities(query, max_results=5, threshold=50)
        
        if len(potential_matches) == 0:
            return {
                'type': 'no_matches',
                'message': f"I couldn't find any Batman universe information for '{query}'. Try being more specific.",
                'suggestions': self._get_random_suggestions()
            }
        elif len(potential_matches) == 1:
            return {
                'type': 'single_match',
                'match': potential_matches[0],
                'message': f"I found one match for '{query}'"
            }
        else:
            return {
                'type': 'multiple_matches',
                'matches': potential_matches,
                'message': f"I found multiple matches for '{query}'. Which one did you mean?",
                'suggestions': [match.name for match in potential_matches]
            }
    
    def _clean_query_for_matching(self, query: str) -> str:
        """Clean query for better fuzzy matching."""
        query_lower = query.lower()
        
        # Handle common aliases and alternative names first
        alias_mappings = {
            'city of gotham': 'gotham city',
            'batman\'s base': 'batcave',
            'batman base': 'batcave',
            'where does batman live': 'wayne manor',
            'batman\'s car': 'batmobile',
            'batman car': 'batmobile',
            'what does batman drive': 'batmobile',
            'batman\'s plane': 'batwing',
            'batman plane': 'batwing',
            'dark knight': 'batman',
            'caped crusader': 'batman',
            'world\'s greatest detective': 'batman',
            'clown prince of crime': 'joker',
            'scarecrow real name': 'jonathan crane',
            'scarecrow\'s real name': 'jonathan crane',
            'batman\'s primary mode of transportation': 'batmobile'
        }
        
        # Check for exact alias matches
        for alias, canonical in alias_mappings.items():
            if alias in query_lower:
                query_lower = query_lower.replace(alias, canonical)
                break
        
        # Remove common stop words but preserve entity names
        stop_words = ['who', 'is', 'what', 'where', 'the', 'a', 'an', 'tell', 'me', 'about', 'does', 'usually', 'operate']
        
        # Convert to lowercase and split
        words = query_lower.split()
        
        # Remove stop words but keep important words
        cleaned_words = []
        for word in words:
            # Remove punctuation
            clean_word = re.sub(r'[^\w\s]', '', word)
            if clean_word and clean_word not in stop_words:
                cleaned_words.append(clean_word)
        
        return ' '.join(cleaned_words)
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract meaningful keywords from query."""
        # Remove stop words and punctuation
        stop_words = {'who', 'is', 'what', 'where', 'when', 'how', 'the', 'a', 'an', 'and', 'or', 'but', 'tell', 'me', 'about', 'can', 'you'}
        
        # Split and clean
        words = re.findall(r'\b\w+\b', query.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _get_random_suggestions(self) -> List[str]:
        """Get random entity suggestions for when no matches are found."""
        suggestions = [
            "Batman", "Joker", "Batmobile", "Gotham City", "Robin", 
            "Alfred", "Catwoman", "Bane", "Two-Face", "Arkham Asylum"
        ]
        return suggestions[:3]
    
    def classify_query_intent(self, query: str) -> Dict[str, Any]:
        """
        Classify the intent of the user's query.
        
        Returns:
            Dictionary with intent type and extracted information
        """
        query_lower = query.lower()
        
        # Intent patterns
        intent_patterns = {
            'character_info': [
                r'who (is|are|was|were) (.+)',
                r'tell me about (.+)',
                r'what (is|are) (.+) like',
                r'describe (.+)'
            ],
            'location_info': [
                r'where (is|are|was|were) (.+)',
                r'what.*location.*(.+)',
                r'describe the place (.+)'
            ],
            'vehicle_info': [
                r'what.*vehicle.*(.+)',
                r'(batmobile|batwing|batboat|batcycle)',
                r'what.*drive.*(.+)',
                r'transportation.*(.+)'
            ],
            'relationship': [
                r'(.+) (vs|versus|against) (.+)',
                r'relationship between (.+) and (.+)',
                r'who (are|is) (.+) (allies|enemies|friends)',
                r'(.+) (ally|enemy|friend) (.+)'
            ],
            'comparison': [
                r'who.*faster.*(.+)',
                r'who.*stronger.*(.+)', 
                r'what.*difference.*(.+)',
                r'compare (.+) (to|with|and) (.+)'
            ],
            'list_request': [
                r'list.*(.+)',
                r'what.*all.*(.+)',
                r'who.*all.*(.+)',
                r'show.*(.+)'
            ]
        }
        
        # Check each intent pattern
        for intent, patterns in intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query_lower)
                if match:
                    extracted_entities = [group.strip() for group in match.groups() if group.strip()]
                    return {
                        'intent': intent,
                        'entities': extracted_entities,
                        'confidence': 0.8,
                        'pattern_matched': pattern
                    }
        
        # Default to general info request
        return {
            'intent': 'general_info',
            'entities': [query.strip()],
            'confidence': 0.5,
            'pattern_matched': None
        }
    
    def _calculate_importance_bonus(self, entity_name: str, entity_type: str) -> float:
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
        
        if entity_type == 'characters' and any(main_char in name_lower for main_char in main_characters):
            return 0.2  # 20% bonus for main characters
        elif entity_type == 'locations' and any(main_loc in name_lower for main_loc in main_locations):
            return 0.15  # 15% bonus for main locations
        elif entity_type == 'vehicles' and any(main_veh in name_lower for main_veh in main_vehicles):
            return 0.15  # 15% bonus for main vehicles
        elif len(entity_name.replace('_', ' ').split()) <= 2:
            return 0.05  # Small bonus for shorter/simpler names
        
        return 0.0  # No bonus for minor characters
    
    def find_best_vehicle_match(self, query: str, threshold: int = 70) -> Optional[EntityMatch]:
        """
        Find the best matching vehicle with context-aware selection.
        
        Args:
            query: User's search query (e.g., "what does joker drive")
            threshold: Minimum confidence threshold (0-100)
            
        Returns:
            Best matching vehicle considering query context
        """
        # Clean the query and extract character name if present
        clean_query = self._clean_query_for_matching(query)
        original_query = query.lower()
        
        # Extract character name from patterns like "what does X drive"
        character_patterns = [
            r'what (?:does|do) (.+?) (?:drive|use|pilot|operate)',
            r'what (?:car|vehicle|transportation) (?:does|do) (.+?) (?:drive|use|have)',
            r'(.+?)(?:\'s|s) (?:car|vehicle|mobile)'
        ]
        
        character_name = None
        for pattern in character_patterns:
            match = re.search(pattern, original_query)
            if match:
                character_name = match.group(1).strip()
                break
        
        # If we found a character name, search for vehicles associated with that character
        if character_name:
            # Use lower threshold for character vehicles since they're more specific
            character_threshold = min(threshold, 40)  # Lower threshold for character-specific searches
            return self._find_character_vehicle(character_name, original_query, character_threshold)
        else:
            # Fall back to regular vehicle search
            return self.find_best_entity_match(clean_query, entity_type='vehicles', threshold=threshold)
    
    def _find_character_vehicle(self, character_name: str, original_query: str, threshold: int = 50) -> Optional[EntityMatch]:
        """Find the best vehicle for a specific character with smart prioritization."""
        
        # Get all vehicles that are related to the character (more flexible matching)
        character_vehicles = []
        for vehicle in self.entity_cache.get('vehicles', []):
            if self._is_character_vehicle_match(character_name, vehicle['name']):
                character_vehicles.append(vehicle)
        
        if not character_vehicles:
            return None
        
        # Score each vehicle based on multiple factors
        scored_vehicles = []
        for vehicle in character_vehicles:
            score = self._calculate_vehicle_score(vehicle, character_name, original_query)
            if score >= threshold:
                scored_vehicles.append((vehicle, score))
        
        if not scored_vehicles:
            return None
        
        # Return the highest-scored vehicle
        best_vehicle, best_score = max(scored_vehicles, key=lambda x: x[1])
        
        return EntityMatch(
            entity_id=best_vehicle['id'],
            entity_type='vehicles',
            name=best_vehicle['name'],
            confidence=min(best_score / 100.0, 1.0),  # Convert to 0-1 scale
            match_type='character_vehicle'
        )
    
    def _calculate_vehicle_score(self, vehicle: dict, character_name: str, query: str) -> float:
        """Calculate a smart score for character vehicle selection."""
        score = 0.0
        vehicle_name = vehicle['name'].lower()
        
        # Base fuzzy match score
        fuzzy_score = fuzz.ratio(character_name.lower(), vehicle_name)
        score += fuzzy_score
        
        # Query context bonuses
        query_lower = query.lower()
        
        # Prefer vehicles appropriate for the query type
        if 'drive' in query_lower or 'car' in query_lower:
            # Prioritize cars/mobiles for "drive" queries
            if any(car_word in vehicle_name for car_word in ['mobile', 'car', 'vehicle']):
                score += 25  # Strong bonus for cars
            elif any(ground_word in vehicle_name for ground_word in ['cycle', 'bike']):
                score += 15  # Medium bonus for ground vehicles  
            elif any(air_word in vehicle_name for air_word in ['copter', 'plane', 'wing']):
                score += 5   # Small bonus for aircraft
            elif any(water_word in vehicle_name for water_word in ['boat', 'sub', 'ship', 'submarine']):
                # Special case: Penguin's submarine should still be acceptable for "drive"
                if character_name.lower() == 'penguin' and 'submarine' in vehicle_name:
                    score += 15  # Medium bonus for Penguin's submarine
                else:
                    score -= 10  # Penalty for other water vehicles when asking about "drive"
            elif any(train_word in vehicle_name for train_word in ['train', 'rail']):
                score -= 15  # Penalty for trains when asking about "drive"
        
        # Prefer iconic/main vehicles
        if character_name.lower() == 'joker':
            if 'jokermobile' in vehicle_name and 'dozierverse' not in vehicle_name:
                score += 30  # Main Jokermobile gets top priority
            elif 'jokermobile' in vehicle_name:
                score += 20  # Other Jokermobiles get high priority
            elif 'goon_car' in vehicle_name:
                score += 10  # Joker Goon Car is also a good choice
        
        elif character_name.lower() == 'batman':
            if vehicle_name == 'batmobile' or ('batmobile' in vehicle_name and len(vehicle_name.split('_')) <= 2):
                score += 30  # Main Batmobile gets top priority
        
        elif character_name.lower() == 'penguin':
            if 'submarine' in vehicle_name:
                score += 30  # Penguin's submarine gets top priority
            elif 'penguin' in vehicle_name:
                score += 20  # Other Penguin vehicles get high priority
        
        # Penalty for overly specific versions (with parentheses/universes)
        if '(' in vehicle_name or 'verse' in vehicle_name:
            score -= 5  # Small penalty for universe-specific vehicles
        
        # Small penalty for URL encoding issues (but don't reject completely)
        if '%' in vehicle_name:
            score -= 3  # Small penalty for malformed names
        
        return score
    
    def _is_character_vehicle_match(self, character_name: str, vehicle_name: str) -> bool:
        """Check if a vehicle is related to a character with flexible matching."""
        character_lower = character_name.lower()
        vehicle_lower = vehicle_name.lower()
        
        # Direct character name match (exact)
        if character_lower in vehicle_lower:
            return True
        
        # Character-specific matching rules
        if character_lower == 'batman':
            # Batman vehicles: batmobile, batcycle, batwing, batboat, etc.
            return any(bat_vehicle in vehicle_lower for bat_vehicle in [
                'batmobile', 'batcycle', 'batwing', 'batboat', 'batcopter'
            ])
        
        elif character_lower == 'joker':
            # Joker vehicles already handled by direct match
            return False
        
        elif character_lower in ['two face', 'two-face', 'twoface']:
            # Two-Face vehicles (handle hyphen variations)
            return any(tf_variant in vehicle_lower for tf_variant in [
                'two-face', 'two_face', 'twoface'
            ])
        
        elif character_lower == 'penguin':
            # Penguin vehicles
            return 'penguin' in vehicle_lower
        
        elif character_lower == 'riddler':
            # Riddler vehicles
            return 'riddler' in vehicle_lower
        
        elif character_lower == 'catwoman':
            # Catwoman vehicles (might be catmobile, catcycle, etc.)
            return any(cat_vehicle in vehicle_lower for cat_vehicle in [
                'catwoman', 'catmobile', 'catcycle', 'catboat'
            ])
        
        elif character_lower in ['harvey dent', 'harvey']:
            # Harvey Dent = Two-Face
            return any(tf_variant in vehicle_lower for tf_variant in [
                'two-face', 'two_face', 'harvey', 'dent'
            ])
        
        # Default: no match
        return False

def test_query_processor():
    """Test the advanced query processor."""
    import sqlite3
    
    # Connect to database
    db_path = "../../database/batman_universe.db"
    conn = sqlite3.connect(db_path)
    
    # Initialize processor
    processor = AdvancedQueryProcessor(conn)
    
    # Test queries
    test_queries = [
        "Who is Btmn?",  # Typo
        "Tell me about the Jokr",  # Typo
        "What is the Batmobil?",  # Typo  
        "Harvy Dent",  # Typo
        "Who is the fastest character?",
        "Batman vs Joker",
        "Where is Gothm City?"  # Typo
    ]
    
    print("🧪 Testing Advanced Query Processor")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Test entity matching
        match = processor.find_best_entity_match(query)
        if match:
            print(f"✅ Best match: {match.name} ({match.entity_type}) - {match.confidence:.1%}")
        else:
            print("❌ No match found")
        
        # Test intent classification
        intent = processor.classify_query_intent(query)
        print(f"🎯 Intent: {intent['intent']} - Entities: {intent['entities']}")
    
    conn.close()

if __name__ == "__main__":
    test_query_processor()