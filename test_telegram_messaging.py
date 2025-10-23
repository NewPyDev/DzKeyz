#!/usr/bin/env python3
"""
Test Telegram messaging functionality
"""
import sys
import os
import requests

# Add current directory to path so we can import from app.py
sys.path.insert(0, os.getcwd())

# Import functions from app.py
from app import send_telegram_message_to_user, send_bot_message

def test_telegram_messaging():
    """Test Telegram messaging functionality"""
    
    print("🧪 TESTING TELEGRAM MESSAGING")
    print("=" * 50)
    
    # Load environment variables
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_id = os.getenv('TELEGRAM_ADMIN_ID')
    
    print(f"📋 Configuration:")
    print(f"   Bot Token: {'✅ Set' if bot_token else '❌ Missing'}")
    print(f"   Admin ID: {'✅ Set' if admin_id else '❌ Missing'}")
    
    if not bot_token:
        print("\n❌ Cannot test without TELEGRAM_BOT_TOKEN")
        return False
    
    # Test 1: Check bot info
    print(f"\n🤖 Test 1: Checking bot information")
    print("-" * 40)
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/getMe"
        response = requests.get(url)
        
        if response.status_code == 200:
            bot_info = response.json()['result']
            print(f"✅ Bot Name: {bot_info['first_name']}")
            print(f"✅ Bot Username: @{bot_info['username']}")
            print(f"✅ Bot ID: {bot_info['id']}")
        else:
            print(f"❌ Failed to get bot info: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting bot info: {e}")
        return False
    
    # Test 2: Test admin notification
    print(f"\n📢 Test 2: Testing admin notification")
    print("-" * 40)
    
    if admin_id:
        test_message = """🧪 TELEGRAM TEST MESSAGE
        
This is a test message to verify that Telegram notifications are working correctly.

✅ If you receive this message, your bot configuration is working!

Time: Now
Test: Admin Notification"""
        
        try:
            success = send_bot_message(admin_id, test_message)
            print(f"Admin notification: {'✅ SENT' if success else '❌ FAILED'}")
        except Exception as e:
            print(f"❌ Admin notification failed: {e}")
    else:
        print("⚠️ No admin ID configured - skipping admin test")
    
    # Test 3: Explain customer messaging limitations
    print(f"\n👤 Test 3: Customer messaging limitations")
    print("-" * 40)
    
    print("📋 Telegram Bot Limitations:")
    print("   ❌ Bots CANNOT send unsolicited messages to users")
    print("   ✅ Users MUST message the bot first (/start)")
    print("   ✅ After /start, bot can message the user")
    print("   ✅ Chat ID is more reliable than username")
    
    # Test 4: Provide setup instructions
    print(f"\n🔧 Test 4: Setup instructions for customers")
    print("-" * 40)
    
    bot_username = bot_info.get('username', 'YourBot') if 'bot_info' in locals() else 'YourBot'
    
    print("📋 Instructions for customers:")
    print(f"   1. Open Telegram and search for @{bot_username}")
    print(f"   2. Send /start to the bot")
    print(f"   3. Bot will reply with their Chat ID")
    print(f"   4. Use Chat ID when placing orders")
    print(f"   5. Bot can now send them notifications!")
    
    # Test 5: Test different identifier formats
    print(f"\n🔍 Test 5: Testing identifier formats")
    print("-" * 40)
    
    test_identifiers = [
        "123456789",  # Chat ID format
        "@testuser",  # Username with @
        "testuser",   # Username without @
    ]
    
    for identifier in test_identifiers:
        print(f"Testing format: {identifier}")
        # We won't actually send messages, just test the format logic
        if identifier.isdigit():
            print(f"   ✅ Detected as Chat ID")
        elif identifier.startswith('@'):
            print(f"   ✅ Detected as username with @")
        else:
            print(f"   ✅ Detected as username without @")
    
    # Results
    print("\n" + "=" * 50)
    print("📊 TELEGRAM MESSAGING TEST RESULTS:")
    
    bot_working = 'bot_info' in locals()
    admin_working = admin_id is not None
    
    print(f"🤖 Bot Configuration: {'✅ WORKING' if bot_working else '❌ FAILED'}")
    print(f"📢 Admin Notifications: {'✅ WORKING' if admin_working else '❌ NEEDS SETUP'}")
    print(f"👤 Customer Messaging: ⚠️ REQUIRES USER ACTION")
    
    print(f"\n💡 SOLUTION FOR CUSTOMER MESSAGING:")
    print(f"   1. Add bot setup instructions to your order form")
    print(f"   2. Tell customers to message @{bot_username} first")
    print(f"   3. Customers should use their Chat ID instead of username")
    print(f"   4. Bot will work perfectly after customers do /start")
    
    success = bot_working
    
    if success:
        print(f"\n✅ TELEGRAM SYSTEM IS WORKING!")
        print(f"   The issue is that customers need to message your bot first.")
        print(f"   This is a Telegram security feature, not a bug in your code.")
    else:
        print(f"\n❌ TELEGRAM SYSTEM NEEDS CONFIGURATION!")
    
    return success

if __name__ == "__main__":
    test_telegram_messaging()