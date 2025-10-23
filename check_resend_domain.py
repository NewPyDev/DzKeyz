#!/usr/bin/env python3
"""
Check Resend.com domain verification and send test emails
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

def check_domains():
    """Check domain verification status"""
    env_vars = load_env_manually()
    api_key = env_vars.get('RESEND_API_KEY')
    
    if not api_key:
        print("❌ Missing API key")
        return
    
    try:
        url = "https://api.resend.com/domains"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print("🔍 Checking domain verification status...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            domains = response.json()
            print("📋 Domain Status:")
            print(json.dumps(domains, indent=2))
        else:
            print(f"❌ Failed to get domains: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error checking domains: {e}")

def test_different_senders():
    """Test sending from different email addresses"""
    env_vars = load_env_manually()
    api_key = env_vars.get('RESEND_API_KEY')
    
    if not api_key:
        print("❌ Missing API key")
        return
    
    # Test different sender addresses
    test_senders = [
        ("Espamoda", "info@espamoda.store"),
        ("Espamoda", "noreply@espamoda.store"),
        ("Espamoda", "support@espamoda.store"),
        ("Test", "onboarding@resend.dev")  # Resend's test domain
    ]
    
    recipient = "relaxthelord@live.fr"
    
    for from_name, from_email in test_senders:
        print(f"\n🧪 Testing sender: {from_name} <{from_email}>")
        
        try:
            url = "https://api.resend.com/emails"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "from": f"{from_name} <{from_email}>",
                "to": [recipient],
                "subject": f"Test from {from_email}",
                "html": f"<p>Test email from <strong>{from_email}</strong></p><p>If you receive this, the sender address works!</p>"
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ SUCCESS: Email ID {result.get('id')}")
            else:
                print(f"❌ FAILED: {response.status_code}")
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                print(f"   Error: {error_data.get('message', response.text)}")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    print("🔍 CHECKING RESEND.COM CONFIGURATION")
    print("=" * 50)
    
    check_domains()
    
    print("\n" + "=" * 50)
    test_different_senders()