#!/usr/bin/env python3
"""
Test script to check if Brevo email sending is working
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_email_sending():
    """Test email sending with current Brevo configuration"""
    
    # Get email configuration from environment variables
    smtp_host = os.getenv('EMAIL_HOST', 'smtp-relay.brevo.com')
    smtp_port = int(os.getenv('EMAIL_PORT', '587'))
    use_tls = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    username = os.getenv('EMAIL_HOST_USER')
    password = os.getenv('EMAIL_HOST_PASSWORD')
    from_email = os.getenv('DEFAULT_FROM_EMAIL', username)
    from_name = os.getenv('STORE_NAME', 'Digital Store')
    
    # Test email details
    test_email = "hami@espamoda.store"  # Send to your own domain
    subject = "🧪 Brevo Email Test - " + str(os.urandom(4).hex())
    body = f"""This is a test email from your Brevo SMTP configuration.

Test Details:
- SMTP Host: {smtp_host}:{smtp_port}
- From: {from_name} <{from_email}>
- TLS: {use_tls}
- Username: {username}
- Time: {os.popen('date /t & time /t').read().strip()}

If you receive this email, your Brevo configuration is working! ✅

Note: Free Brevo accounts may have delivery delays or lower priority routing.
"""
    
    print("🧪 TESTING BREVO EMAIL CONFIGURATION")
    print("=" * 50)
    print(f"📧 To: {test_email}")
    print(f"📧 From: {from_name} <{from_email}>")
    print(f"📧 Subject: {subject}")
    print(f"📧 SMTP: {smtp_host}:{smtp_port}")
    print(f"📧 TLS: {use_tls}")
    print(f"📧 Username: {username}")
    print("=" * 50)
    
    if not username or not password:
        print("❌ FAILED: Missing EMAIL_HOST_USER or EMAIL_HOST_PASSWORD in .env")
        return False
    
    if password == "PUT_YOUR_SMTP_PASSWORD_HERE":
        print("❌ FAILED: Please update EMAIL_HOST_PASSWORD in .env with your actual SMTP password")
        return False
    
    try:
        # Create message
        msg = MIMEMultipart()
        msg['From'] = f"{from_name} <{from_email}>"
        msg['To'] = test_email
        msg['Subject'] = subject
        
        # Add body to email
        msg.attach(MIMEText(body, 'plain'))
        
        print("📧 Connecting to SMTP server...")
        # Create SMTP session
        server = smtplib.SMTP(smtp_host, smtp_port)
        
        if use_tls:
            print("📧 Starting TLS...")
            server.starttls()  # Enable TLS encryption
        
        print("📧 Logging in...")
        server.login(username, password)
        
        print("📧 Sending email...")
        text = msg.as_string()
        server.sendmail(from_email, test_email, text)
        server.quit()
        
        print("✅ EMAIL SENT SUCCESSFULLY!")
        print("📧 Check your inbox and spam folder")
        print("📧 Note: Free Brevo accounts may have delivery delays")
        print("📧 Email should arrive within 5-30 minutes")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ SMTP Authentication failed: {e}")
        print("❌ Check your EMAIL_HOST_USER and EMAIL_HOST_PASSWORD in .env")
        return False
    except smtplib.SMTPRecipientsRefused as e:
        print(f"❌ Recipient refused: {e}")
        print("❌ Check if the recipient email address is valid")
        return False
    except smtplib.SMTPServerDisconnected as e:
        print(f"❌ SMTP server disconnected: {e}")
        print("❌ Check your internet connection and SMTP settings")
        return False
    except Exception as e:
        print(f"❌ EMAIL SENDING FAILED: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_email_sending()