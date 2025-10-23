#!/usr/bin/env python3
"""
Simple run script for the Digital Products Store
"""

import os
import sys

def check_requirements():
    """Check if required packages are installed"""
    try:
        import flask
        import requests
        from dotenv import load_dotenv
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_setup():
    """Check if the application is properly set up"""
    if not os.path.exists('store.db'):
        print("❌ Database not found. Please run setup first:")
        print("python setup.py")
        return False
    
    if not os.path.exists('.env'):
        print("⚠ Warning: .env file not found. Using default configuration.")
    
    return True

def main():
    print("🚀 Starting Digital Products Store...")
    
    if not check_requirements():
        sys.exit(1)
    
    if not check_setup():
        sys.exit(1)
    
    # Import and run the Flask app
    from app import app
    
    print("✅ Application starting...")
    print("📱 Access the store at: http://localhost:5000")
    print("🔧 Admin panel at: http://localhost:5000/admin")
    print("👤 Default admin: admin/admin123")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Goodbye!")

if __name__ == '__main__':
    main()