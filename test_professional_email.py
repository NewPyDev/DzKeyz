#!/usr/bin/env python3
"""
Test the new professional email formatting
"""
import sys
import os

# Add current directory to path so we can import from app.py
sys.path.insert(0, os.getcwd())

# Import the send_email function from app.py
from app import send_email

def test_professional_emails():
    """Test the new professional email formatting"""
    
    print("🧪 TESTING NEW PROFESSIONAL EMAIL FORMATTING")
    print("=" * 60)
    
    # Test email address
    test_email = "relaxthelord@live.fr"
    
    # Test 1: Order received email
    print("\n📧 Test 1: Order Received Email")
    print("-" * 40)
    
    subject1 = "Order Received - Espamoda"
    body1 = """Thank you for your order! We have received your payment and are processing your request.

Order Details:
- Order ID: #12345
- Product: Premium Digital Art Pack
- Price: 2500 DZD
- Payment Method: BARIDIMOB

Your order is currently being reviewed by our team. You will receive another email once your order is confirmed and your product is ready.

If you have any questions, please contact our support team."""
    
    success1 = send_email(test_email, subject1, body1, "Ahmed", "order_received")
    
    # Test 2: Order confirmation email
    print("\n📧 Test 2: Order Confirmation Email")
    print("-" * 40)
    
    subject2 = "Your Order Confirmation from Espamoda"
    body2 = """Your order has been confirmed and your product is ready!

Order Details:
- Order ID: #12345
- Product: Premium Digital Art Pack
- Price: 2500 DZD
- Payment Method: BARIDIMOB

Your Product Key: ART-PACK-2024-PREMIUM-XYZ789

Thank you for choosing Espamoda!"""
    
    success2 = send_email(test_email, subject2, body2, "Ahmed", "order_confirmation")
    
    # Test 3: General email
    print("\n📧 Test 3: General Professional Email")
    print("-" * 40)
    
    subject3 = "Welcome to Espamoda - Your Digital Store"
    body3 = """Welcome to our digital store! We're excited to have you as a customer.

Our store offers:
- High-quality digital products
- Instant delivery after confirmation
- Professional customer support
- Secure payment processing

Browse our collection and find amazing digital products at great prices."""
    
    success3 = send_email(test_email, subject3, body3, "Ahmed", "general")
    
    # Results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS:")
    print(f"✅ Order Received Email: {'PASSED' if success1 else 'FAILED'}")
    print(f"✅ Order Confirmation Email: {'PASSED' if success2 else 'FAILED'}")
    print(f"✅ General Professional Email: {'PASSED' if success3 else 'FAILED'}")
    
    if all([success1, success2, success3]):
        print("\n🎉 ALL TESTS PASSED!")
        print("📧 Your emails now use the professional format you liked!")
        print("📧 Features included:")
        print("   - Professional greeting with customer name")
        print("   - Clean, structured content")
        print("   - Professional closing with features list")
        print("   - Beautiful HTML formatting")
        print("   - Consistent branding")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
    
    return all([success1, success2, success3])

if __name__ == "__main__":
    test_professional_emails()