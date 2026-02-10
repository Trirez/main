#!/usr/bin/env python
"""
Captcha Generator System - Main Launcher
Run this file to start the application
"""

import os
import sys
import webbrowser
from threading import Timer


def open_browser():
    """Open the browser to the application URL"""
    webbrowser.open('http://127.0.0.1:5000')


def main():
    """Main entry point for the Captcha Generator application"""
    print("=" * 50)
    print("🛡️  Captcha Generator System")
    print("=" * 50)
    print()
    
    # Check if we should open browser automatically
    auto_open = '--no-browser' not in sys.argv
    
    if auto_open:
        print("📌 Opening browser in 2 seconds...")
        Timer(2, open_browser).start()
    
    print("🌐 Starting server at http://127.0.0.1:5000")
    print("📝 Press Ctrl+C to stop the server")
    print()
    
    # Import and run the Flask app
    from app import app
    
    # Run the Flask development server
    app.run(
        host='127.0.0.1',
        port=5000,
        debug=True,
        use_reloader=True
    )


if __name__ == '__main__':
    main()
