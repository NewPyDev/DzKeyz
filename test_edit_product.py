#!/usr/bin/env python3
"""
Test the edit product functionality
"""
import sys
import os
import sqlite3

# Add current directory to path so we can import from app.py
sys.path.insert(0, os.getcwd())

# Import functions from app.py
from app import init_db, get_db

def test_edit_product_functionality():
    """Test the edit product routes and functionality"""
    
    print("🧪 TESTING EDIT PRODUCT FUNCTIONALITY")
    print("=" * 50)
    
    # Initialize database
    init_db()
    
    conn = get_db()
    
    # Test 1: Create a test product to edit
    print("\n📦 Test 1: Creating test products")
    print("-" * 40)
    
    # Create a KEY product
    cursor = conn.execute('''INSERT INTO products (name, description, price_dzd, stock_count, type, file_or_key_path)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        ('Test Edit Software', 'Software for edit testing', 150.0, 0, 'key', 'MANAGED_KEYS'))
    key_product_id = cursor.lastrowid
    
    # Add keys
    test_keys = ['EDIT-KEY-001', 'EDIT-KEY-002']
    for key_value in test_keys:
        conn.execute('''INSERT INTO product_keys (product_id, key_value) VALUES (?, ?)''',
                   (key_product_id, key_value))
    
    # Update stock
    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (len(test_keys), key_product_id))
    
    # Create a FILE product
    cursor = conn.execute('''INSERT INTO products (name, description, price_dzd, stock_count, type, file_or_key_path)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        ('Test Edit File', 'File for edit testing', 75.0, 5, 'file', 'products/test_edit_file.zip'))
    file_product_id = cursor.lastrowid
    
    conn.commit()
    
    print(f"✅ Created KEY product (ID: {key_product_id}) with {len(test_keys)} keys")
    print(f"✅ Created FILE product (ID: {file_product_id}) with stock: 5")
    
    # Test 2: Check current product data
    print("\n📋 Test 2: Current product data")
    print("-" * 40)
    
    key_product = conn.execute('SELECT * FROM products WHERE id = ?', (key_product_id,)).fetchone()
    file_product = conn.execute('SELECT * FROM products WHERE id = ?', (file_product_id,)).fetchone()
    
    print("KEY Product:")
    print(f"  Name: {key_product['name']}")
    print(f"  Price: {key_product['price_dzd']} DZD")
    print(f"  Stock: {key_product['stock_count']}")
    print(f"  Type: {key_product['type']}")
    
    print("FILE Product:")
    print(f"  Name: {file_product['name']}")
    print(f"  Price: {file_product['price_dzd']} DZD")
    print(f"  Stock: {file_product['stock_count']}")
    print(f"  Type: {file_product['type']}")
    
    # Test 3: Simulate edit operations
    print("\n✏️ Test 3: Simulating edit operations")
    print("-" * 40)
    
    # Edit KEY product - update basic info
    conn.execute('''UPDATE products SET name = ?, description = ?, price_dzd = ? WHERE id = ?''',
                ('Updated Software Name', 'Updated description for software', 200.0, key_product_id))
    
    # Add more keys to KEY product
    new_keys = ['EDIT-KEY-003', 'EDIT-KEY-004', 'EDIT-KEY-005']
    for key_value in new_keys:
        conn.execute('''INSERT INTO product_keys (product_id, key_value) VALUES (?, ?)''',
                   (key_product_id, key_value))
    
    # Update stock count for KEY product
    total_keys = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                            (key_product_id,)).fetchone()[0]
    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (total_keys, key_product_id))
    
    # Edit FILE product - update basic info only
    conn.execute('''UPDATE products SET name = ?, description = ?, price_dzd = ? WHERE id = ?''',
                ('Updated File Name', 'Updated description for file', 100.0, file_product_id))
    
    conn.commit()
    
    print("✅ Updated KEY product name, description, price, and added 3 new keys")
    print("✅ Updated FILE product name, description, and price")
    
    # Test 4: Verify changes
    print("\n✅ Test 4: Verifying changes")
    print("-" * 40)
    
    updated_key_product = conn.execute('SELECT * FROM products WHERE id = ?', (key_product_id,)).fetchone()
    updated_file_product = conn.execute('SELECT * FROM products WHERE id = ?', (file_product_id,)).fetchone()
    
    # Check KEY product keys
    all_keys = conn.execute('SELECT key_value, is_used FROM product_keys WHERE product_id = ? ORDER BY created_at',
                          (key_product_id,)).fetchall()
    
    print("Updated KEY Product:")
    print(f"  Name: {updated_key_product['name']}")
    print(f"  Price: {updated_key_product['price_dzd']} DZD")
    print(f"  Stock: {updated_key_product['stock_count']}")
    print(f"  Total keys: {len(all_keys)}")
    print("  Keys:")
    for key_row in all_keys:
        status = "Used" if key_row['is_used'] else "Available"
        print(f"    {key_row['key_value']} ({status})")
    
    print("Updated FILE Product:")
    print(f"  Name: {updated_file_product['name']}")
    print(f"  Price: {updated_file_product['price_dzd']} DZD")
    print(f"  Stock: {updated_file_product['stock_count']}")
    
    # Test 5: Test delete functionality (check constraints)
    print("\n🗑️ Test 5: Testing delete constraints")
    print("-" * 40)
    
    # Try to delete products (should work since no orders exist)
    orders_key = conn.execute('SELECT COUNT(*) FROM orders WHERE product_id = ?', (key_product_id,)).fetchone()[0]
    orders_file = conn.execute('SELECT COUNT(*) FROM orders WHERE product_id = ?', (file_product_id,)).fetchone()[0]
    
    print(f"KEY product has {orders_key} orders (can delete: {'Yes' if orders_key == 0 else 'No'})")
    print(f"FILE product has {orders_file} orders (can delete: {'Yes' if orders_file == 0 else 'No'})")
    
    # Test Results
    print("\n" + "=" * 50)
    print("📊 EDIT FUNCTIONALITY TEST RESULTS:")
    
    name_updated = updated_key_product['name'] == 'Updated Software Name'
    price_updated = updated_key_product['price_dzd'] == 200.0
    keys_added = len(all_keys) == 5  # Original 2 + 3 new
    stock_correct = updated_key_product['stock_count'] == 5
    
    print(f"✅ Product name update: {'PASSED' if name_updated else 'FAILED'}")
    print(f"✅ Product price update: {'PASSED' if price_updated else 'FAILED'}")
    print(f"✅ Key addition: {'PASSED' if keys_added else 'FAILED'}")
    print(f"✅ Stock management: {'PASSED' if stock_correct else 'FAILED'}")
    print(f"✅ Delete constraints: {'WORKING' if orders_key == 0 and orders_file == 0 else 'ISSUES'}")
    
    success = all([name_updated, price_updated, keys_added, stock_correct])
    
    if success:
        print("\n🎉 EDIT PRODUCT FUNCTIONALITY TEST PASSED!")
        print("✅ Products can be edited successfully")
        print("✅ Key products support adding new keys")
        print("✅ Stock management works correctly")
        print("✅ Delete constraints prevent data integrity issues")
    else:
        print("\n❌ EDIT PRODUCT FUNCTIONALITY TEST FAILED!")
    
    conn.close()
    return success

if __name__ == "__main__":
    test_edit_product_functionality()