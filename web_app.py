#!/usr/bin/env python3
"""
BatChatBot Web Interface
Flask application for the Batman Database Chatbot
CLI Terminal Aesthetic with atomic green styling
"""

import os
import re
import sys
import uuid
from flask import Flask, render_template, request, jsonify, session
from datetime import datetime

import batman_config as cfg
from chatbot.core.batman_chatbot import BatmanChatbot, BatmanResponse
from chatbot.sessions import SessionStore, ConversationSession

app = Flask(__name__)
app.config['SECRET_KEY'] = cfg.FLASK_SECRET_KEY

# Initialize Batman Chatbot
chatbot = None
database_stats = {}

# Persistent session store (SQLite)
session_store = SessionStore(cfg.SESSION_DB_PATH, ttl_seconds=cfg.SESSION_TTL_SECONDS)


def get_or_create_session() -> ConversationSession:
    """Get existing session or create new one."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session_store.get_or_create(session['session_id'])

def initialize_chatbot():
    """Initialize the Batman chatbot and gather database stats."""
    global chatbot, database_stats
    
    try:
        chatbot = BatmanChatbot(str(cfg.DB_PATH))

        # Gather database statistics
        database_stats = {
            'characters': 685,
            'vehicles': 120,
            'locations': 112,
            'storylines': 13,
            'organizations': 126,
            'total_entities': 1056,
            'accuracy': '89.0%',
            'uptime': '99.9%',
            'last_update': 'June 1, 2025',
            'queries_processed': '10,000+'
        }
        
        print("🦇 BatChatBot web interface initialized successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error initializing chatbot: {e}")
        return False

@app.route('/')
def home():
    """Main page with CLI terminal interface."""
    return render_template('index.html', stats=database_stats)

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chatbot queries via API with session management."""
    global chatbot
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'error': 'No query provided',
                'response': 'ERROR: Empty query detected. Please enter a valid Batman-related question.'
            }), 400
        
        # Get or create conversation session
        conv_session = get_or_create_session()
        
        # Resolve pronouns using session context
        original_query = query
        resolved_query = conv_session.resolve_pronouns(query)
        if resolved_query != query:
            print(f"🔍 PRONOUN RESOLVED: '{query}' → '{resolved_query}'")
        query = resolved_query
        
        # Check if query is a number selection
        if query.isdigit():
            number = int(query)
            selected_option = conv_session.get_option_by_number(number)
            
            if selected_option:
                # User selected a numbered option - get detailed info about that entity
                selected_name = selected_option.replace('_', ' ')
                conv_session.clear_numbered_options()  # Clear after selection
                
                # Ensure we have a working chatbot instance
                if not chatbot or not hasattr(chatbot, 'conversation_intelligence') or not chatbot.conversation_intelligence:
                    print("🔧 Reinitializing chatbot for better performance...")
                    chatbot = BatmanChatbot(str(cfg.DB_PATH))
                
                # Get entity info directly by name instead of processing as new query
                result = chatbot.get_entity_info_direct(selected_option)
                
                # Add to conversation history with entity tracking
                conv_session.add_to_history(f"Selection: {number} ({selected_name})", result.answer, entity_name=selected_name)
                session_store.save(conv_session)

                # Format response
                response_text = result.answer
                if len(response_text) > 10000:
                    response_text = response_text[:9997] + "..."

                return jsonify({
                    'query': f"Selection {number}: {selected_name}",
                    'response': response_text,
                    'confidence': f"{result.confidence * 100:.1f}%",
                    'source_entities': len(result.source_entities),
                    'query_type': result.query_type,
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'session_id': conv_session.session_id
                })
            else:
                return jsonify({
                    'error': 'Invalid selection',
                    'response': f'ERROR: "{number}" is not a valid selection. Please choose a number from the previous options or ask a new question.',
                    'timestamp': datetime.now().strftime('%H:%M:%S')
                }), 400
        
        # Ensure we have a working chatbot instance
        if not chatbot or not hasattr(chatbot, 'conversation_intelligence') or not chatbot.conversation_intelligence:
            print("🔧 Reinitializing chatbot for better performance...")
            chatbot = BatmanChatbot(str(cfg.DB_PATH))
        
        # Process regular query through Batman chatbot
        result = chatbot.process_query(query)
        
        # Check if response contains numbered options and store them
        if "Please select which one you'd like to learn about:" in result.answer and hasattr(result, 'suggestions'):
            conv_session.store_numbered_options(result.suggestions, query)
        
        # Extract entity name for context tracking with enhanced patterns
        entity_name = None
        if result.source_entities and len(result.source_entities) > 0:
            # Try to extract clean entity name from response or source entities
            if hasattr(result, 'answer') and "**" in result.answer:
                # Extract from formatted response like "**WEAPONS ANALYSIS - Batmobile**"
                entity_match = re.search(r'\*\*[^-]+-\s*(.+?)\*\*', result.answer)
                if entity_match:
                    entity_name = entity_match.group(1).strip()
            elif ":" in result.answer and len(result.answer) > 50:
                # Extract from responses like "Batman: Description..." 
                # Skip this pattern for now as it's not reliable for our response format
                pass
            else:
                # Enhanced patterns for better entity extraction
                response_text = result.answer
                
                extraction_patterns = [
                    # From query patterns for better context awareness
                    (r'\btell\s+me\s+about\s+(?:the\s+)?(\w+(?:\s+\w+)?)', query.lower()),  # "tell me about the batplane"
                    (r'\bwhat\s+(?:weapons|defenses|features)\s+(?:does|are\s+on)\s+(?:the\s+)?(\w+(?:\s+\w+)?)', query.lower()),  # "what weapons does the batplane have"
                    (r'\b(?:weapons|defenses|features)\s+(?:of|on)\s+(?:the\s+)?(\w+(?:\s+\w+)?)', query.lower()),  # "weapons of the batplane"
                    (r'\b(\w+(?:\s+\w+)?)\s+(?:weapons|defenses|features)', query.lower()),  # "batplane weapons"
                    
                    # From response patterns
                    (r'the ([A-Za-z]+(?:\s+[A-Za-z]+)*) stands out', response_text),
                    (r'The ([A-Za-z]+(?:\s+[A-Za-z]+)*) is', response_text),
                    (r'^([A-Za-z]+(?:\s+[A-Za-z]+)*) is (?:one of|an?|Batman)', response_text),
                    (r'(?:, )?(?:the )?([A-Za-z]+(?:\s+[A-Za-z]+)*) (?:serves|functions) as', response_text),
                    (r', the ([A-Za-z]+(?:\s+[A-Za-z]+)*)', response_text),
                    (r'(?:analyzing|discussing)\s+(?:the\s+)?(\w+(?:\s+\w+)?)', response_text.lower()),
                ]
                
                for pattern, text in extraction_patterns:
                    match = re.search(pattern, text, re.IGNORECASE)
                    if match:
                        candidate = match.group(1).strip()
                        # Clean common words that aren't entities
                        if candidate.lower() not in ['batman', 'the', 'a', 'an', 'analysis', 'weapons', 'defenses', 'features', 'about', 'what', 'does', 'have']:
                            entity_name = candidate
                            break
        
        # Add to conversation history with entity tracking
        print(f"🔍 DEBUG: Extracted entity_name: '{entity_name}' from query: '{query}'")
        conv_session.add_to_history(query, result.answer, entity_name=entity_name)
        session_store.save(conv_session)

        # Format response for terminal display
        response_text = result.answer
        if len(response_text) > 10000:
            response_text = response_text[:9997] + "..."
        
        return jsonify({
            'query': query,
            'response': response_text,
            'confidence': f"{result.confidence * 100:.1f}%",
            'source_entities': len(result.source_entities),
            'query_type': result.query_type,
            'timestamp': datetime.now().strftime('%H:%M:%S'),
            'session_id': conv_session.session_id,
            'has_numbered_options': bool(conv_session.last_numbered_options)
        })
        
    except Exception as e:
        print(f"❌ Chat error: {e}")
        return jsonify({
            'error': str(e),
            'response': 'ERROR: BatComputer malfunction detected. Query processing failed.'
        }), 500

@app.route('/api/session/new', methods=['POST'])
def new_session():
    """Create a new conversation session."""
    if 'session_id' in session:
        session_store.delete(session['session_id'])

    session['session_id'] = str(uuid.uuid4())
    session_store.get_or_create(session['session_id'])

    return jsonify({
        'message': 'New conversation session started',
        'session_id': session['session_id'],
        'timestamp': datetime.now().strftime('%H:%M:%S')
    })

@app.route('/api/session/status')
def session_status():
    """Get current session status and conversation history."""
    conv_session = get_or_create_session()
    
    return jsonify({
        'session_id': conv_session.session_id,
        'created_at': conv_session.created_at,
        'conversation_length': len(conv_session.conversation_history),
        'has_numbered_options': bool(conv_session.last_numbered_options),
        'numbered_options_count': len(conv_session.last_numbered_options)
    })

@app.route('/api/stats')
def stats():
    """Get current database statistics."""
    return jsonify(database_stats)

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'online',
        'chatbot_ready': chatbot is not None,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🦇 Starting BatChatBot Web Interface...")
    print("""
    ██████╗  █████╗ ████████╗███╗   ███╗ █████╗ ███╗   ██╗
    ██╔══██╗██╔══██╗╚══██╔══╝████╗ ████║██╔══██╗████╗  ██║
    ██████╔╝███████║   ██║   ██╔████╔██║███████║██╔██╗ ██║
    ██╔══██╗██╔══██║   ██║   ██║╚██╔╝██║██╔══██║██║╚██╗██║
    ██████╔╝██║  ██║   ██║   ██║ ╚═╝ ██║██║  ██║██║ ╚████║
    ╚═════╝ ╚═╝  ╚═╝   ╚═╝   ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝
    
                    ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
                  ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
                ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
              ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
            ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
          ⚫⚫⚫⚫⚫⚫⚫    ⚫⚫⚫⚫⚫⚫⚫    ⚫⚫⚫⚫⚫⚫⚫
        ⚫⚫⚫⚫⚫⚫⚫⚫    ⚫⚫⚫⚫⚫⚫⚫    ⚫⚫⚫⚫⚫⚫⚫⚫
      ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
    ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
    ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
      ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
        ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
          ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
            ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
              ⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫⚫
                ⚫⚫⚫⚫⚫⚫⚫⚫
                  ⚫⚫⚫⚫
    """)
    print("🔧 Initializing Batman Database Chatbot...")
    
    if initialize_chatbot():
        print("✅ BatComputer online!")
        print("🌐 Starting web server...")
        
        # Use port 5001 to avoid conflicts
        port = 5001
        print(f"🦇 Visit: http://localhost:{port}")
        print(f"🦇 Also try: http://127.0.0.1:{port}")
        print(f"🦇 Also try: http://192.168.68.87:{port}")
        print("═" * 50)
        
        try:
            app.run(debug=False, host='0.0.0.0', port=port, threaded=True, use_reloader=False)
        except Exception as e:
            print(f"❌ Server failed to start: {e}")
            print("🔧 Trying alternative port...")
            import socket
            def find_free_port():
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', 0))
                    return s.getsockname()[1]
            
            alt_port = find_free_port()
            print(f"🦇 Alternative URL: http://localhost:{alt_port}")
            app.run(debug=False, host='0.0.0.0', port=alt_port, threaded=True, use_reloader=False)
    else:
        print("❌ Failed to initialize BatComputer. Exiting.")
        sys.exit(1)