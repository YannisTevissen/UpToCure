#!/usr/bin/env python
"""
UpToCure Server Runner
======================

This script provides a simple way to start the UpToCure server.
"""

import os
import sys
import webbrowser
from time import sleep
from threading import Thread

def setup_directories():
    """Set up the necessary report directories"""
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Ensure the reports directory exists
    reports_dir = os.path.join(base_dir, 'reports')
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir, exist_ok=True)
        print(f"Created reports directory at {reports_dir}")
    
    # Check for en directory
    en_dir = os.path.join(reports_dir, 'en')
    if not os.path.exists(en_dir):
        os.makedirs(en_dir, exist_ok=True)
        print(f"Created English reports directory at {en_dir}")
    
    # Check for fr directory
    fr_dir = os.path.join(reports_dir, 'fr')
    if not os.path.exists(fr_dir):
        os.makedirs(fr_dir, exist_ok=True)
        print(f"Created French reports directory at {fr_dir}")

def open_browser():
    """Open the browser after a short delay"""
    sleep(1)  # Give the server a moment to start
    webbrowser.open('http://localhost:8000')
    print("Browser opened to http://localhost:8000")

def start_server():
    """Start the UpToCure API server"""
    # Setup directories
    setup_directories()
    
    # Add src directory to path if needed
    base_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.join(base_dir, 'src')
    if src_dir not in sys.path:
        sys.path.insert(0, src_dir)
    
    # Start the server
    print("Starting UpToCure server...")
    
    # Open browser in a separate thread
    browser_thread = Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Import and run the Flask app directly
    from src.app import app
    app.run(host='0.0.0.0', port=8000, debug=True)

if __name__ == "__main__":
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1) 