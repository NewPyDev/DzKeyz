#!/usr/bin/env python3
"""
Test Resend.com using the official Python SDK
"""
import os
import resend

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

def test_domain_info():
    """Get domain information using the SDK"""
    env_vars = load_env_manually()
    api_key = env_vars.get('RESEND_API_KEY')
    
    if not api_key:
        print("❌ Missing API key")
        return
    
    # Set API key
    resend.api_key = api_key
    
    print("🔍 CHECKING DOMAIN WITH RESEND SDK")
    print("=" * 50)
    
    try:
        # Get domain details using the ID from your previous output
        domain_id = "e65cc6f6-fbaf-403b-b207-d43ea2e24765"
        domain_info = resend.Domains.get(domain_id)
        
        print("📋 Domain Information:")
        print(f"   ID: {domain_info.get('id', 'N/A')}")
        print(f"   Name: {domain_info.get('name', 'N/A')}")
        print(f"   Status: {domain_info.get('status', 'N/A')}")
        print(f"   Capability: {domain_info.get('capability', 'N/A')}")
        print(f"   Region: {domain_info.get('region', 'N/A')}")
        print(f"   Created: {domain_info.get('created_at', 'N/A')}")
        
        if hasattr(domain_info, 'records'):
            print("📋 DNS Records:")
            for record in domain_info.records:
                print(f"   {record.type}: {record.name} -> {record.value}")
        
        return domain_info
        
    except Exception as e:
        print(f"❌ Error getting domain info: {e}")
        return None

def test_send_email_sdk():
    """Send email using the official Resend SDK"""
    env_vars = load_env_manually()
    api_key = env_vars.get('RESEND_API_KEY')
    from_email = env_vars.get('MAIL_FROM', 'info@espamoda.store')
    from_name = env_vars.get('MAIL_NAME', 'Espamoda')
    
    if not api_key:
        print("❌ Missing API key")
        return False
    
    # Set API key
    resend.api_key = api_key
    
    print("\n🧪 TESTING EMAIL WITH RESEND SDK")
    print("=" * 50)
    
    try:
        # Send email using SDK
        params = {
            "from": f"{from_name} <{from_email}>",
            "to": ["relaxthelord@live.fr"],
            "subject": "🧪 Resend SDK Test - Official Python Library",
            "html": """
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2 style="color: #333;">🧪 Resend SDK Test</h2>
                <p>This email was sent using the <strong>official Resend Python SDK</strong>!</p>
                
                <div style="background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3>✅ Success!</h3>
                    <p>If you're reading this, the Resend Python SDK is working perfectly with your Flask application.</p>
                </div>
                
                <h3>📋 Technical Details:</h3>
                <ul>
                    <li><strong>Method:</strong> Official Resend Python SDK</li>
                    <li><strong>Domain:</strong> espamoda.store (Verified)</li>
                    <li><strong>From:</strong> {from_name} &lt;{from_email}&gt;</li>
                    <li><strong>Library:</strong> resend-python v2.17.0</li>
                </ul>
                
                <p style="color: #666; font-size: 14px; margin-top: 30px;">
                    This is an automated test from your digital store setup.<br>
                    <strong>Espamoda Store</strong> | Powered by Resend.com
                </p>
            </div>
            """,
            "text": f"""
🧪 Resend SDK Test - Official Python Library

This email was sent using the official Resend Python SDK!

✅ Success!
If you're reading this, the Resend Python SDK is working perfectly with your Flask application.

📋 Technical Details:
- Method: Official Resend Python SDK
- Domain: espamoda.store (Verified)
- From: {from_name} <{from_email}>
- Library: resend-python v2.17.0

This is an automated test from your digital store setup.
Espamoda Store | Powered by Resend.com
            """
        }
        
        print(f"📧 Sending email to: relaxthelord@live.fr")
        print(f"📧 From: {from_name} <{from_email}>")
        print("📧 Using official Resend SDK...")
        
        email = resend.Emails.send(params)
        
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print(f"📧 Email ID: {email.get('id', 'Unknown')}")
        print("📧 Check your inbox and spam folder!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

if __name__ == "__main__":
    # Test domain info
    domain_info = test_domain_info()
    
    # Test email sending
    if domain_info and domain_info.get('status') == "verified":
        test_send_email_sdk()
    else:
        print("❌ Domain not verified, skipping email test")