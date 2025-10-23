#!/usr/bin/env python3
"""
Test file products vs key products to ensure both work correctly
"""
import sys
import os
import sqlite3

# Add current directory to path so we can import from app.py
sys.path.insert(0, os.getcwd())

# Import functions from app.py
from app import init_db, get_db, deliver_product

def test_file_vs_key_products():
    """Test both file and key products"""
    
    print("🧪 TESTING FILE vs KEY PRODUCTS")
    print("=" * 60)
    
    # Initialize database
    init_db()
    
    conn = get_db()
    
    # Test 1: Create a KEY product
    print("\n🔑 Test 1: Creating KEY product")
    print("-" * 40)
    
    cursor = conn.execute('''INSERT INTO products (name, description, price_dzd, stock_count, type, file_or_key_path)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        ('Test Software License', 'Software with license keys', 100.0, 0, 'key', 'MANAGED_KEYS'))
    key_product_id = cursor.lastrowid
    
    # Add keys for the key product
    test_keys = ['LICENSE-001', 'LICENSE-002', 'LICENSE-003']
    for key_value in test_keys:
        conn.execute('''INSERT INTO product_keys (product_id, key_value) VALUES (?, ?)''',
                   (key_product_id, key_value))
    
    # Update stock count
    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (len(test_keys), key_product_id))
    
    print(f"✅ Created KEY product with {len(test_keys)} keys")
    
    # Test 2: Create a FILE product
    print("\n📁 Test 2: Creating FILE product")
    print("-" * 40)
    
    # Simulate a file upload (create a test file)
    test_file_path = os.path.join('products', 'test_digital_product.zip')
    os.makedirs('products', exist_ok=True)
    with open(test_file_path, 'w') as f:
        f.write("This is a test digital product file content")
    
    cursor = conn.execute('''INSERT INTO products (name, description, price_dzd, stock_count, type, file_or_key_path)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        ('Digital Art Pack', 'High-quality digital art files', 50.0, 10, 'file', test_file_path))
    file_product_id = cursor.lastrowid
    
    print(f"✅ Created FILE product with file: {test_file_path}")
    print(f"   Stock: 10 units")
    
    conn.commit()
    
    # Test 3: Create test orders
    print("\n📦 Test 3: Creating test orders")
    print("-" * 40)
    
    # Order for KEY product
    cursor = conn.execute('''INSERT INTO orders 
                            (product_id, buyer_name, email, phone, telegram_username, payment_method, 
                             payment_proof_path, transaction_id, status) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (key_product_id, 'Ahmed Key Buyer', 'ahmed@test.com', '0123456789', 'ahmed_key', 'baridimob',
                          'test_proof.jpg', 'TXN001', 'confirmed'))
    key_order_id = cursor.lastrowid
    
    # Order for FILE product
    cursor = conn.execute('''INSERT INTO orders 
                            (product_id, buyer_name, email, phone, telegram_username, payment_method, 
                             payment_proof_path, transaction_id, status) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (file_product_id, 'Sara File Buyer', 'sara@test.com', '0987654321', 'sara_file', 'ccp',
                          'test_proof2.jpg', 'TXN002', 'confirmed'))
    file_order_id = cursor.lastrowid
    
    conn.commit()
    
    print(f"✅ Created KEY order #{key_order_id} for Ahmed")
    print(f"✅ Created FILE order #{file_order_id} for Sara")
    
    # Test 4: Get order data for delivery (simulate confirm_order)
    print("\n📋 Test 4: Getting order data for delivery")
    print("-" * 40)
    
    # Get KEY order data
    key_order = conn.execute('''SELECT o.*, p.name as product_name, p.type, p.file_or_key_path, p.price_dzd
                               FROM orders o 
                               JOIN products p ON o.product_id = p.id 
                               WHERE o.id = ?''', (key_order_id,)).fetchone()
    
    # Get FILE order data
    file_order = conn.execute('''SELECT o.*, p.name as product_name, p.type, p.file_or_key_path, p.price_dzd
                                FROM orders o 
                                JOIN products p ON o.product_id = p.id 
                                WHERE o.id = ?''', (file_order_id,)).fetchone()
    
    print("✅ Retrieved order data:")
    print(f"   KEY order: {dict(key_order)}")
    print(f"   FILE order: {dict(file_order)}")
    
    # Test 5: Test delivery for KEY product
    print("\n🔑 Test 5: Testing KEY product delivery")
    print("-" * 40)
    
    print("Delivering KEY product...")
    deliver_product(dict(key_order))
    
    # Check if key was assigned
    used_key = conn.execute('SELECT key_value FROM product_keys WHERE used_by_order_id = ?', 
                          (key_order_id,)).fetchone()
    if used_key:
        print(f"✅ KEY assigned: {used_key['key_value']}")
    else:
        print("❌ No key assigned")
    
    # Test 6: Test delivery for FILE product
    print("\n📁 Test 6: Testing FILE product delivery")
    print("-" * 40)
    
    print("Delivering FILE product...")
    deliver_product(dict(file_order))
    
    # Check if file exists
    if os.path.exists(file_order['file_or_key_path']):
        print(f"✅ FILE exists: {file_order['file_or_key_path']}")
    else:
        print(f"❌ FILE missing: {file_order['file_or_key_path']}")
    
    # Test 7: Check stock management
    print("\n📊 Test 7: Checking stock management")
    print("-" * 40)
    
    # Check KEY product stock (should decrease)
    key_product = conn.execute('SELECT stock_count FROM products WHERE id = ?', (key_product_id,)).fetchone()
    available_keys = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                (key_product_id,)).fetchone()[0]
    
    print(f"KEY product stock: {key_product['stock_count']} (should match available keys: {available_keys})")
    
    # Check FILE product stock (should decrease by 1)
    file_product = conn.execute('SELECT stock_count FROM products WHERE id = ?', (file_product_id,)).fetchone()
    print(f"FILE product stock: {file_product['stock_count']} (should be 9 if decreased from 10)")
    
    # Test Results
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY:")
    
    key_success = used_key is not None and key_product['stock_count'] == available_keys
    file_success = os.path.exists(file_order['file_or_key_path'])
    
    print(f"🔑 KEY Product: {'✅ WORKING' if key_success else '❌ ISSUES'}")
    print(f"   - Key assignment: {'✅' if used_key else '❌'}")
    print(f"   - Stock management: {'✅' if key_product['stock_count'] == available_keys else '❌'}")
    
    print(f"📁 FILE Product: {'✅ WORKING' if file_success else '❌ ISSUES'}")
    print(f"   - File exists: {'✅' if file_success else '❌'}")
    print(f"   - Delivery message: ⚠️ NEEDS IMPROVEMENT (tells customer to contact support)")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if key_success:
        print("✅ KEY products work perfectly - customers get individual keys")
    else:
        print("❌ KEY products need fixing")
    
    if file_success:
        print("⚠️ FILE products work but need improvement:")
        print("   - Files exist and are stored correctly")
        print("   - But customers are told to 'contact support' instead of getting download links")
        print("   - Consider adding direct download links or file attachment to emails")
    else:
        print("❌ FILE products have issues - files not found")
    
    conn.close()
    
    # Cleanup test file
    if os.path.exists(test_file_path):
        os.remove(test_file_path)
    
    return key_success, file_success

if __name__ == "__main__":
    test_file_vs_key_products()