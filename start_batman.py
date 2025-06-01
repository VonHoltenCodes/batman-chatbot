#!/usr/bin/env python3
"""
Production Batman Chatbot Launcher
Direct deployment to ensure reliable connection
"""

import os
import sys
import socket
import signal

def find_free_port(start_port=5001):
    """Find a free port starting from start_port"""
    port = start_port
    while port < 65535:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            port += 1
    raise RuntimeError("No free ports available")

def signal_handler(sig, frame):
    print("\n🦇 Batman Chatbot shutting down gracefully...")
    sys.exit(0)

if __name__ == '__main__':
    # Handle graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("🦇 BATMAN CHATBOT - PRODUCTION LAUNCHER 🦇")
    print("=" * 50)
    
    # Change to correct directory
    os.chdir('/home/traxx/batman_chatbot')
    
    # Find free port
    try:
        port = find_free_port(5001)
        print(f"✅ Found free port: {port}")
    except RuntimeError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Import and configure the app
    try:
        from web_app import app, initialize_chatbot
        print("✅ Flask app imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import app: {e}")
        sys.exit(1)
    
    # Initialize chatbot
    print("🔧 Initializing Batman Database...")
    if not initialize_chatbot():
        print("❌ Failed to initialize chatbot")
        sys.exit(1)
    
    print("✅ BatComputer online!")
    print("🚀 Starting production server...")
    print(f"🌐 Visit: http://localhost:{port}")
    print(f"🌐 Also try: http://127.0.0.1:{port}")
    print(f"🌐 Network: http://192.168.68.87:{port}")
    print("=" * 50)
    print("🦇 Server running... Press Ctrl+C to stop")
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=False,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)