#!/usr/bin/env python3
"""
Test script to check if Resend.com email sending is working
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_resend_email():
    """Test email sending with Resend.com API"""
    
    # Get Resend configuration from environment variables
    api_key = os.getenv('RESEND_API_KEY')
    from_email = os.getenv('MAIL_FROM', 'info@espamoda.store')
    from_name = os.getenv('MAIL_NAME', 'Espamoda')
    
    # Test email details
    test_email = "hami@espamoda.store"  # Send to your own domain
    subject = "🧪 Resend.com Email Test - " + str(os.urandom(4).hex())
    
    html_body = f"""
    <h2>🧪 Resend.com Email Test</h2>
    <p>This is a test email from your Resend.com API configuration.</p>
    
    <h3>Test Details:</h3>
    <ul>
        <li><strong>Service:</strong> Resend.com API</li>
        <li><strong>From:</strong> {from_name} &lt;{from_email}&gt;</li>
        <li><strong>API Key:</strong> {api_key[:10] + '...' + api_key[-4:] if api_key else 'MISSING'}</li>
        <li><strong>Time:</strong> Now</li>
    </ul>
    
    <p><strong>If you receive this email, your Resend.com configuration is working! ✅</strong></p>
    
    <p><em>Note: Resend.com typically has excellent deliverability and fast delivery times.</em></p>
    """
    
    text_body = f"""🧪 Resend.com Email Test

This is a test email from your Resend.com API configuration.

Test Details:
- Service: Resend.com API
- From: {from_name} <{from_email}>
- API Key: {api_key[:10] + '...' + api_key[-4:] if api_key else 'MISSING'}

If you receive this email, your Resend.com configuration is working! ✅

Note: Resend.com typically has excellent deliverability and fast delivery times.
"""
    
    print("🧪 TESTING RESEND.COM EMAIL CONFIGURATION")
    print("=" * 50)
    print(f"📧 To: {test_email}")
    print(f"📧 From: {from_name} <{from_email}>")
    print(f"📧 Subject: {subject}")
    print(f"📧 API Key: {api_key[:10] + '...' + api_key[-4:] if api_key else 'MISSING'}")
    print("=" * 50)
    
    if not api_key:
        print("❌ FAILED: Missing RESEND_API_KEY in .env")
        return False
    
    if not from_email:
        print("❌ FAILED: Missing MAIL_FROM in .env")
        return False
    
    try:
        # Resend API endpoint
        url = "https://api.resend.com/emails"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # Email data
        data = {
            "from": f"{from_name} <{from_email}>",
            "to": [test_email],
            "subject": subject,
            "html": html_body,
            "text": text_body
        }
        
        print("📧 Sending email via Resend.com API...")
        
        # Send the email
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            email_id = result.get('id', 'Unknown')
            
            print("✅ EMAIL SENT SUCCESSFULLY!")
            print(f"📧 Email ID: {email_id}")
            print("📧 Check your inbox - Resend.com has excellent deliverability!")
            print("📧 Email should arrive within 1-5 minutes")
            return True
        else:
            print(f"❌ EMAIL SENDING FAILED!")
            print(f"❌ Status Code: {response.status_code}")
            print(f"❌ Response: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                if 'message' in error_data:
                    print(f"❌ Error Message: {error_data['message']}")
                if 'name' in error_data:
                    print(f"❌ Error Type: {error_data['name']}")
            except:
                pass
            
            return False
        
    except requests.exceptions.RequestException as e:
        print(f"❌ REQUEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ EMAIL SENDING FAILED: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_resend_email()