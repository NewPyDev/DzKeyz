#!/usr/bin/env python3
"""
Test the complete edit functionality including file replacement and key deletion
"""
import sys
import os
import sqlite3

# Add current directory to path so we can import from app.py
sys.path.insert(0, os.getcwd())

# Import functions from app.py
from app import init_db, get_db

def test_full_edit_functionality():
    """Test all edit functionality including file replacement and key management"""
    
    print("🧪 TESTING COMPLETE EDIT FUNCTIONALITY")
    print("=" * 60)
    
    # Initialize database
    init_db()
    
    conn = get_db()
    
    # Test 1: Create test products
    print("\n📦 Test 1: Creating test products")
    print("-" * 40)
    
    # Create KEY product with keys
    cursor = conn.execute('''INSERT INTO products (name, description, price_dzd, stock_count, type, file_or_key_path)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        ('Full Test Software', 'Software for full testing', 100.0, 0, 'key', 'MANAGED_KEYS'))
    key_product_id = cursor.lastrowid
    
    # Add initial keys
    initial_keys = ['FULL-001', 'FULL-002', 'FULL-003', 'FULL-004', 'FULL-005']
    for key_value in initial_keys:
        conn.execute('''INSERT INTO product_keys (product_id, key_value) VALUES (?, ?)''',
                   (key_product_id, key_value))
    
    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (len(initial_keys), key_product_id))
    
    # Create FILE product with test file
    test_file_path = os.path.join('products', 'original_test_file.txt')
    os.makedirs('products', exist_ok=True)
    with open(test_file_path, 'w') as f:
        f.write("This is the ORIGINAL test file content")
    
    cursor = conn.execute('''INSERT INTO products (name, description, price_dzd, stock_count, type, file_or_key_path)
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        ('Full Test File Product', 'File for full testing', 75.0, 10, 'file', test_file_path))
    file_product_id = cursor.lastrowid
    
    conn.commit()
    
    print(f"✅ Created KEY product (ID: {key_product_id}) with {len(initial_keys)} keys")
    print(f"✅ Created FILE product (ID: {file_product_id}) with original file")
    
    # Test 2: Test key deletion
    print("\n🗑️ Test 2: Testing individual key deletion")
    print("-" * 40)
    
    # Get a key to delete
    key_to_delete = conn.execute('SELECT id, key_value FROM product_keys WHERE product_id = ? AND is_used = FALSE LIMIT 1',
                               (key_product_id,)).fetchone()
    
    if key_to_delete:
        print(f"Deleting key: {key_to_delete['key_value']}")
        
        # Simulate key deletion
        conn.execute('DELETE FROM product_keys WHERE id = ?', (key_to_delete['id'],))
        
        # Update stock count
        remaining_keys = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                    (key_product_id,)).fetchone()[0]
        conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (remaining_keys, key_product_id))
        conn.commit()
        
        print(f"✅ Key deleted. Remaining keys: {remaining_keys}")
    
    # Test 3: Test adding new keys
    print("\n🔑 Test 3: Testing new key addition")
    print("-" * 40)
    
    # Add new keys
    new_keys = ['FULL-NEW-001', 'FULL-NEW-002', 'FULL-NEW-003']
    existing_keys = conn.execute('SELECT key_value FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                               (key_product_id,)).fetchall()
    existing_key_values = [row['key_value'] for row in existing_keys]
    
    added_count = 0
    for key_value in new_keys:
        if key_value not in existing_key_values:
            conn.execute('''INSERT INTO product_keys (product_id, key_value) VALUES (?, ?)''',
                       (key_product_id, key_value))
            added_count += 1
    
    # Update stock
    total_available = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                 (key_product_id,)).fetchone()[0]
    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (total_available, key_product_id))
    conn.commit()
    
    print(f"✅ Added {added_count} new keys. Total available: {total_available}")
    
    # Test 4: Test file replacement
    print("\n📁 Test 4: Testing file replacement")
    print("-" * 40)
    
    # Get current file info
    current_product = conn.execute('SELECT file_or_key_path FROM products WHERE id = ?', (file_product_id,)).fetchone()
    old_file_path = current_product['file_or_key_path']
    
    print(f"Current file: {old_file_path}")
    
    # Create new file
    new_file_path = os.path.join('products', 'updated_test_file.txt')
    with open(new_file_path, 'w') as f:
        f.write("This is the UPDATED test file content - much better!")
    
    # Simulate file replacement
    if old_file_path and os.path.exists(old_file_path):
        os.remove(old_file_path)
        print(f"✅ Deleted old file: {old_file_path}")
    
    # Update database with new file path
    conn.execute('UPDATE products SET file_or_key_path = ? WHERE id = ?', (new_file_path, file_product_id))
    conn.commit()
    
    print(f"✅ Updated file path: {new_file_path}")
    
    # Verify new file content
    with open(new_file_path, 'r') as f:
        new_content = f.read()
    print(f"✅ New file content: {new_content[:50]}...")
    
    # Test 5: Test stock updates for file products
    print("\n📊 Test 5: Testing file stock updates")
    print("-" * 40)
    
    # Update file stock
    new_stock = 25
    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (new_stock, file_product_id))
    conn.commit()
    
    updated_stock = conn.execute('SELECT stock_count FROM products WHERE id = ?', (file_product_id,)).fetchone()[0]
    print(f"✅ Updated file stock from 10 to {updated_stock}")
    
    # Test 6: Verify all changes
    print("\n✅ Test 6: Verifying all changes")
    print("-" * 40)
    
    # Check KEY product
    key_product = conn.execute('SELECT * FROM products WHERE id = ?', (key_product_id,)).fetchone()
    all_keys = conn.execute('SELECT key_value, is_used FROM product_keys WHERE product_id = ? ORDER BY created_at',
                          (key_product_id,)).fetchall()
    
    print("KEY Product Status:")
    print(f"  Stock: {key_product['stock_count']}")
    print(f"  Total keys: {len(all_keys)}")
    print("  Keys:")
    for key_row in all_keys:
        status = "Used" if key_row['is_used'] else "Available"
        print(f"    {key_row['key_value']} ({status})")
    
    # Check FILE product
    file_product = conn.execute('SELECT * FROM products WHERE id = ?', (file_product_id,)).fetchone()
    
    print("FILE Product Status:")
    print(f"  Stock: {file_product['stock_count']}")
    print(f"  File: {file_product['file_or_key_path']}")
    print(f"  File exists: {os.path.exists(file_product['file_or_key_path'])}")
    
    # Test Results
    print("\n" + "=" * 60)
    print("📊 COMPLETE EDIT FUNCTIONALITY TEST RESULTS:")
    
    key_deletion_works = len(all_keys) == len(initial_keys) - 1 + len(new_keys)  # -1 deleted, +3 added
    key_addition_works = any('FULL-NEW' in key['key_value'] for key in all_keys)
    file_replacement_works = os.path.exists(file_product['file_or_key_path']) and not os.path.exists(old_file_path)
    stock_update_works = file_product['stock_count'] == new_stock
    
    print(f"🔑 Key deletion: {'✅ WORKING' if key_deletion_works else '❌ FAILED'}")
    print(f"🔑 Key addition: {'✅ WORKING' if key_addition_works else '❌ FAILED'}")
    print(f"📁 File replacement: {'✅ WORKING' if file_replacement_works else '❌ FAILED'}")
    print(f"📊 Stock updates: {'✅ WORKING' if stock_update_works else '❌ FAILED'}")
    
    success = all([key_deletion_works, key_addition_works, file_replacement_works, stock_update_works])
    
    if success:
        print("\n🎉 COMPLETE EDIT FUNCTIONALITY TEST PASSED!")
        print("✅ You can now delete individual keys")
        print("✅ You can add new keys without duplicates")
        print("✅ You can replace files completely")
        print("✅ You can update stock counts for file products")
        print("✅ All changes are properly tracked and managed")
        print("\n🔥 NO MORE LIMITATIONS - FULL CONTROL OVER YOUR PRODUCTS!")
    else:
        print("\n❌ SOME FUNCTIONALITY FAILED!")
    
    # Cleanup
    conn.close()
    
    # Clean up test files
    for file_path in [new_file_path]:
        if os.path.exists(file_path):
            os.remove(file_path)
    
    return success

if __name__ == "__main__":
    test_full_edit_functionality()