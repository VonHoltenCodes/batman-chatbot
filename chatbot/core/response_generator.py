#!/usr/bin/env python3
"""
Advanced Response Generator for Batman Chatbot
Phase 2.3: Enhanced response generation with personality and dynamic content
"""

import sqlite3
import random
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

@dataclass
class ResponseContext:
    """Context for generating responses."""
    entity: Dict[str, Any]
    entity_type: str
    query_intent: str
    user_query: str
    confidence: float
    related_entities: List[Dict] = None

class BatmanResponseGenerator:
    """Advanced response generator with Batman expert personality."""
    
    def __init__(self, db_connection: sqlite3.Connection):
        """Initialize the response generator."""
        self.conn = db_connection
        
        # Batman expert personality settings
        self.personality = {
            "expertise_level": "expert",
            "tone": "authoritative_but_helpful", 
            "enthusiasm": "high",
            "detail_level": "comprehensive",
            "batman_focus": True
        }
        
        # Enhanced response templates
        self.templates = {
            "character_intro": [
                "Based on my extensive knowledge of the Batman universe, {name} is {description}",
                "Let me tell you about {name}. {description}",
                "From the depths of Gotham's history, {name} is {description}",
                "As a Batman expert, I can tell you that {name} is {description}",
                "In the shadows of Gotham, {name} is {description}"
            ],
            "vehicle_intro": [
                "The {name} is one of Batman's most impressive vehicles. {description}",
                "From the Batcave's vehicle bay, the {name} stands out. {description}",
                "Batman's arsenal includes the remarkable {name}. {description}",
                "Let me detail this incredible piece of Batman technology: the {name}. {description}",
                "In Batman's war on crime, the {name} plays a crucial role. {description}"
            ],
            "location_intro": [
                "In the sprawling metropolis of Gotham, {name} holds special significance. {description}",
                "Within Batman's domain, {name} is {description}",
                "Gotham City's geography includes the notable {name}. {description}",
                "From my knowledge of Batman's world, {name} is {description}",
                "The Dark Knight's territory encompasses {name}, which is {description}"
            ],
            "organization_intro": [
                "In the complex web of Gotham's power structures, {name} is {description}",
                "Batman has encountered {name}, which is {description}",
                "Among Gotham's many organizations, {name} stands out. {description}",
                "From Batman's extensive case files, {name} is {description}",
                "The {name} plays a role in Batman's world. {description}"
            ],
            "storyline_intro": [
                "One of the most significant stories in Batman's history is {name}. {description}",
                "Batman enthusiasts know {name} as {description}",
                "In the pantheon of Batman stories, {name} is {description}",
                "From the comic archives, {name} represents {description}",
                "The storyline {name} is {description}"
            ]
        }
        
        # Confidence-based modifiers
        self.confidence_modifiers = {
            "high": ["I'm confident that", "Without a doubt", "Definitely", "Absolutely"],
            "medium": ["I believe", "Based on available information", "It appears that", "Most likely"],
            "low": ["I think", "It's possible that", "There's some indication that", "Perhaps"]
        }
        
        # Interest enhancers
        self.interest_enhancers = [
            "Here's what makes this fascinating:",
            "What's particularly interesting is that",
            "The remarkable thing about this is",
            "What really stands out is that",
            "You might find it intriguing that"
        ]
        
    def generate_response(self, context: ResponseContext) -> str:
        """
        Generate an enhanced response with personality and dynamic content.
        
        Args:
            context: Response context with entity and query information
            
        Returns:
            Enhanced response string
        """
        # Get base response template
        base_response = self._get_base_response(context)
        
        # Enhance with personality
        enhanced_response = self._add_personality(base_response, context)
        
        # Add related information
        enhanced_response = self._add_related_info(enhanced_response, context)
        
        # Optimize length
        enhanced_response = self._optimize_length(enhanced_response, context)
        
        # Add Batman expert touch
        enhanced_response = self._add_expert_touch(enhanced_response, context)
        
        return enhanced_response
    
    def _get_base_response(self, context: ResponseContext) -> str:
        """Generate base response using appropriate template."""
        entity = context.entity
        entity_type = context.entity_type
        
        # Choose template based on entity type
        if entity_type == 'characters':
            template = random.choice(self.templates["character_intro"])
            return template.format(
                name=self._clean_entity_name(entity.get('name', 'Unknown')),
                description=self._improve_description_formatting(entity.get('description', ''))
            )
        elif entity_type == 'vehicles':
            template = random.choice(self.templates["vehicle_intro"])
            return template.format(
                name=self._clean_entity_name(entity.get('name', 'Unknown Vehicle')),
                description=self._improve_description_formatting(entity.get('description', ''))
            )
        elif entity_type == 'locations':
            template = random.choice(self.templates["location_intro"])
            return template.format(
                name=self._clean_entity_name(entity.get('name', 'Unknown Location')),
                description=self._improve_description_formatting(entity.get('description', ''))
            )
        elif entity_type == 'organizations':
            template = random.choice(self.templates["organization_intro"])
            return template.format(
                name=self._clean_entity_name(entity.get('name', 'Unknown Organization')),
                description=self._improve_description_formatting(entity.get('description', ''))
            )
        elif entity_type == 'storylines':
            template = random.choice(self.templates["storyline_intro"])
            return template.format(
                name=self._clean_entity_name(entity.get('name', 'Unknown Storyline')),
                description=self._improve_description_formatting(entity.get('description', ''))
            )
        else:
            return f"I found information about {self._clean_entity_name(entity.get('name', 'this entity'))}: {self._improve_description_formatting(entity.get('description', ''))}"
    
    def _add_personality(self, response: str, context: ResponseContext) -> str:
        """Add Batman expert personality to the response."""
        confidence_level = "high" if context.confidence > 0.8 else "medium" if context.confidence > 0.5 else "low"
        
        # Add confidence modifier occasionally
        if random.random() < 0.3:  # 30% chance
            modifier = random.choice(self.confidence_modifiers[confidence_level])
            response = f"{modifier}, {response.lower()}"
        
        return response
    
    def _add_related_info(self, response: str, context: ResponseContext) -> str:
        """Add related information to enrich the response."""
        if context.entity_type == 'characters':
            return self._add_character_relations(response, context)
        elif context.entity_type == 'vehicles':
            return self._add_vehicle_specs(response, context)
        elif context.entity_type == 'locations':
            return self._add_location_details(response, context)
        else:
            return response
    
    def _add_character_relations(self, response: str, context: ResponseContext) -> str:
        """Add character relationship information."""
        try:
            cursor = self.conn.cursor()
            
            # Get character aliases
            cursor.execute("""
                SELECT alias FROM character_aliases 
                WHERE character_id = ? 
                LIMIT 3
            """, (context.entity['id'],))
            
            aliases = [row[0] for row in cursor.fetchall()]
            if aliases:
                alias_text = ", ".join(aliases[:2])  # Show first 2 aliases
                response += f" Also known as {alias_text}."
            
            # Get character powers/abilities
            cursor.execute("""
                SELECT power_ability FROM character_powers 
                WHERE character_id = ? 
                LIMIT 3
            """, (context.entity['id'],))
            
            powers = [row[0] for row in cursor.fetchall()]
            if powers:
                power_text = ", ".join(powers[:2])  # Show first 2 powers
                response += f" Notable abilities include {power_text}."
            
            return response
            
        except Exception as e:
            return response
    
    def _add_vehicle_specs(self, response: str, context: ResponseContext) -> str:
        """Add vehicle specification details."""
        try:
            cursor = self.conn.cursor()
            
            # Get vehicle specifications
            cursor.execute("""
                SELECT max_speed, armor, crew_capacity 
                FROM vehicle_specifications 
                WHERE vehicle_id = ?
            """, (context.entity['id'],))
            
            spec = cursor.fetchone()
            if spec and any(spec):
                spec_details = []
                if spec[0]:  # max_speed
                    spec_details.append(f"top speed of {spec[0]}")
                if spec[1]:  # armor
                    spec_details.append(f"armor: {spec[1]}")
                if spec[2]:  # crew_capacity
                    spec_details.append(f"crew capacity: {spec[2]}")
                
                if spec_details:
                    response += f" Key specifications: {', '.join(spec_details)}."
            
            # Get weapons
            cursor.execute("""
                SELECT weapon FROM vehicle_weapons 
                WHERE vehicle_id = ? 
                LIMIT 3
            """, (context.entity['id'],))
            
            weapons = [row[0] for row in cursor.fetchall()]
            if weapons:
                weapon_text = ", ".join(weapons[:2])
                response += f" Armed with {weapon_text}."
            
            return response
            
        except Exception as e:
            return response
    
    def _add_location_details(self, response: str, context: ResponseContext) -> str:
        """Add location-specific details."""
        try:
            cursor = self.conn.cursor()
            
            # Find characters associated with this location
            cursor.execute("""
                SELECT c.name FROM characters c
                JOIN character_locations cl ON c.id = cl.character_id
                WHERE cl.location_id = ?
                LIMIT 3
            """, (context.entity['id'],))
            
            associated_chars = [row[0] for row in cursor.fetchall()]
            if associated_chars:
                char_text = ", ".join(associated_chars[:2])
                response += f" Associated with {char_text}."
            
            return response
            
        except Exception as e:
            return response
    
    def _optimize_length(self, response: str, context: ResponseContext) -> str:
        """Optimize response length for readability."""
        # Target length: 150-400 characters for concise, 400-800 for detailed
        target_max = 600 if self.personality["detail_level"] == "comprehensive" else 300
        
        if len(response) > target_max:
            # Truncate at sentence boundary
            sentences = response.split('. ')
            truncated = []
            current_length = 0
            
            for sentence in sentences:
                if current_length + len(sentence) > target_max:
                    break
                truncated.append(sentence)
                current_length += len(sentence) + 2  # +2 for '. '
            
            if truncated:
                result = '. '.join(truncated)
                if not result.endswith('.'):
                    result += '.'
                return result
        
        return response
    
    def _add_expert_touch(self, response: str, context: ResponseContext) -> str:
        """Add Batman expert personality touches."""
        # Add expert insights occasionally
        if random.random() < 0.2:  # 20% chance
            enhancer = random.choice(self.interest_enhancers)
            
            # Add context-specific insights
            if context.entity_type == 'characters':
                insights = [
                    "this character has a rich history in Batman comics",
                    "their relationship with Batman is complex and evolving",
                    "they represent an important part of Gotham's ecosystem"
                ]
            elif context.entity_type == 'vehicles':
                insights = [
                    "this vehicle showcases Batman's technological prowess",
                    "it represents Batman's strategic approach to crime fighting",
                    "the engineering behind this is truly remarkable"
                ]
            elif context.entity_type == 'locations':
                insights = [
                    "this location has witnessed many pivotal Batman moments",
                    "it plays a crucial role in Gotham's geography",
                    "the atmosphere here perfectly captures Gotham's essence"
                ]
            else:
                insights = [
                    "this adds depth to the Batman universe",
                    "it showcases the complexity of Batman's world"
                ]
            
            insight = random.choice(insights)
            response += f" {enhancer} {insight}."
        
        return response
    
    def _clean_description(self, description: str) -> str:
        """Clean and format description text."""
        if not description:
            return "No description available"
        
        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', description.strip())
        
        # Ensure it ends with proper punctuation
        if cleaned and not cleaned.endswith(('.', '!', '?')):
            cleaned += '.'
        
        return cleaned
    
    def _clean_entity_name(self, name: str) -> str:
        """Clean and format entity names for display."""
        if not name:
            return "Unknown"
        
        import urllib.parse
        
        # 1. URL decode to fix %27 → ' issues
        cleaned = urllib.parse.unquote(name)
        
        # 2. Replace underscores with spaces
        cleaned = cleaned.replace('_', ' ')
        
        # 3. Remove parenthetical universe references for cleaner display
        cleaned = re.sub(r'\s*\([^)]*verse[^)]*\)$', '', cleaned)
        
        # 4. Clean up multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned.strip())
        
        return cleaned
    
    def _improve_description_formatting(self, description: str) -> str:
        """Improve description formatting beyond basic cleaning."""
        if not description:
            return "No description available"
        
        # Start with basic cleaning
        cleaned = self._clean_description(description)
        
        # Fix missing spaces after periods
        cleaned = re.sub(r'\.([A-Z])', r'. \1', cleaned)
        
        # Fix capitalization issues like "BatmobilesareBatman's" 
        # Add space before capital letters that follow lowercase letters
        cleaned = re.sub(r'([a-z])([A-Z])', r'\1 \2', cleaned)
        
        # Fix common concatenations
        concatenation_fixes = {
            'theBatmobile': 'the Batmobile',
            'theJoker': 'the Joker', 
            'theBatman': 'the Batman',
            'theUnited': 'the United',
            'asArkham': 'as Arkham',
            'ofGotham': 'of Gotham',
            'byBatman': 'by Batman',
            'bythe': 'by the',
            'ofthe': 'of the',
            'inthe': 'in the',
            'onthe': 'on the',
            'atthe': 'at the'
        }
        
        for incorrect, correct in concatenation_fixes.items():
            cleaned = cleaned.replace(incorrect, correct)
        
        return cleaned
    
    def generate_multiple_choice_response(self, matches: List[Dict], query: str) -> str:
        """Generate response for multiple entity matches."""
        intro_options = [
            f"I found several Batman universe entities matching '{query}':",
            f"Your query '{query}' could refer to multiple things in Batman's world:",
            f"There are several possibilities for '{query}' in the Batman universe:",
            f"'{query}' matches multiple entities in my Batman database:"
        ]
        
        intro = random.choice(intro_options)
        
        # Format the matches
        match_lines = []
        for i, match in enumerate(matches[:5], 1):
            entity_type = match.get('entity_type', match.get('type', 'entity'))
            name = match.get('name', 'Unknown')
            match_lines.append(f"{i}. {name} ({entity_type})")
        
        suggestion = "Which one would you like to know more about?"
        
        return f"{intro}\n\n" + "\n".join(match_lines) + f"\n\n{suggestion}"
    
    def generate_no_match_response(self, query: str) -> str:
        """Generate helpful response when no matches are found."""
        responses = [
            f"I couldn't find '{query}' in my extensive Batman database. Could you be more specific or check the spelling?",
            f"'{query}' doesn't appear in my Batman universe knowledge. Try asking about characters, vehicles, locations, or storylines.",
            f"I don't have information about '{query}' in the Batman universe. Perhaps you meant something else?",
            f"My Batman database doesn't contain '{query}'. Feel free to ask about any Batman character, vehicle, or location!"
        ]
        
        base_response = random.choice(responses)
        
        # Add helpful suggestions
        suggestions = [
            "Popular searches include Batman, Joker, Batmobile, Gotham City, or Robin.",
            "Try asking about iconic characters like Batman, villains like Two-Face, or locations like Wayne Manor.",
            "You might be interested in Batman, Catwoman, the Batcave, or Arkham Asylum."
        ]
        
        suggestion = random.choice(suggestions)
        return f"{base_response} {suggestion}"

def test_response_generator():
    """Test the response generator."""
    import sqlite3
    
    # Connect to database
    db_path = "../../database/batman_universe.db"
    conn = sqlite3.connect(db_path)
    
    # Initialize generator
    generator = BatmanResponseGenerator(conn)
    
    # Test with sample entity
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM characters WHERE name = 'Batman' LIMIT 1")
    batman_data = cursor.fetchone()
    
    if batman_data:
        # Convert to dict
        columns = [description[0] for description in cursor.description]
        batman_dict = dict(zip(columns, batman_data))
        
        # Create context
        context = ResponseContext(
            entity=batman_dict,
            entity_type='characters',
            query_intent='character_info',
            user_query="Who is Batman?",
            confidence=0.95
        )
        
        # Generate response
        response = generator.generate_response(context)
        
        print("🦇 Testing Enhanced Response Generator")
        print("=" * 50)
        print(f"Query: {context.user_query}")
        print(f"Enhanced Response:\n{response}")
        print(f"Length: {len(response)} characters")
    
    conn.close()

if __name__ == "__main__":
    test_response_generator()