#!/usr/bin/env python3
"""
Batman Chatbot Core Engine
Phase 2: Core Chatbot Architecture

The ultimate Batman universe expert chatbot powered by 1,056 entities.
"""

import os
import sys
import sqlite3
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import advanced query processor, response generator, and conversation intelligence
from .query_processor import AdvancedQueryProcessor
from .response_generator import BatmanResponseGenerator, ResponseContext
from .conversation_intelligence import ConversationIntelligence
from .intelligent_search import IntelligentSearchEngine
from .relationship_processor import RelationshipProcessor

@dataclass
class BatmanResponse:
    """Response structure for Batman chatbot."""
    answer: str
    confidence: float
    source_entities: List[str]
    query_type: str
    suggestions: List[str] = None

class BatmanChatbot:
    """
    The Ultimate Batman Universe Expert Chatbot
    
    Features:
    - 1,056 Batman entities (characters, vehicles, locations, storylines, organizations)
    - Advanced fuzzy matching for character names and aliases
    - Full-text search capabilities
    - Context-aware responses
    - Batman expert personality
    """
    
    def __init__(self, db_path: str = "../database/batman_universe.db"):
        """Initialize the Batman chatbot."""
        self.db_path = os.path.abspath(db_path)
        self.conn = None
        self.conversation_history = []
        
        # Chatbot personality settings
        self.personality = {
            "expertise_level": "expert",
            "tone": "knowledgeable",
            "batman_focus": True,
            "detailed_responses": True
        }
        
        # Response templates
        self.templates = {
            "character_info": "Based on my knowledge of the Batman universe, {name} is {description}",
            "not_found": "I don't have information about '{query}' in my Batman database. Could you be more specific or check the spelling?",
            "multiple_matches": "I found multiple matches for '{query}'. Please select which one you'd like to learn about:\n\n{matches}\n\nType the number of your choice, or be more specific with your question.",
            "relationship": "{character1} and {character2} have a {relationship} relationship in the Batman universe.",
            "location_info": "{location} is {description}",
            "vehicle_info": "The {vehicle} is {description}",
            "organization_info": "{organization} is {description}",
            "storyline_info": "{storyline} is {description}"
        }
        
        # Initialize database connection and advanced processors
        self.connect_database()
        self.query_processor = None
        self.response_generator = None
        self.conversation_intelligence = None
        self.search_engine = None
        self.relationship_processor = None
        if self.conn:
            self.query_processor = AdvancedQueryProcessor(self.conn)
            self.response_generator = BatmanResponseGenerator(self.conn)
            self.conversation_intelligence = ConversationIntelligence(self.conn, self.query_processor)
            self.search_engine = IntelligentSearchEngine(self.conn)
            self.relationship_processor = RelationshipProcessor(self.conn)
        print("🦇 Batman Chatbot initialized with 1,056 entities and relationship intelligence!")
    
    def connect_database(self) -> bool:
        """Connect to the Batman universe database."""
        try:
            if not os.path.exists(self.db_path):
                print(f"❌ Database not found at: {self.db_path}")
                print("Run the import_data.py script first to create the database.")
                return False
                
            # Use check_same_thread=False for Flask threading
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Enable dict-like access
            
            # Test connection
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM characters")
            result = cursor.fetchone()
            print(f"✅ Connected to Batman database with {result['total']} characters")
            return True
            
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False
    
    def process_query(self, user_input: str) -> BatmanResponse:
        """
        Main query processing function.
        
        Args:
            user_input: User's question or query
            
        Returns:
            BatmanResponse with answer and metadata
        """
        if not self.conn:
            return BatmanResponse(
                answer="Database connection error. Please check your setup.",
                confidence=0.0,
                source_entities=[],
                query_type="error"
            )
        
        # Clean and prepare input
        query = self._clean_input(user_input)
        
        # Add to conversation history
        self.conversation_history.append({"role": "user", "content": query})
        
        # First, try relationship processor for weapons, defenses, features, etc.
        if self.relationship_processor:
            relationship_result = self.relationship_processor.process_relationship_query(query)
            if relationship_result:
                return self._handle_relationship_processor_result(relationship_result)
        
        # Then try intelligent search for complex queries
        if self.search_engine:
            # Check for multi-entity queries (comparisons)
            multi_result = self.search_engine.search_multi_entity(query)
            if multi_result['type'] == 'comparison':
                return self._handle_comparison_result(multi_result)
            
            # Check for relationship queries (where does X park, who uses Y)
            relationship_result = self.search_engine.search_by_relationship(query)
            if relationship_result:
                return self._handle_relationship_result(relationship_result, query)
        
        # Then try advanced conversation intelligence
        if self.conversation_intelligence:
            # Try comparative query
            comp_result = self.conversation_intelligence.handle_comparative_query(query)
            if comp_result:
                return BatmanResponse(
                    answer=comp_result.explanation,
                    confidence=comp_result.confidence,
                    source_entities=[comp_result.entity1['id'], comp_result.entity2['id']],
                    query_type="comparative_analysis"
                )
            
            # Try relationship query
            rel_result = self.conversation_intelligence.handle_relationship_query(query)
            if rel_result:
                source_ids = [rel_result.primary_entity['id']] + [e['id'] for e in rel_result.related_entities[:3]]
                return BatmanResponse(
                    answer=rel_result.explanation,
                    confidence=rel_result.confidence,
                    source_entities=source_ids,
                    query_type="relationship_query"
                )
            
            # Try multi-entity query
            multi_result = self.conversation_intelligence.handle_multi_entity_query(query)
            if multi_result:
                entities_text = ""
                if multi_result['entities']:
                    entity_names = [e['name'] for e in multi_result['entities'][:5]]
                    entities_text = f" Here are some examples: {', '.join(entity_names)}"
                    if multi_result['total_count'] > 5:
                        entities_text += f" and {multi_result['total_count'] - 5} others"
                    entities_text += "."
                
                answer = multi_result['explanation'] + entities_text
                source_ids = [e['id'] for e in multi_result['entities'][:5]]
                
                return BatmanResponse(
                    answer=answer,
                    confidence=0.8,
                    source_entities=source_ids,
                    query_type="multi_entity_query"
                )
        
        # Determine query type and process normally
        query_type = self._classify_query(query)
        
        if query_type == "character_lookup":
            response = self._handle_character_query(query)
        elif query_type == "sidekick_lookup":
            response = self._handle_sidekick_query(query)
        elif query_type == "vehicle_lookup":
            response = self._handle_vehicle_query(query)
        elif query_type == "location_lookup":
            response = self._handle_location_query(query)
        elif query_type == "relationship_query":
            response = self._handle_relationship_query(query)
        elif query_type == "general_search":
            response = self._handle_general_search(query)
        else:
            response = self._handle_unknown_query(query)
        
        # Add response to conversation history
        self.conversation_history.append({"role": "assistant", "content": response.answer})
        
        return response
    
    def _clean_entity_name(self, name: str) -> str:
        """Clean entity names for display (consistent with response generator)."""
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
    
    def _improve_description_formatting(self, description: str) -> str:
        """Improve description formatting for better readability."""
        if not description:
            return ""
        
        # Fix missing spaces after periods
        cleaned = re.sub(r'\.([A-Z])', r'. \1', description)
        
        # Fix capitalization issues like "BatmobilesareBatman's" 
        # Add space before capital letters that follow lowercase letters
        cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)
        
        # Fix common concatenations with more comprehensive patterns
        concatenation_fixes = {
            'theBatmobile': 'the Batmobile',
            'theJoker': 'the Joker', 
            'theBatman': 'the Batman',
            'theBatcave': 'the Batcave',
            'theRiddler': 'the Riddler',
            'thePenguin': 'the Penguin',
            'theUnited': 'the United',
            'asArkham': 'as Arkham',
            'ofGotham': 'of Gotham',
            'byBatman': 'by Batman',
            'andBatman': 'and Batman',
            'forBatman': 'for Batman',
            'asBatman': 'as Batman',
            'bythe': 'by the',
            'ofthe': 'of the',
            'inthe': 'in the',
            'onthe': 'on the',
            'atthe': 'at the',
            'Batman s': "Batman's",
            'Joker s': "Joker's"
        }
        
        for incorrect, correct in concatenation_fixes.items():
            cleaned = cleaned.replace(incorrect, correct)
        
        # Fix remaining common word concatenations with regex
        cleaned = re.sub(r'([a-z])(Batman|Joker|Robin|Gotham|Wayne)', r'\1 \2', cleaned)
        cleaned = re.sub(r'(Batman|Joker|Robin|Gotham|Wayne)([a-z])', r'\1 \2', cleaned)
        
        return cleaned
    
    def _check_batman_scope(self, query: str) -> Dict[str, Any]:
        """Check if a query is asking about non-Batman entities and should be rejected."""
        query_lower = query.lower()
        
        # Non-Batman superhero characters that should be rejected
        non_batman_heroes = [
            'superman', 'clark kent', 'kal-el',
            'wonder woman', 'diana prince',
            'green lantern', 'hal jordan', 'john stewart', 'kyle rayner',
            'flash', 'barry allen', 'wally west',
            'aquaman', 'arthur curry',
            'green arrow', 'oliver queen',
            'martian manhunter', 'j\'onn j\'onzz',
            'cyborg', 'victor stone',
            'shazam', 'billy batson',
            'hawkman', 'carter hall',
            'atom', 'ray palmer',
            'firestorm', 'ronnie raymond'
        ]
        
        # Non-Batman locations/organizations
        non_batman_entities = [
            'metropolis', 'smallville', 'daily planet',
            'lexcorp', 'lex corp', 'luthorcorp',
            'themyscira', 'paradise island',
            'coast city', 'central city', 'keystone city',
            'atlantis', 'star city',
            'mount justice', 'watchtower',
            'fortress of solitude',
            'hall of justice'
        ]
        
        # Check for explicit non-Batman entities
        for entity in non_batman_heroes + non_batman_entities:
            if entity in query_lower:
                # Check if it's also asking about Batman (comparative query)
                batman_terms = ['batman', 'bruce wayne', 'dark knight', 'gotham', 'bat-family']
                has_batman = any(term in query_lower for term in batman_terms)
                
                if not has_batman:
                    return {
                        'is_batman_related': False,
                        'message': f"I'm a Batman universe specialist. My expertise is focused on Batman, Gotham City, and the extended Bat-Family. For information about {entity.title()}, you'd need a more general DC Comics database."
                    }
        
        # Check for vehicle/equipment queries about non-Batman characters
        vehicle_patterns = ['what does', 'what vehicles', 'what cars', 'drives', 'rides']
        equipment_patterns = ['gadgets', 'weapons', 'equipment', 'gear', 'tools']
        
        if any(pattern in query_lower for pattern in vehicle_patterns + equipment_patterns):
            for hero in non_batman_heroes:
                if hero in query_lower:
                    return {
                        'is_batman_related': False,
                        'message': f"I specialize in Batman's vehicles and technology. For information about {hero.title()}'s vehicles or equipment, you'd need a broader DC Comics database."
                    }
        
        # Query appears to be Batman-related or general enough to process
        return {
            'is_batman_related': True,
            'message': ''
        }
    
    def _handle_contextual_followup(self, query: str) -> BatmanResponse:
        """Handle contextual follow-up queries using conversation history."""
        # Try to extract entity from recent conversation history for context
        if hasattr(self, 'conversation_history') and self.conversation_history:
            for history_item in reversed(self.conversation_history[-6:]):  # Last 3 exchanges
                content = history_item.get('content', '')
                
                # Extract entity mentions from previous responses
                entity_patterns = [
                    r'\*\*([^*]+)\*\*',  # **Entity Name**
                    r'(?:The\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:is|was|has)',  # "The Batplane is"
                    r'(?:analyzing|discussing)\s+(?:the\s+)?([A-Za-z]+(?:\s+[A-Za-z]+)?)',  # "analyzing the batplane"
                ]
                
                for pattern in entity_patterns:
                    match = re.search(pattern, content, re.IGNORECASE)
                    if match:
                        entity_name = match.group(1).strip()
                        # Create resolved query by replacing pronoun with entity
                        resolved_query = re.sub(r'\b(?:it|that|this)\b', entity_name, query, flags=re.IGNORECASE)
                        if resolved_query != query:
                            # Process the resolved query
                            return self.process_query(resolved_query)
        
        # If context resolution fails, return a clarification request
        return BatmanResponse(
            answer="I need more context. What specific entity are you referring to?",
            confidence=0.0,
            source_entities=[],
            query_type="clarification_needed"
        )
    
    def _clean_input(self, user_input: str) -> str:
        """Clean and normalize user input."""
        # Remove extra whitespace and convert to title case for names
        cleaned = user_input.strip()
        return cleaned
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query to determine processing approach."""
        query_lower = query.lower()
        
        # Define keywords with priority order - specific entities first
        vehicle_keywords = ["batmobile", "batwing", "batboat", "batcycle", "vehicle", "car", "plane", "boat", "drive", "drives"]
        location_keywords = ["gotham", "arkham", "wayne manor", "batcave", "where is", "location", "place"]
        relationship_keywords = ["relationship", "ally", "enemy", "friend", "vs", "versus", "against"]
        sidekick_keywords = ["sidekick", "partner", "robin", "assistant", "helper"]
        character_keywords = ["who is", "tell me about", "what about", "character", "person"]
        
        # Check in priority order - specific entities before generic phrases
        if any(keyword in query_lower for keyword in vehicle_keywords):
            return "vehicle_lookup"
        elif any(keyword in query_lower for keyword in location_keywords):
            return "location_lookup"
        elif any(keyword in query_lower for keyword in relationship_keywords):
            return "relationship_query"
        elif any(keyword in query_lower for keyword in sidekick_keywords):
            return "sidekick_lookup"
        elif any(keyword in query_lower for keyword in character_keywords):
            return "character_lookup"
        else:
            return "general_search"
    
    def _handle_character_query(self, query: str) -> BatmanResponse:
        """Handle character-specific queries using advanced processing."""
        # Check Batman scope first
        scope_check = self._check_batman_scope(query)
        if not scope_check['is_batman_related']:
            return BatmanResponse(
                answer=scope_check['message'],
                confidence=0.0,
                source_entities=[],
                query_type="out_of_scope"
            )
        
        if not self.query_processor:
            return self._handle_character_query_fallback(query)
        
        # Check for commonly ambiguous character names that should show options
        ambiguous_names = ['robin', 'batgirl', 'flash', 'green lantern', 'joker', 'batman']
        query_clean = query.lower().strip()
        
        # Try context-aware resolution first for pronoun queries
        if any(pronoun in query_clean for pronoun in ['it', 'that', 'this', 'them', 'him', 'her']):
            # Check if we have context that could resolve this
            if hasattr(self, 'conversation_history') and self.conversation_history:
                # Look for recently mentioned entities that could resolve pronouns
                for history_item in reversed(self.conversation_history[-4:]):  # Last 2 exchanges
                    if history_item.get('role') == 'assistant' and 'weapons' in history_item.get('content', '').lower():
                        # If recent response was about weapons, this might be a follow-up
                        return self._handle_contextual_followup(query)
        
        # Force ambiguous handling for common ambiguous names
        if any(ambiguous_name in query_clean for ambiguous_name in ambiguous_names):
            ambiguous_result = self.query_processor.handle_ambiguous_query(query)
            if ambiguous_result['type'] == 'multiple_matches':
                char_matches = [m for m in ambiguous_result['matches'] if m.entity_type == 'characters']
                if len(char_matches) > 1:  # More than one character match
                    numbered_options = []
                    for i, match in enumerate(char_matches[:5], 1):
                        clean_name = match.name.replace('_', ' ')
                        confidence_pct = int(match.confidence * 100)
                        numbered_options.append(f"{i}. {clean_name} ({match.entity_type}) - {confidence_pct}% match")
                    
                    answer = self.templates["multiple_matches"].format(
                        query=query,
                        matches="\n".join(numbered_options)
                    )
                    return BatmanResponse(
                        answer=answer,
                        confidence=0.5,
                        source_entities=[],
                        query_type="character_lookup",
                        suggestions=[m.name for m in char_matches[:5]]
                    )
        
        # Use advanced query processor for better matching
        match = self.query_processor.find_best_entity_match(query, entity_type='characters')
        
        if match and match.confidence > 0.6:
            # Get full character data
            character = self._get_entity_by_id(match.entity_id, 'characters')
            if character and self.response_generator:
                # Use enhanced response generator
                context = ResponseContext(
                    entity=character,
                    entity_type='characters',
                    query_intent='character_info',
                    user_query=query,
                    confidence=match.confidence
                )
                
                enhanced_answer = self.response_generator.generate_response(context)
                
                return BatmanResponse(
                    answer=enhanced_answer,
                    confidence=match.confidence,
                    source_entities=[match.entity_id],
                    query_type="character_lookup"
                )
            elif character:
                # Fallback to basic template
                answer = self.templates["character_info"].format(
                    name=match.name,
                    description=character["description"][:3000] + "..." if len(character["description"]) > 3000 else character["description"]
                )
                
                return BatmanResponse(
                    answer=answer,
                    confidence=match.confidence,
                    source_entities=[match.entity_id],
                    query_type="character_lookup"
                )
        
        # Handle ambiguous results
        ambiguous_result = self.query_processor.handle_ambiguous_query(query)
        
        if ambiguous_result['type'] == 'multiple_matches':
            # Filter for characters only
            char_matches = [m for m in ambiguous_result['matches'] if m.entity_type == 'characters']
            if char_matches:
                # Create numbered list with entity types
                numbered_options = []
                for i, match in enumerate(char_matches[:5], 1):
                    clean_name = match.name.replace('_', ' ')
                    confidence_pct = int(match.confidence * 100)
                    numbered_options.append(f"{i}. {clean_name} ({match.entity_type}) - {confidence_pct}% match")
                
                answer = self.templates["multiple_matches"].format(
                    query=query,
                    matches="\n".join(numbered_options)
                )
                return BatmanResponse(
                    answer=answer,
                    confidence=0.5,
                    source_entities=[],
                    query_type="character_lookup",
                    suggestions=[m.name for m in char_matches[:5]]
                )
        
        return BatmanResponse(
            answer=self.templates["not_found"].format(query=query),
            confidence=0.0,
            source_entities=[],
            query_type="character_lookup"
        )
    
    def _handle_sidekick_query(self, query: str) -> BatmanResponse:
        """Handle sidekick-specific queries by focusing on Robin variants."""
        # For sidekick queries, directly search for Robin variants
        robin_query = "robin"
        
        if not self.query_processor:
            return self._handle_character_query_fallback(robin_query)
        
        # Force ambiguous handling for Robin to show all variants
        ambiguous_result = self.query_processor.handle_ambiguous_query(robin_query)
        if ambiguous_result['type'] == 'multiple_matches':
            char_matches = [m for m in ambiguous_result['matches'] if m.entity_type == 'characters' and 'robin' in m.name.lower()]
            if len(char_matches) > 1:
                numbered_options = []
                for i, match in enumerate(char_matches[:5], 1):
                    clean_name = match.name.replace('_', ' ')
                    confidence_pct = int(match.confidence * 100)
                    numbered_options.append(f"{i}. {clean_name} ({match.entity_type}) - {confidence_pct}% match")
                
                answer = f"Batman's main sidekicks are the various Robins. Please select which one you'd like to learn about:\n\n{chr(10).join(numbered_options)}\n\nType the number of your choice, or be more specific with your question."
                
                return BatmanResponse(
                    answer=answer,
                    confidence=0.5,
                    source_entities=[],
                    query_type="sidekick_lookup",
                    suggestions=[m.name for m in char_matches[:5]]
                )
        
        # Fallback to regular character query
        return self._handle_character_query(robin_query)
    
    def _handle_vehicle_query(self, query: str) -> BatmanResponse:
        """Handle vehicle-specific queries using advanced processing."""
        # Check Batman scope first
        scope_check = self._check_batman_scope(query)
        if not scope_check['is_batman_related']:
            return BatmanResponse(
                answer=scope_check['message'],
                confidence=0.0,
                source_entities=[],
                query_type="out_of_scope"
            )
        
        if not self.query_processor:
            return self._handle_vehicle_query_fallback(query)
        
        # Use smart vehicle matching for character-related queries
        query_lower = query.lower()
        if any(pattern in query_lower for pattern in ['what does', 'what do', 'drive', 'car']):
            match = self.query_processor.find_best_vehicle_match(query)
        else:
            # Use regular entity matching for other vehicle queries
            match = self.query_processor.find_best_entity_match(query, entity_type='vehicles')
        
        # Use lower confidence threshold for character vehicle matches since they're more specific
        confidence_threshold = 0.4 if (match and match.match_type == 'character_vehicle') else 0.6
        
        if match and match.confidence > confidence_threshold:
            vehicle = self._get_entity_by_id(match.entity_id, 'vehicles')
            if vehicle and self.response_generator:
                # Use enhanced response generator
                context = ResponseContext(
                    entity=vehicle,
                    entity_type='vehicles',
                    query_intent='vehicle_info',
                    user_query=query,
                    confidence=match.confidence
                )
                
                enhanced_answer = self.response_generator.generate_response(context)
                
                return BatmanResponse(
                    answer=enhanced_answer,
                    confidence=match.confidence,
                    source_entities=[match.entity_id],
                    query_type="vehicle_lookup"
                )
            elif vehicle:
                # Fallback to basic template
                answer = self.templates["vehicle_info"].format(
                    vehicle=match.name,
                    description=vehicle["description"][:3000] + "..." if len(vehicle["description"]) > 3000 else vehicle["description"]
                )
                
                return BatmanResponse(
                    answer=answer,
                    confidence=match.confidence,
                    source_entities=[match.entity_id],
                    query_type="vehicle_lookup"
                )
        
        return BatmanResponse(
            answer=self.templates["not_found"].format(query=query),
            confidence=0.0,
            source_entities=[],
            query_type="vehicle_lookup"
        )
    
    def _handle_location_query(self, query: str) -> BatmanResponse:
        """Handle location-specific queries using advanced processing."""
        if not self.query_processor:
            return self._handle_location_query_fallback(query)
        
        # Use advanced query processor
        match = self.query_processor.find_best_entity_match(query, entity_type='locations')
        
        if match and match.confidence > 0.6:
            location = self._get_entity_by_id(match.entity_id, 'locations')
            if location and self.response_generator:
                # Use enhanced response generator
                context = ResponseContext(
                    entity=location,
                    entity_type='locations',
                    query_intent='location_info',
                    user_query=query,
                    confidence=match.confidence
                )
                
                enhanced_answer = self.response_generator.generate_response(context)
                
                return BatmanResponse(
                    answer=enhanced_answer,
                    confidence=match.confidence,
                    source_entities=[match.entity_id],
                    query_type="location_lookup"
                )
            elif location:
                # Fallback to basic template
                answer = self.templates["location_info"].format(
                    location=match.name,
                    description=location["description"][:3000] + "..." if len(location["description"]) > 3000 else location["description"]
                )
                
                return BatmanResponse(
                    answer=answer,
                    confidence=match.confidence,
                    source_entities=[match.entity_id],
                    query_type="location_lookup"
                )
        
        return BatmanResponse(
            answer=self.templates["not_found"].format(query=query),
            confidence=0.0,
            source_entities=[],
            query_type="location_lookup"
        )
    
    def _handle_relationship_query(self, query: str) -> BatmanResponse:
        """Handle relationship queries between characters."""
        if self.conversation_intelligence:
            rel_result = self.conversation_intelligence.handle_relationship_query(query)
            if rel_result:
                source_ids = [rel_result.primary_entity['id']] + [e['id'] for e in rel_result.related_entities[:3]]
                return BatmanResponse(
                    answer=rel_result.explanation,
                    confidence=rel_result.confidence,
                    source_entities=source_ids,
                    query_type="relationship_query"
                )
        
        # Fallback for unknown relationships
        return BatmanResponse(
            answer="I don't have specific relationship information for that query, but I can help with general character information.",
            confidence=0.0,
            source_entities=[],
            query_type="relationship_query"
        )
    
    def _handle_general_search(self, query: str) -> BatmanResponse:
        """Handle general search across all entities using advanced processor."""
        # First check if query is about non-Batman entities
        scope_check = self._check_batman_scope(query)
        if not scope_check['is_batman_related']:
            return BatmanResponse(
                answer=scope_check['message'],
                confidence=0.0,
                source_entities=[],
                query_type="out_of_scope"
            )
        
        if not self.query_processor:
            return self._handle_general_search_fallback(query)
        
        # Try to find best match across all entity types
        best_match = self.query_processor.find_best_entity_match(query, threshold=60)
        
        if best_match and best_match.confidence > 0.6:
            # Get entity data and return appropriate response
            entity = self._get_entity_by_id(best_match.entity_id, best_match.entity_type)
            if entity:
                # Format response based on entity type
                if best_match.entity_type == 'characters':
                    template = self.templates["character_info"]
                elif best_match.entity_type == 'vehicles':
                    template = self.templates["vehicle_info"]
                elif best_match.entity_type == 'locations':
                    template = self.templates["location_info"]
                elif best_match.entity_type == 'organizations':
                    template = self.templates["organization_info"]
                elif best_match.entity_type == 'storylines':
                    template = self.templates["storyline_info"]
                else:
                    template = "I found information about {name}: {description}"
                
                # Replace placeholders based on entity type
                if best_match.entity_type == 'characters':
                    answer = template.format(name=best_match.name, description=entity["description"][:3000])
                elif best_match.entity_type == 'vehicles':
                    answer = template.format(vehicle=best_match.name, description=entity["description"][:3000])
                elif best_match.entity_type == 'locations':
                    answer = template.format(location=best_match.name, description=entity["description"][:3000])
                elif best_match.entity_type == 'organizations':
                    answer = template.format(organization=best_match.name, description=entity["description"][:3000])
                elif best_match.entity_type == 'storylines':
                    answer = template.format(name=best_match.name, description=entity["description"][:3000])
                else:
                    answer = template.format(name=best_match.name, description=entity["description"][:3000])
                
                return BatmanResponse(
                    answer=answer + ("..." if len(entity["description"]) > 3000 else ""),
                    confidence=best_match.confidence,
                    source_entities=[best_match.entity_id],
                    query_type="general_search"
                )
        
        # Handle ambiguous results  
        ambiguous_result = self.query_processor.handle_ambiguous_query(query)
        
        if ambiguous_result['type'] == 'multiple_matches':
            matches = ambiguous_result['matches'][:5]  # Top 5 matches
            # Create numbered list with entity types and confidence
            numbered_options = []
            for i, match in enumerate(matches, 1):
                clean_name = match.name.replace('_', ' ')
                confidence_pct = int(match.confidence * 100)
                numbered_options.append(f"{i}. {clean_name} ({match.entity_type}) - {confidence_pct}% match")
            
            answer = self.templates["multiple_matches"].format(
                query=query,
                matches="\n".join(numbered_options)
            )
            return BatmanResponse(
                answer=answer,
                confidence=0.5,
                source_entities=[],
                query_type="general_search",
                suggestions=[m.name for m in matches]
            )
        
        return BatmanResponse(
            answer="I couldn't find any Batman universe information matching your query. Try asking about specific characters, vehicles, or locations.",
            confidence=0.0,
            source_entities=[],
            query_type="general_search"
        )
    
    def _handle_unknown_query(self, query: str) -> BatmanResponse:
        """Handle queries that don't fit known patterns."""
        return BatmanResponse(
            answer="I'm the ultimate Batman expert, but I'm not sure how to help with that query. Try asking about Batman characters, vehicles, locations, or storylines!",
            confidence=0.0,
            source_entities=[],
            query_type="unknown"
        )
    
    def _extract_entity_name(self, query: str) -> str:
        """Extract entity name from user query."""
        # Simple extraction - remove common query words while preserving entity names
        stop_phrases = ["who is ", "what is ", "tell me about ", "what about ", "where is "]
        
        query_clean = query
        for phrase in stop_phrases:
            if query_clean.lower().startswith(phrase):
                query_clean = query_clean[len(phrase):]
                break
        
        # Clean up punctuation but preserve the name
        query_clean = query_clean.strip().replace("?", "").replace(".", "")
        return query_clean.strip()
    
    def _find_character(self, name: str) -> Optional[Dict]:
        """Find character by name (exact or fuzzy match)."""
        try:
            cursor = self.conn.cursor()
            
            # Try exact match first
            cursor.execute("""
                SELECT * FROM characters 
                WHERE LOWER(name) = LOWER(?) 
                LIMIT 1
            """, (name,))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            
            # Try partial match (for "the Joker" -> "Joker")
            cursor.execute("""
                SELECT * FROM characters 
                WHERE LOWER(name) LIKE LOWER(?) 
                LIMIT 1
            """, (f"%{name.replace('the ', '')}%",))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            
            # Try alias match
            cursor.execute("""
                SELECT c.* FROM characters c
                JOIN character_aliases ca ON c.id = ca.character_id
                WHERE LOWER(ca.alias) = LOWER(?)
                LIMIT 1
            """, (name,))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            
            return None
            
        except Exception as e:
            print(f"Error finding character: {e}")
            return None
    
    def _find_vehicle(self, name: str) -> Optional[Dict]:
        """Find vehicle by name."""
        try:
            cursor = self.conn.cursor()
            
            # Try exact match
            cursor.execute("""
                SELECT * FROM vehicles 
                WHERE LOWER(name) = LOWER(?) 
                LIMIT 1
            """, (name,))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            
            # Try partial match (for "the Batmobile" -> "Batmobile")
            cursor.execute("""
                SELECT * FROM vehicles 
                WHERE LOWER(name) LIKE LOWER(?) 
                LIMIT 1
            """, (f"%{name.replace('the ', '')}%",))
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            print(f"Error finding vehicle: {e}")
            return None
    
    def _find_location(self, name: str) -> Optional[Dict]:
        """Find location by name."""
        try:
            cursor = self.conn.cursor()
            
            # Try exact match
            cursor.execute("""
                SELECT * FROM locations 
                WHERE LOWER(name) = LOWER(?) 
                LIMIT 1
            """, (name,))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            
            # Try partial match
            cursor.execute("""
                SELECT * FROM locations 
                WHERE LOWER(name) LIKE LOWER(?) 
                LIMIT 1
            """, (f"%{name.replace('the ', '')}%",))
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            print(f"Error finding location: {e}")
            return None
    
    def _get_character_suggestions(self, name: str, limit: int = 5) -> List[Dict]:
        """Get character name suggestions using fuzzy matching."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT name, id FROM characters 
                WHERE name LIKE ? 
                ORDER BY name 
                LIMIT ?
            """, (f"%{name}%", limit))
            
            results = cursor.fetchall()
            return [dict(result) for result in results]
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []
    
    def _full_text_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Perform full-text search across all entities."""
        results = []
        
        try:
            cursor = self.conn.cursor()
            
            # Search characters (fallback to regular search if FTS fails)
            try:
                cursor.execute("""
                    SELECT 'character' as entity_type, id, name, description
                    FROM characters_fts 
                    WHERE characters_fts MATCH ? 
                    LIMIT ?
                """, (query, limit))
                
                for row in cursor.fetchall():
                    results.append(dict(row))
            except:
                # Fallback to LIKE search
                cursor.execute("""
                    SELECT 'character' as entity_type, id, name, description
                    FROM characters 
                    WHERE name LIKE ? OR description LIKE ?
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                
                for row in cursor.fetchall():
                    results.append(dict(row))
            
            # Search vehicles
            try:
                cursor.execute("""
                    SELECT 'vehicle' as entity_type, id, name, description
                    FROM vehicles_fts 
                    WHERE vehicles_fts MATCH ? 
                    LIMIT ?
                """, (query, limit))
                
                for row in cursor.fetchall():
                    results.append(dict(row))
            except:
                cursor.execute("""
                    SELECT 'vehicle' as entity_type, id, name, description
                    FROM vehicles 
                    WHERE name LIKE ? OR description LIKE ?
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                
                for row in cursor.fetchall():
                    results.append(dict(row))
            
            # Search locations
            try:
                cursor.execute("""
                    SELECT 'location' as entity_type, id, name, description
                    FROM locations_fts 
                    WHERE locations_fts MATCH ? 
                    LIMIT ?
                """, (query, limit))
                
                for row in cursor.fetchall():
                    results.append(dict(row))
            except:
                cursor.execute("""
                    SELECT 'location' as entity_type, id, name, description
                    FROM locations 
                    WHERE name LIKE ? OR description LIKE ?
                    LIMIT ?
                """, (f"%{query}%", f"%{query}%", limit))
                
                for row in cursor.fetchall():
                    results.append(dict(row))
            
            return results
            
        except Exception as e:
            print(f"Error in full-text search: {e}")
            return []
    
    def _get_entity_by_id(self, entity_id: str, entity_type: str) -> Optional[Dict]:
        """Get entity by ID from database."""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"""
                SELECT * FROM {entity_type} 
                WHERE id = ? 
                LIMIT 1
            """, (entity_id,))
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
        except Exception as e:
            print(f"Error getting entity by ID: {e}")
            return None
    
    def _handle_character_query_fallback(self, query: str) -> BatmanResponse:
        """Fallback character query handler."""
        character_name = self._extract_entity_name(query)
        character = self._find_character(character_name)
        
        if character:
            answer = self.templates["character_info"].format(
                name=character["name"],
                description=character["description"][:3000] + "..." if len(character["description"]) > 3000 else character["description"]
            )
            return BatmanResponse(
                answer=answer,
                confidence=0.9,
                source_entities=[character["id"]],
                query_type="character_lookup"
            )
        
        return BatmanResponse(
            answer=self.templates["not_found"].format(query=character_name),
            confidence=0.0,
            source_entities=[],
            query_type="character_lookup"
        )
    
    def _handle_vehicle_query_fallback(self, query: str) -> BatmanResponse:
        """Fallback vehicle query handler."""
        vehicle_name = self._extract_entity_name(query)
        vehicle = self._find_vehicle(vehicle_name)
        
        if vehicle:
            answer = self.templates["vehicle_info"].format(
                vehicle=vehicle["name"],
                description=vehicle["description"][:3000] + "..." if len(vehicle["description"]) > 3000 else vehicle["description"]
            )
            return BatmanResponse(
                answer=answer,
                confidence=0.9,
                source_entities=[vehicle["id"]],
                query_type="vehicle_lookup"
            )
        
        return BatmanResponse(
            answer=self.templates["not_found"].format(query=vehicle_name),
            confidence=0.0,
            source_entities=[],
            query_type="vehicle_lookup"
        )
    
    def _handle_location_query_fallback(self, query: str) -> BatmanResponse:
        """Fallback location query handler."""
        location_name = self._extract_entity_name(query)
        location = self._find_location(location_name)
        
        if location:
            answer = self.templates["location_info"].format(
                location=location["name"],
                description=location["description"][:3000] + "..." if len(location["description"]) > 3000 else location["description"]
            )
            return BatmanResponse(
                answer=answer,
                confidence=0.9,
                source_entities=[location["id"]],
                query_type="location_lookup"
            )
        
        return BatmanResponse(
            answer=self.templates["not_found"].format(query=location_name),
            confidence=0.0,
            source_entities=[],
            query_type="location_lookup"
        )
    
    def _handle_general_search_fallback(self, query: str) -> BatmanResponse:
        """Fallback general search handler."""
        # Check Batman scope first for fallback too
        scope_check = self._check_batman_scope(query)
        if not scope_check['is_batman_related']:
            return BatmanResponse(
                answer=scope_check['message'],
                confidence=0.0,
                source_entities=[],
                query_type="out_of_scope"
            )
        
        results = self._full_text_search(query)
        
        if results:
            best_match = results[0]
            entity_type = best_match["entity_type"]
            
            if entity_type == "character":
                return self._handle_character_query(best_match["name"])
            elif entity_type == "vehicle":
                return self._handle_vehicle_query(best_match["name"])
            elif entity_type == "location":
                return self._handle_location_query(best_match["name"])
            else:
                answer = f"I found information about {best_match['name']}: {best_match['description'][:300]}..."
                return BatmanResponse(
                    answer=answer,
                    confidence=0.7,
                    source_entities=[best_match["id"]],
                    query_type="general_search"
                )
        
        return BatmanResponse(
            answer="I couldn't find any Batman universe information matching your query. Try asking about specific characters, vehicles, or locations.",
            confidence=0.0,
            source_entities=[],
            query_type="general_search"
        )
    
    def get_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        if not self.conn:
            return {}
        
        try:
            cursor = self.conn.cursor()
            stats = {}
            
            # Count entities
            for table in ["characters", "vehicles", "locations", "storylines", "organizations"]:
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                result = cursor.fetchone()
                stats[table] = result["count"]
            
            return stats
            
        except Exception as e:
            print(f"Error getting stats: {e}")
            return {}
    
    def get_entity_info_direct(self, entity_name: str) -> BatmanResponse:
        """
        Get entity information directly by database name (e.g., 'Robin_(Tim_Drake)').
        
        Args:
            entity_name: The exact entity name as stored in the database
            
        Returns:
            BatmanResponse with detailed entity information
        """
        if not self.conn:
            return BatmanResponse(
                answer="Database connection error. Please check your setup.",
                confidence=0.0,
                source_entities=[],
                query_type="error"
            )
        
        try:
            cursor = self.conn.cursor()
            
            # Try each table to find the entity
            tables = ['characters', 'vehicles', 'locations', 'storylines', 'organizations']
            entity_found = None
            entity_type = None
            
            for table in tables:
                cursor.execute(f"SELECT * FROM {table} WHERE name = ?", (entity_name,))
                result = cursor.fetchone()
                if result:
                    entity_found = dict(result)
                    entity_type = table
                    break
            
            if not entity_found:
                return BatmanResponse(
                    answer=f"Entity '{entity_name}' not found in the database.",
                    confidence=0.0,
                    source_entities=[],
                    query_type="not_found"
                )
            
            # Generate detailed response using the response generator
            if self.response_generator:
                context = ResponseContext(
                    entity=entity_found,
                    entity_type=entity_type,
                    query_intent="detailed_info",
                    user_query=f"Tell me about {entity_name.replace('_', ' ')}",
                    confidence=1.0
                )
                detailed_response = self.response_generator.generate_response(context)
                
                return BatmanResponse(
                    answer=detailed_response,
                    confidence=1.0,
                    source_entities=[entity_name],
                    query_type=entity_type
                )
            else:
                # Fallback simple response
                name_display = entity_name.replace('_', ' ')
                description = entity_found.get('description', 'No description available.')
                
                return BatmanResponse(
                    answer=f"{name_display}: {description}",
                    confidence=1.0,
                    source_entities=[entity_name],
                    query_type=entity_type
                )
                
        except Exception as e:
            return BatmanResponse(
                answer=f"Error retrieving entity information: {e}",
                confidence=0.0,
                source_entities=[],
                query_type="error"
            )

    def _handle_comparison_result(self, comparison_result: Dict[str, Any]) -> BatmanResponse:
        """Handle intelligent search comparison results."""
        entity1 = comparison_result['entity1']
        entity2 = comparison_result['entity2']
        comparison_data = comparison_result['comparison_data']
        
        # Build comprehensive comparison response
        response_parts = []
        response_parts.append(f"Comparing {entity1.name.replace('_', ' ')} and {entity2.name.replace('_', ' ')}:\n")
        
        # Add basic descriptions
        response_parts.append(f"**{entity1.name.replace('_', ' ')}**: {entity1.description[:200]}...")
        response_parts.append(f"**{entity2.name.replace('_', ' ')}**: {entity2.description[:200]}...")
        
        # Add specific comparisons based on type
        if comparison_data.get('comparison_type') == 'vehicles':
            specs1 = comparison_data.get('specifications_comparison', {}).get(entity1.entity_id, {})
            specs2 = comparison_data.get('specifications_comparison', {}).get(entity2.entity_id, {})
            weapons1 = comparison_data.get('weapons_comparison', {}).get(entity1.entity_id, [])
            weapons2 = comparison_data.get('weapons_comparison', {}).get(entity2.entity_id, [])
            
            if specs1 or specs2:
                response_parts.append("\n**Specifications:**")
                if specs1.get('max_speed'): response_parts.append(f"- {entity1.name} max speed: {specs1['max_speed']}")
                if specs2.get('max_speed'): response_parts.append(f"- {entity2.name} max speed: {specs2['max_speed']}")
            
            if weapons1 or weapons2:
                response_parts.append("\n**Weapons:**")
                if weapons1: response_parts.append(f"- {entity1.name}: {', '.join(weapons1)}")
                if weapons2: response_parts.append(f"- {entity2.name}: {', '.join(weapons2)}")
        
        answer = "\n".join(response_parts)
        
        return BatmanResponse(
            answer=answer,
            confidence=0.9,
            source_entities=[entity1.entity_id, entity2.entity_id],
            query_type="comparison"
        )

    def _handle_relationship_result(self, result, original_query: str) -> BatmanResponse:
        """Handle intelligent search relationship results."""
        context_prefix = ""
        
        if result.match_type == 'relationship':
            context_prefix = f"Based on database relationships: {result.context}\n\n"
        elif result.match_type == 'inference':
            context_prefix = f"Based on logical inference: {result.context}\n\n"
        
        # Generate detailed response about the found entity
        if self.response_generator:
            response_context = ResponseContext(
                entity={'id': result.entity_id, 'name': result.name, 'description': result.description},
                entity_type=result.entity_type,
                query_intent="location_info" if result.entity_type == 'locations' else "character_info",
                user_query=original_query,
                confidence=result.confidence
            )
            detailed_response = self.response_generator.generate_response(response_context)
            answer = context_prefix + detailed_response
        else:
            answer = context_prefix + f"{result.name.replace('_', ' ')}: {result.description}"
        
        return BatmanResponse(
            answer=answer,
            confidence=result.confidence,
            source_entities=[result.entity_id],
            query_type=result.entity_type
        )

    def _handle_relationship_processor_result(self, result) -> BatmanResponse:
        """Handle relationship processor results (weapons, defenses, features, etc.)."""
        
        # Build comprehensive response based on relationship type
        response_parts = []
        
        if result.query_type == 'weapons':
            response_parts.append(f"🔫 **WEAPONS ANALYSIS - {self._clean_entity_name(result.primary_entity['name'])}**")
            response_parts.append(self._improve_description_formatting(result.explanation))
            
            if result.related_data:
                response_parts.append("\n**Detailed Arsenal:**")
                for weapon_data in result.related_data:
                    response_parts.append(f"• {weapon_data['weapon'].title()}")
        
        elif result.query_type == 'defenses':
            response_parts.append(f"🛡️ **DEFENSIVE SYSTEMS - {self._clean_entity_name(result.primary_entity['name'])}**")
            response_parts.append(self._improve_description_formatting(result.explanation))
            
            if result.related_data:
                response_parts.append("\n**Protection Details:**")
                for defense_data in result.related_data:
                    response_parts.append(f"• {defense_data['defensive_system'].title()}")
        
        elif result.query_type == 'features':
            response_parts.append(f"⚙️ **SPECIAL FEATURES - {self._clean_entity_name(result.primary_entity['name'])}**")
            response_parts.append(self._improve_description_formatting(result.explanation))
            
            if result.related_data:
                response_parts.append("\n**Feature List:**")
                for feature_data in result.related_data:
                    response_parts.append(f"• {feature_data['special_feature'].title()}")
        
        elif result.query_type == 'specifications':
            response_parts.append(f"📊 **TECHNICAL SPECIFICATIONS - {result.primary_entity['name'].replace('_', ' ')}**")
            response_parts.append(result.explanation)
        
        elif result.query_type == 'character_locations':
            response_parts.append(f"📍 **LOCATION ANALYSIS - {result.primary_entity['name'].replace('_', ' ')}**")
            response_parts.append(result.explanation)
            
            if len(result.related_data) > 1:
                response_parts.append(f"\n**All Associated Locations ({len(result.related_data)} total):**")
                for i, loc_data in enumerate(result.related_data[:10], 1):
                    response_parts.append(f"{i}. {loc_data['name'].replace('_', ' ')}")
                if len(result.related_data) > 10:
                    response_parts.append(f"... and {len(result.related_data) - 10} more locations")
        
        else:
            response_parts.append(f"**{result.primary_entity['name'].replace('_', ' ')}**")
            response_parts.append(result.explanation)
        
        # Add entity description if available and not too long
        if 'description' in result.primary_entity and result.primary_entity['description']:
            desc = result.primary_entity['description']
            formatted_desc = self._improve_description_formatting(desc)
            if len(formatted_desc) > 300:
                formatted_desc = formatted_desc[:297] + "..."
            response_parts.append(f"\n**Background:** {formatted_desc}")
        
        answer = "\n".join(response_parts)
        
        return BatmanResponse(
            answer=answer,
            confidence=result.confidence,
            source_entities=[result.primary_entity['id']],
            query_type=result.query_type
        )

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("Batman chatbot connection closed.")

def main():
    """Test the Batman chatbot."""
    chatbot = BatmanChatbot()
    
    # Display stats
    stats = chatbot.get_stats()
    print(f"\n🦇 Batman Database Stats:")
    for entity_type, count in stats.items():
        print(f"  {entity_type.title()}: {count}")
    
    print("\n🦇 Batman Chatbot Ready! Ask me anything about the Batman universe!")
    print("Type 'quit' to exit.\n")
    
    try:
        while True:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("🦇 Thanks for using the Batman chatbot! See you in Gotham!")
                break
            
            if not user_input:
                continue
            
            # Process query
            response = chatbot.process_query(user_input)
            print(f"\nBatman Expert: {response.answer}")
            print(f"Confidence: {response.confidence:.1%}")
            
            if response.suggestions:
                print(f"Did you mean: {', '.join(response.suggestions)}")
            
            print()
    
    except KeyboardInterrupt:
        print("\n🦇 Batman chatbot interrupted. Goodbye!")
    
    finally:
        chatbot.close()

if __name__ == "__main__":
    main()