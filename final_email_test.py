#!/usr/bin/env python3
"""
Final comprehensive email test
"""
import os
import requests
import json
from datetime import datetime

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

def send_comprehensive_test():
    """Send a comprehensive test email"""
    env_vars = load_env_manually()
    api_key = env_vars.get('RESEND_API_KEY')
    
    if not api_key:
        print("❌ Missing API key")
        return
    
    # Email details
    recipient = "relaxthelord@live.fr"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    subject = f"🧪 FINAL EMAIL TEST - {timestamp}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Email Test</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
            <h1>🧪 Email Delivery Test</h1>
            <p>Testing Resend.com Integration</p>
        </div>
        
        <div style="padding: 20px; background: #f9f9f9; margin: 20px 0; border-radius: 5px;">
            <h2>✅ SUCCESS! This email was delivered!</h2>
            <p><strong>If you're reading this, the email system is working perfectly!</strong></p>
            
            <h3>📋 Test Details:</h3>
            <ul>
                <li><strong>Service:</strong> Resend.com</li>
                <li><strong>From:</strong> Espamoda &lt;info@espamoda.store&gt;</li>
                <li><strong>Domain Status:</strong> Verified ✅</li>
                <li><strong>Sent At:</strong> {timestamp}</li>
                <li><strong>Recipient:</strong> {recipient}</li>
            </ul>
            
            <h3>🎯 What This Means:</h3>
            <p>Your Flask shop's email system is now fully operational and ready to:</p>
            <ul>
                <li>Send order confirmations</li>
                <li>Deliver digital products</li>
                <li>Send receipts and invoices</li>
                <li>Handle customer communications</li>
            </ul>
        </div>
        
        <div style="text-align: center; padding: 20px; color: #666;">
            <p>This is an automated test from your digital store setup.</p>
            <p><strong>Espamoda Store</strong> | Powered by Resend.com</p>
        </div>
    </body>
    </html>
    """
    
    text_body = f"""
🧪 EMAIL DELIVERY TEST - {timestamp}

✅ SUCCESS! This email was delivered!

If you're reading this, the email system is working perfectly!

📋 Test Details:
- Service: Resend.com
- From: Espamoda <info@espamoda.store>
- Domain Status: Verified ✅
- Sent At: {timestamp}
- Recipient: {recipient}

🎯 What This Means:
Your Flask shop's email system is now fully operational and ready to:
- Send order confirmations
- Deliver digital products  
- Send receipts and invoices
- Handle customer communications

This is an automated test from your digital store setup.
Espamoda Store | Powered by Resend.com
    """
    
    try:
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "from": "Espamoda <info@espamoda.store>",
            "to": [recipient],
            "subject": subject,
            "html": html_body,
            "text": text_body
        }
        
        print(f"📧 Sending comprehensive test email to: {recipient}")
        print(f"📧 Subject: {subject}")
        print(f"📧 From: Espamoda <info@espamoda.store>")
        print("📧 Sending...")
        
        response = requests.post(url, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            email_id = result.get('id')
            
            print("✅ EMAIL SENT SUCCESSFULLY!")
            print(f"📧 Email ID: {email_id}")
            print(f"📧 Sent to: {recipient}")
            print(f"📧 Time: {timestamp}")
            print("\n🔍 IMPORTANT: Check these locations for the email:")
            print("   1. Inbox")
            print("   2. Spam/Junk folder")
            print("   3. Promotions tab (Gmail)")
            print("   4. Updates tab (Gmail)")
            print("\n⏰ Email should arrive within 1-5 minutes")
            
            return True
        else:
            print(f"❌ FAILED: {response.status_code}")
            print(f"❌ Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🚀 FINAL EMAIL DELIVERY TEST")
    print("=" * 50)
    send_comprehensive_test()