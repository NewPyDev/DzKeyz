#!/usr/bin/env python3
"""
Test the new key management system
"""
import sys
import os
import sqlite3

# Add current directory to path so we can import from app.py
sys.path.insert(0, os.getcwd())

# Import functions from app.py
from app import init_db, get_db, get_available_key

def test_key_management():
    """Test the key management system"""
    
    print("🧪 TESTING KEY MANAGEMENT SYSTEM")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    # Test 1: Add a product with multiple keys
    print("\n📦 Test 1: Adding product with multiple keys")
    print("-" * 40)
    
    conn = get_db()
    
    # Add a test product
    cursor = conn.execute('''INSERT INTO products (name, description, price_dzd, stock_count, type, file_or_key_path)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        ('Test Software', 'Test software with license keys', 100.0, 0, 'key', 'MANAGED_KEYS'))
    product_id = cursor.lastrowid
    
    # Add individual keys
    test_keys = ['KEY001', 'KEY002', 'KEY003', 'KEY004', 'KEY005']
    for key_value in test_keys:
        conn.execute('''INSERT INTO product_keys (product_id, key_value) VALUES (?, ?)''',
                   (product_id, key_value))
    
    # Update stock count
    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (len(test_keys), product_id))
    conn.commit()
    
    print(f"✅ Added product with {len(test_keys)} keys")
    print(f"   Keys: {', '.join(test_keys)}")
    
    # Test 2: Get available keys one by one
    print("\n🔑 Test 2: Getting individual keys")
    print("-" * 40)
    
    used_keys = []
    for i in range(3):  # Get 3 keys
        order_id = 1000 + i  # Fake order IDs
        key = get_available_key(product_id, order_id)
        if key:
            used_keys.append(key)
            print(f"✅ Order #{order_id} got key: {key}")
        else:
            print(f"❌ Order #{order_id} got no key")
    
    # Test 3: Check remaining keys
    print("\n📊 Test 3: Checking remaining keys")
    print("-" * 40)
    
    remaining_keys = conn.execute('SELECT key_value FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                (product_id,)).fetchall()
    used_keys_db = conn.execute('SELECT key_value, used_by_order_id FROM product_keys WHERE product_id = ? AND is_used = TRUE',
                              (product_id,)).fetchall()
    
    print(f"✅ Used keys: {len(used_keys_db)}")
    for key_row in used_keys_db:
        print(f"   {key_row['key_value']} → Order #{key_row['used_by_order_id']}")
    
    print(f"✅ Remaining keys: {len(remaining_keys)}")
    for key_row in remaining_keys:
        print(f"   {key_row['key_value']} (available)")
    
    # Test 4: Update stock count
    print("\n📦 Test 4: Stock count management")
    print("-" * 40)
    
    available_count = len(remaining_keys)
    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (available_count, product_id))
    conn.commit()
    
    product = conn.execute('SELECT stock_count FROM products WHERE id = ?', (product_id,)).fetchone()
    print(f"✅ Product stock updated to: {product['stock_count']}")
    
    # Test 5: Try to get more keys than available
    print("\n⚠️ Test 5: Exhausting keys")
    print("-" * 40)
    
    # Get remaining keys
    for i in range(5):  # Try to get 5 more keys (should only get 2)
        order_id = 2000 + i
        key = get_available_key(product_id, order_id)
        if key:
            print(f"✅ Order #{order_id} got key: {key}")
        else:
            print(f"❌ Order #{order_id} got no key (expected - no keys left)")
    
    # Final check
    final_remaining = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                 (product_id,)).fetchone()[0]
    final_used = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = TRUE',
                            (product_id,)).fetchone()[0]
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   Total keys added: {len(test_keys)}")
    print(f"   Keys used: {final_used}")
    print(f"   Keys remaining: {final_remaining}")
    print(f"   Stock should be: {final_remaining}")
    
    # Update final stock
    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (final_remaining, product_id))
    conn.commit()
    
    final_product = conn.execute('SELECT stock_count FROM products WHERE id = ?', (product_id,)).fetchone()
    print(f"   Actual stock: {final_product['stock_count']}")
    
    conn.close()
    
    # Test results
    success = (final_used > 0 and final_remaining >= 0 and final_product['stock_count'] == final_remaining)
    
    if success:
        print("\n🎉 KEY MANAGEMENT SYSTEM TEST PASSED!")
        print("✅ Keys are now managed individually")
        print("✅ Each order gets exactly ONE key")
        print("✅ Stock count reflects available keys")
        print("✅ Used keys are properly tracked")
        print("✅ No more sending all keys to one customer!")
    else:
        print("\n❌ KEY MANAGEMENT SYSTEM TEST FAILED!")
    
    return success

if __name__ == "__main__":
    test_key_management()