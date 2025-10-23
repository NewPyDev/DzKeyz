#!/usr/bin/env python3
"""
Test the updated app.py email function
"""
import sys
import os

# Add current directory to path so we can import from app.py
sys.path.insert(0, os.getcwd())

# Import the send_email function from app.py
from app import send_email

def test_app_email():
    """Test the updated send_email function from app.py"""
    
    print("🧪 TESTING UPDATED APP.PY EMAIL FUNCTION")
    print("=" * 50)
    
    # Test email
    to_email = "relaxthelord@live.fr"
    subject = "🧪 App.py Email Test - Updated with Resend.com SDK"
    body = """Dear Customer,

This is a test email from your updated Flask application.

The app is now using the official Resend.com Python SDK for better email delivery!

Features:
- Faster delivery times
- Better inbox placement
- More reliable service
- Professional email formatting

Best regards,
Espamoda Team"""
    
    print(f"📧 Testing email to: {to_email}")
    print(f"📧 Subject: {subject}")
    print("=" * 50)
    
    # Send the test email
    success = send_email(to_email, subject, body)
    
    if success:
        print("✅ APP EMAIL FUNCTION TEST PASSED!")
        print("📧 Your Flask app is now ready to send emails via Resend.com")
    else:
        print("❌ APP EMAIL FUNCTION TEST FAILED!")
        print("❌ Check the error messages above")
    
    return success

if __name__ == "__main__":
    test_app_email()