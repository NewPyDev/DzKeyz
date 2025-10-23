#!/usr/bin/env python3
"""
Simple test script for Resend.com email
"""
import os
import requests
import json

def load_env_manually():
    """Manually load .env file"""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except Exception as e:
        print(f"Error loading .env: {e}")
    return env_vars

def test_resend():
    """Test Resend.com email sending"""
    
    # Load environment variables manually
    env_vars = load_env_manually()
    
    api_key = env_vars.get('RESEND_API_KEY')
    from_email = env_vars.get('MAIL_FROM', 'info@espamoda.store')
    from_name = env_vars.get('MAIL_NAME', 'Espamoda')
    
    print("🧪 TESTING RESEND.COM EMAIL")
    print("=" * 40)
    print(f"📧 API Key: {api_key[:10] + '...' + api_key[-4:] if api_key else 'MISSING'}")
    print(f"📧 From: {from_name} <{from_email}>")
    print("=" * 40)
    
    if not api_key:
        print("❌ FAILED: Missing RESEND_API_KEY")
        print("Available env vars:", list(env_vars.keys()))
        return False
    
    # Test email details
    test_email = "relaxthelord@live.fr"
    subject = "🧪 Resend Test - " + str(os.urandom(4).hex())
    
    html_body = f"""
    <h2>🧪 Resend.com Email Test</h2>
    <p>This is a test email from your Resend.com configuration.</p>
    <p><strong>From:</strong> {from_name} &lt;{from_email}&gt;</p>
    <p><strong>If you receive this, Resend.com is working! ✅</strong></p>
    """
    
    try:
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "from": f"{from_name} <{from_email}>",
            "to": [test_email],
            "subject": subject,
            "html": html_body
        }
        
        print("📧 Sending email...")
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ EMAIL SENT SUCCESSFULLY!")
            print(f"📧 Email ID: {result.get('id', 'Unknown')}")
            print("📧 Check your inbox!")
            return True
        else:
            print(f"❌ FAILED: Status {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    test_resend()