#!/usr/bin/env python3
"""
Setup script for Digital Products Store
Run this script to initialize the application
"""

import os
import sqlite3
from werkzeug.security import generate_password_hash

def create_directories():
    """Create necessary directories"""
    directories = ['uploads', 'products', 'static', 'templates']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def setup_database():
    """Initialize the database with tables"""
    conn = sqlite3.connect('store.db')
    c = conn.cursor()
    
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price_dzd REAL NOT NULL,
        stock_count INTEGER DEFAULT 0,
        type TEXT CHECK(type IN ('key', 'file')) NOT NULL,
        file_or_key_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        buyer_name TEXT NOT NULL,
        email TEXT NOT NULL,
        telegram_username TEXT,
        payment_method TEXT CHECK(payment_method IN ('baridimob', 'ccp')),
        payment_proof_path TEXT,
        transaction_id TEXT,
        status TEXT CHECK(status IN ('pending', 'confirmed', 'rejected')) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        confirmed_at TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    
    # Audit log table
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER,
        action TEXT NOT NULL,
        actor TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        note TEXT,
        FOREIGN KEY (order_id) REFERENCES orders (id)
    )''')
    
    # Admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')
    
    # Create default admin if not exists
    c.execute('SELECT COUNT(*) FROM admin')
    if c.fetchone()[0] == 0:
        admin_hash = generate_password_hash('admin123')
        c.execute('INSERT INTO admin (username, password_hash) VALUES (?, ?)', ('admin', admin_hash))
        print("✓ Created default admin user (admin/admin123)")
    
    conn.commit()
    conn.close()
    print("✓ Database initialized successfully")

def create_sample_product():
    """Create a sample product for testing"""
    conn = sqlite3.connect('store.db')
    c = conn.cursor()
    
    # Check if sample product already exists
    c.execute('SELECT COUNT(*) FROM products WHERE name = ?', ('Sample Software Key',))
    if c.fetchone()[0] == 0:
        c.execute('''INSERT INTO products (name, description, price_dzd, stock_count, type, file_or_key_path)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                 ('Sample Software Key', 'A sample software license key for testing', 500.0, 5, 'key', 'SAMPLE-KEY-12345-ABCDE'))
        print("✓ Created sample product")
    
    conn.commit()
    conn.close()

def check_env_file():
    """Check if .env file exists and has required variables"""
    if not os.path.exists('.env'):
        print("⚠ Warning: .env file not found. Please create it with your configuration.")
        return False
    
    required_vars = ['SECRET_KEY', 'TELEGRAM_BOT_TOKEN', 'TELEGRAM_ADMIN_ID']
    missing_vars = []
    
    with open('.env', 'r') as f:
        content = f.read()
        for var in required_vars:
            if f"{var}=" not in content or f"{var}=your-" in content:
                missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠ Warning: Please configure these variables in .env: {', '.join(missing_vars)}")
        return False
    
    print("✓ Environment configuration looks good")
    return True

def main():
    print("🚀 Setting up Digital Products Store...")
    print("=" * 50)
    
    # Create directories
    create_directories()
    
    # Setup database
    setup_database()
    
    # Create sample product
    create_sample_product()
    
    # Check environment
    env_ok = check_env_file()
    
    print("=" * 50)
    print("✅ Setup completed!")
    print()
    print("Next steps:")
    print("1. Configure your .env file with Telegram bot credentials")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run the application: python app.py")
    print("4. Visit http://localhost:5000")
    print("5. Login to admin panel with: admin/admin123")
    print()
    
    if not env_ok:
        print("⚠ Don't forget to configure your .env file!")

if __name__ == '__main__':
    main()