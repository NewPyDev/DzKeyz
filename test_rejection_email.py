#!/usr/bin/env python3
"""
Test the new rejection email functionality
"""
import sys
import os

# Add current directory to path so we can import from app.py
sys.path.insert(0, os.getcwd())

# Import the send_email function from app.py
from app import send_email

def test_rejection_email():
    """Test the new rejection email format"""
    
    print("🧪 TESTING REJECTION EMAIL FUNCTIONALITY")
    print("=" * 50)
    
    # Test email address
    test_email = "relaxthelord@live.fr"
    
    # Test rejection email
    subject = "Order Update - Espamoda"
    body = """We regret to inform you that your recent order could not be processed.

Order Details:
- Order ID: #12345
- Product: Premium Digital Art Pack
- Submitted by: Ahmed

Reason for rejection:
Unfortunately, we were unable to verify your payment. This could be due to:
- Payment screenshot was unclear or incomplete
- Payment amount did not match the order total
- Payment was sent to incorrect account details
- Technical issues with payment verification

Next Steps:
If you believe this is an error, please contact our support team with your order ID and payment details. We're here to help resolve any issues.

We apologize for any inconvenience caused."""
    
    print(f"📧 Testing rejection email to: {test_email}")
    print(f"📧 Subject: {subject}")
    print("=" * 50)
    
    success = send_email(test_email, subject, body, "Ahmed", "order_rejection")
    
    if success:
        print("✅ REJECTION EMAIL TEST PASSED!")
        print("📧 Professional rejection email sent successfully!")
        print("📧 Features of the rejection email:")
        print("   - Professional and empathetic tone")
        print("   - Clear explanation of rejection reasons")
        print("   - Helpful next steps for the customer")
        print("   - Professional closing with support team signature")
        print("   - Beautiful HTML formatting")
    else:
        print("❌ REJECTION EMAIL TEST FAILED!")
        print("❌ Check the error messages above")
    
    return success

if __name__ == "__main__":
    test_rejection_email()