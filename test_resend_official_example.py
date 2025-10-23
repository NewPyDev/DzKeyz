#!/usr/bin/env python3
"""
Test using the exact Resend official example format
"""
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

def test_official_example():
    """Test using the exact official Resend example"""
    
    # Load API key
    env_vars = load_env_manually()
    api_key = env_vars.get('RESEND_API_KEY')
    
    if not api_key:
        print("❌ Missing RESEND_API_KEY")
        return
    
    print("🧪 TESTING WITH OFFICIAL RESEND EXAMPLE FORMAT")
    print("=" * 60)
    print(f"📧 API Key: {api_key[:10]}...{api_key[-4:]}")
    
    # Set API key exactly as in the example
    resend.api_key = api_key
    
    # Use the exact format from the official example
    params: resend.Emails.SendParams = {
        "from": "Espamoda <info@espamoda.store>",
        "to": ["relaxthelord@live.fr"],
        "subject": "🧪 Official Resend Example Test",
        "html": """
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #333;">🧪 It works!</h1>
            <p>This email was sent using the <strong>exact official Resend example format</strong>!</p>
            
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #2d5a2d; margin-top: 0;">✅ Success!</h3>
                <p style="margin-bottom: 0;">Your Resend.com integration is working perfectly with the official Python SDK.</p>
            </div>
            
            <h3>📋 Test Details:</h3>
            <ul>
                <li><strong>Method:</strong> Official Resend.Emails.SendParams</li>
                <li><strong>Domain:</strong> espamoda.store (Verified)</li>
                <li><strong>From:</strong> Espamoda &lt;info@espamoda.store&gt;</li>
                <li><strong>SDK Version:</strong> Latest</li>
            </ul>
            
            <p style="color: #666; font-size: 14px; margin-top: 30px; text-align: center;">
                This is a test from your digital store setup<br>
                <strong>Espamoda Store</strong> | Powered by Resend.com
            </p>
        </div>
        """
    }
    
    print("📧 Sending email using official example format...")
    print(f"📧 From: {params['from']}")
    print(f"📧 To: {params['to']}")
    print(f"📧 Subject: {params['subject']}")
    
    try:
        # Send email exactly as in the official example
        email = resend.Emails.send(params)
        
        # Print result exactly as in the official example
        print("\n✅ EMAIL SENT SUCCESSFULLY!")
        print("📧 Response from Resend:")
        print(email)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_official_example()