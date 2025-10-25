import os
import sqlite3
import uuid
import json
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, send_file, render_template_string
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import requests
import resend
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

load_dotenv()

app = Flask(__name__)

# Template filters
@app.template_filter('get_product_images')
def get_product_images_filter(images_string):
    return get_product_images(images_string)

@app.template_filter('from_json')
def from_json_filter(json_string):
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        # Fallback for old comma-separated format
        if json_string:
            return [img.strip() for img in json_string.split(',') if img.strip()]
        return []

# Image handling functions
ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_image_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def save_product_images(files):
    """Save multiple product images and return JSON list of filenames"""
    if not files:
        return None
    
    saved_filenames = []
    skipped_files = []
    
    for file in files:
        if file and file.filename and allowed_image_file(file.filename):
            # Check file size
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size <= MAX_IMAGE_SIZE:
                # Generate unique filename
                file_extension = file.filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
                file_path = os.path.join('static', 'products', unique_filename)
                
                file.save(file_path)
                saved_filenames.append(unique_filename)
            else:
                skipped_files.append(f"{file.filename} (too large)")
        elif file and file.filename:
            skipped_files.append(f"{file.filename} (invalid format)")
    
    if skipped_files:
        flash(f'Skipped files: {", ".join(skipped_files)}', 'warning')
    
    return json.dumps(saved_filenames) if saved_filenames else None

def delete_product_images(images_json):
    """Delete product images from filesystem"""
    if not images_json:
        return
    
    try:
        image_filenames = json.loads(images_json)
        for filename in image_filenames:
            if filename:
                file_path = os.path.join('static', 'products', filename)
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"✅ Deleted image: {filename}")
                except Exception as e:
                    print(f"⚠️ Could not delete image {filename}: {e}")
    except json.JSONDecodeError:
        # Fallback for old comma-separated format
        image_filenames = images_json.split(',')
        for filename in image_filenames:
            if filename.strip():
                file_path = os.path.join('static', 'products', filename.strip())
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"✅ Deleted image: {filename}")
                except Exception as e:
                    print(f"⚠️ Could not delete image {filename}: {e}")

def get_product_images(images_json):
    """Convert JSON string to list of image URLs"""
    if not images_json:
        return []
    
    try:
        image_filenames = json.loads(images_json)
        return [f"/static/products/{img}" for img in image_filenames if img]
    except json.JSONDecodeError:
        # Fallback for old comma-separated format
        return [f"/static/products/{img.strip()}" for img in images_json.split(',') if img.strip()]

def get_categories():
    """Get all categories"""
    conn = get_db()
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    conn.close()
    return [dict(cat) for cat in categories]

def get_tags():
    """Get all tags"""
    conn = get_db()
    tags = conn.execute('SELECT * FROM tags ORDER BY name').fetchall()
    conn.close()
    return [dict(tag) for tag in tags]

def get_product_tags(product_id):
    """Get tags for a specific product"""
    conn = get_db()
    tags = conn.execute('''
        SELECT t.* FROM tags t
        JOIN product_tags pt ON t.id = pt.tag_id
        WHERE pt.product_id = ?
        ORDER BY t.name
    ''', (product_id,)).fetchall()
    conn.close()
    return [dict(tag) for tag in tags]

def get_bundles():
    """Get all bundles with their products"""
    conn = get_db()
    bundles = conn.execute('SELECT * FROM bundles ORDER BY name').fetchall()
    bundle_list = []
    
    for bundle in bundles:
        bundle_dict = dict(bundle)
        # Get products in this bundle
        products = conn.execute('''
            SELECT p.* FROM products p
            JOIN bundle_products bp ON p.id = bp.product_id
            WHERE bp.bundle_id = ?
        ''', (bundle['id'],)).fetchall()
        bundle_dict['products'] = [dict(p) for p in products]
        bundle_dict['image_urls'] = get_product_images(bundle['images'])
        bundle_dict['main_image'] = bundle_dict['image_urls'][0] if bundle_dict['image_urls'] else None
        bundle_list.append(bundle_dict)
    
    conn.close()
    return bundle_list

def calculate_bundle_price(bundle_id):
    """Calculate the total price of a bundle with discount"""
    conn = get_db()
    
    # Get bundle info
    bundle = conn.execute('SELECT * FROM bundles WHERE id = ?', (bundle_id,)).fetchone()
    if not bundle:
        return 0
    
    # Get total price of all products in bundle
    total_price = conn.execute('''
        SELECT SUM(p.price_dzd) FROM products p
        JOIN bundle_products bp ON p.id = bp.product_id
        WHERE bp.bundle_id = ?
    ''', (bundle_id,)).fetchone()[0] or 0
    
    conn.close()
    
    # Apply discount
    if bundle['discount_percentage'] > 0:
        discount = total_price * (bundle['discount_percentage'] / 100)
        return max(0, total_price - discount)
    elif bundle['discount_amount'] > 0:
        return max(0, total_price - bundle['discount_amount'])
    
    return total_price
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['PRODUCTS_FOLDER'] = 'products'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['STORE_NAME'] = os.getenv('STORE_NAME', 'Digital Store')
app.config['BASE_URL'] = os.getenv('BASE_URL', 'https://dzkeyz.onrender.com')
app.config['CONTACT_EMAIL'] = os.getenv('CONTACT_EMAIL', 'support@yourdomain.com')
app.config['TELEGRAM_LINK'] = os.getenv('TELEGRAM_LINK', 'https://t.me/StockilyBot')

# Ensure directories exist
os.makedirs('uploads', exist_ok=True)
os.makedirs('products', exist_ok=True)
os.makedirs('static', exist_ok=True)
os.makedirs('static/products', exist_ok=True)
os.makedirs('templates', exist_ok=True)
os.makedirs('receipts', exist_ok=True)

# Initialize database when app is imported (for gunicorn)
try:
    init_db()
    print("✅ Database initialized successfully")
except Exception as e:
    print(f"⚠️ Database initialization warning: {e}")
    # Continue anyway - database might already exist

# Database setup
def init_db():
    conn = sqlite3.connect('store.db')
    c = conn.cursor()
    
    # Categories table
    c.execute('''CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        icon TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Tags table
    c.execute('''CREATE TABLE IF NOT EXISTS tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        color TEXT DEFAULT '#007bff',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Bundles table
    c.execute('''CREATE TABLE IF NOT EXISTS bundles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        discount_percentage REAL DEFAULT 0,
        discount_amount REAL DEFAULT 0,
        is_visible BOOLEAN DEFAULT TRUE,
        images TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Bundle products relationship table
    c.execute('''CREATE TABLE IF NOT EXISTS bundle_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bundle_id INTEGER,
        product_id INTEGER,
        FOREIGN KEY (bundle_id) REFERENCES bundles (id) ON DELETE CASCADE,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
        UNIQUE(bundle_id, product_id)
    )''')
    
    # Products table
    c.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price_dzd REAL NOT NULL,
        stock_count INTEGER DEFAULT 0,
        type TEXT CHECK(type IN ('key', 'file', 'bundle')) NOT NULL,
        file_or_key_path TEXT,
        images TEXT,
        category_id INTEGER,
        is_visible BOOLEAN DEFAULT TRUE,
        is_featured BOOLEAN DEFAULT FALSE,
        stock_limit INTEGER DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )''')
    
    # Product tags relationship table
    c.execute('''CREATE TABLE IF NOT EXISTS product_tags (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        tag_id INTEGER,
        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
        FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
        UNIQUE(product_id, tag_id)
    )''')
    
    # Add new columns to existing products table if they don't exist
    new_columns = [
        ('category_id', 'INTEGER'),
        ('is_visible', 'BOOLEAN DEFAULT TRUE'),
        ('is_featured', 'BOOLEAN DEFAULT FALSE'),
        ('stock_limit', 'INTEGER DEFAULT NULL'),
        ('images', 'TEXT')
    ]
    
    for column_name, column_def in new_columns:
        try:
            c.execute(f'ALTER TABLE products ADD COLUMN {column_name} {column_def}')
        except sqlite3.OperationalError:
            # Column already exists
            pass
    
    # Product keys table for individual key management
    c.execute('''CREATE TABLE IF NOT EXISTS product_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        key_value TEXT NOT NULL,
        is_used BOOLEAN DEFAULT FALSE,
        used_by_order_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        used_at TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (used_by_order_id) REFERENCES orders (id)
    )''')
    
    # Orders table
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER,
        user_id INTEGER,
        buyer_name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT,
        telegram_username TEXT,
        payment_method TEXT CHECK(payment_method IN ('baridimob', 'ccp')),
        payment_proof_path TEXT,
        transaction_id TEXT,
        status TEXT CHECK(status IN ('pending', 'confirmed', 'rejected')) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        confirmed_at TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    # Add phone column if it doesn't exist (for existing databases)
    try:
        c.execute('ALTER TABLE orders ADD COLUMN phone TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Add user_id column if it doesn't exist (for existing databases)
    try:
        c.execute('ALTER TABLE orders ADD COLUMN user_id INTEGER')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Add activation columns to users table if they don't exist (for existing databases)
    try:
        c.execute('ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT FALSE')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    try:
        c.execute('ALTER TABLE users ADD COLUMN activation_token TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Contact messages table
    c.execute('''CREATE TABLE IF NOT EXISTS contact_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        subject TEXT NOT NULL,
        message TEXT NOT NULL,
        attachment_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        status TEXT DEFAULT 'new' CHECK(status IN ('new', 'read', 'replied'))
    )''')
    
    # Add receipt_path column if it doesn't exist (for existing databases)
    try:
        c.execute('ALTER TABLE orders ADD COLUMN receipt_path TEXT')
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
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
    
    # Users table for customer accounts - REBUILT
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_active BOOLEAN DEFAULT FALSE,
        is_admin BOOLEAN DEFAULT FALSE,
        activation_token TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Add new columns to existing users table if they don't exist
    user_columns = [
        ('is_admin', 'BOOLEAN DEFAULT FALSE'),
    ]
    
    for column_name, column_def in user_columns:
        try:
            c.execute(f'ALTER TABLE users ADD COLUMN {column_name} {column_def}')
            print(f"✅ Added column {column_name} to users table")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"✅ Column {column_name} already exists")
            else:
                print(f"⚠️ Error adding column {column_name}: {e}")
                # Continue anyway
    
    # Admin table
    c.execute('''CREATE TABLE IF NOT EXISTS admin (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')
    
    # Download tokens table for secure file downloads
    c.execute('''CREATE TABLE IF NOT EXISTS download_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE NOT NULL,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        file_path TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        is_used BOOLEAN DEFAULT FALSE,
        used_at TIMESTAMP,
        download_count INTEGER DEFAULT 0,
        max_downloads INTEGER DEFAULT 3,
        FOREIGN KEY (order_id) REFERENCES orders (id),
        FOREIGN KEY (product_id) REFERENCES products (id)
    )''')
    
    # Create default admin if not exists
    c.execute('SELECT COUNT(*) FROM admin')
    if c.fetchone()[0] == 0:
        admin_hash = generate_password_hash('admin123')
        c.execute('INSERT INTO admin (username, password_hash) VALUES (?, ?)', ('admin', admin_hash))
    
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect('store.db')
    conn.row_factory = sqlite3.Row
    return conn

def log_action(order_id, action, actor, note=None):
    conn = get_db()
    conn.execute('INSERT INTO audit_log (order_id, action, actor, note) VALUES (?, ?, ?, ?)',
                 (order_id, action, actor, note))
    conn.commit()
    conn.close()

def generate_receipt_pdf(order_data):
    """Generate professional branded PDF receipt for confirmed order"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from datetime import datetime
        
        # Create filename
        receipt_filename = f"receipt_{order_data['id']}.pdf"
        receipt_path = os.path.join('receipts', receipt_filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(receipt_path, pagesize=letter, 
                              rightMargin=50, leftMargin=50, 
                              topMargin=50, bottomMargin=50)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor('#2c3e50'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Heading2'],
            fontSize=16,
            spaceAfter=20,
            textColor=colors.HexColor('#34495e'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        header_style = ParagraphStyle(
            'CustomHeader',
            parent=styles['Heading3'],
            fontSize=14,
            spaceAfter=10,
            textColor=colors.HexColor('#2c3e50'),
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            textColor=colors.HexColor('#2c3e50')
        )
        
        # Store information
        store_name = os.getenv('STORE_NAME', 'Espamoda')
        
        # Header with store branding
        elements.append(Paragraph(f"🖤 {store_name}", title_style))
        elements.append(Paragraph("RECEIPT", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # Order information section
        elements.append(Paragraph("Order Information", header_style))
        
        order_info_data = [
            ['Order ID:', f"#{order_data['id']}"],
            ['Date:', datetime.now().strftime('%B %d, %Y at %I:%M %p')],
            ['Status:', 'CONFIRMED ✅'],
        ]
        
        order_table = Table(order_info_data, colWidths=[2*inch, 4*inch])
        order_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(order_table)
        elements.append(Spacer(1, 20))
        
        # Customer information section
        elements.append(Paragraph("Customer Information", header_style))
        
        customer_data = [
            ['Name:', order_data['buyer_name']],
            ['Email:', order_data['email']],
            ['Phone:', order_data['phone'] or 'Not provided'],
            ['Telegram:', f"@{order_data['telegram_username']}" if order_data['telegram_username'] else 'Not provided'],
        ]
        
        customer_table = Table(customer_data, colWidths=[2*inch, 4*inch])
        customer_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(customer_table)
        elements.append(Spacer(1, 20))
        
        # Product and payment section
        elements.append(Paragraph("Order Summary", header_style))
        
        # Product details table
        product_data = [
            ['Product', 'Quantity', 'Price'],
            [order_data['product_name'], '1', f"{order_data['price_dzd']:,.0f} DZD"],
        ]
        
        product_table = Table(product_data, colWidths=[3*inch, 1*inch, 2*inch])
        product_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2c3e50')),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
            
            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(product_table)
        elements.append(Spacer(1, 15))
        
        # Total section
        total_data = [
            ['', 'Total Amount:', f"{order_data['price_dzd']:,.0f} DZD"],
        ]
        
        total_table = Table(total_data, colWidths=[3*inch, 1*inch, 2*inch])
        total_table.setStyle(TableStyle([
            ('FONTNAME', (1, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (1, 0), (-1, 0), 14),
            ('TEXTCOLOR', (1, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
            ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (1, 0), (-1, 0), 2, colors.HexColor('#27ae60')),
        ]))
        
        elements.append(total_table)
        elements.append(Spacer(1, 20))
        
        # Payment information
        elements.append(Paragraph("Payment Information", header_style))
        
        payment_data = [
            ['Payment Method:', order_data['payment_method'].upper()],
            ['Payment Status:', 'CONFIRMED ✅'],
            ['Confirmation Date:', order_data['confirmed_at'][:19] if order_data['confirmed_at'] else datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
        ]
        
        payment_table = Table(payment_data, colWidths=[2*inch, 4*inch])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2c3e50')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(payment_table)
        elements.append(Spacer(1, 30))
        
        # Thank you footer
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=14,
            textColor=colors.HexColor('#e74c3c'),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        elements.append(Paragraph("Thank you for shopping with Espamoda 🖤", footer_style))
        elements.append(Spacer(1, 10))
        
        # Additional footer info
        footer_info_style = ParagraphStyle(
            'FooterInfo',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#7f8c8d'),
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph("This is an official receipt for your purchase.", footer_info_style))
        elements.append(Paragraph("For support, please contact us with your order ID.", footer_info_style))
        
        # Build PDF
        doc.build(elements)
        
        print(f"✅ Professional PDF receipt generated: {receipt_path}")
        return receipt_path
        
    except Exception as e:
        print(f"❌ Professional PDF generation failed: {e}")
        import traceback
        traceback.print_exc()
        
        # Fallback to simple PDF
        try:
            receipt_filename = f"receipt_{order_data['id']}.pdf"
            receipt_path = os.path.join('receipts', receipt_filename)
            
            c = canvas.Canvas(receipt_path, pagesize=letter)
            width, height = letter
            
            store_name = os.getenv('STORE_NAME', 'Espamoda')
            
            c.setFont("Helvetica-Bold", 20)
            c.drawString(50, height - 50, f"🖤 {store_name}")
            
            c.setFont("Helvetica-Bold", 16)
            c.drawString(50, height - 80, "RECEIPT")
            
            c.setFont("Helvetica", 12)
            y_position = height - 120
            
            details = [
                f"Order ID: #{order_data['id']}",
                f"Customer: {order_data['buyer_name']}",
                f"Email: {order_data['email']}",
                f"Product: {order_data['product_name']}",
                f"Amount: {order_data['price_dzd']:,.0f} DZD",
                f"Payment: {order_data['payment_method'].upper()}",
                f"Status: CONFIRMED",
                "",
                "Thank you for shopping with Espamoda 🖤"
            ]
            
            for detail in details:
                c.drawString(50, y_position, detail)
                y_position -= 20
            
            c.save()
            print(f"✅ Fallback PDF receipt generated: {receipt_path}")
            return receipt_path
            
        except Exception as fallback_error:
            print(f"❌ Fallback PDF generation also failed: {fallback_error}")
            return None

def format_professional_email(customer_name, content, email_type="general"):
    """Format email content using the professional template you liked"""
    store_name = os.getenv('STORE_NAME', 'Espamoda')
    
    # Professional greeting
    greeting = f"Dear {customer_name}," if customer_name else "Dear Customer,"
    
    # Professional closing based on email type
    if email_type == "order_confirmation":
        closing = f"""Features:
- Faster delivery times
- Better inbox placement
- More reliable service
- Professional email formatting

Thank you for choosing {store_name}!

Best regards,
{store_name} Team"""
    elif email_type == "order_received":
        closing = f"""Features:
- Secure payment processing
- Fast order verification
- Professional customer service
- Reliable delivery system

We appreciate your business!

Best regards,
{store_name} Team"""
    elif email_type == "order_rejection":
        closing = f"""Our Commitment:
- Transparent communication
- Fair payment verification
- Professional customer service
- Quick issue resolution

We value your understanding and look forward to serving you better.

Best regards,
{store_name} Support Team"""
    elif email_type == "account_activation":
        closing = f"""Account Benefits:
- Track all your orders in one place
- Faster checkout with saved information
- Access download links anytime
- Professional customer support

Welcome to {store_name}!

Best regards,
{store_name} Team"""
    else:
        closing = f"""Features:
- Faster delivery times
- Better inbox placement
- More reliable service
- Professional email formatting

Best regards,
{store_name} Team"""
    
    # Combine all parts
    formatted_content = f"""{greeting}

{content}

{closing}"""
    
    return formatted_content

def send_activation_email(user_email, user_name, activation_link):
    """Send activation email using direct Resend API calls"""
    try:
        import requests
        
        resend_key = os.getenv('RESEND_API_KEY')
        if not resend_key:
            print("❌ RESEND_API_KEY not found in environment")
            return False
        
        print(f"📧 Sending activation email to: {user_email}")
        print(f"📧 Activation link: {activation_link}")
        print(f"📧 API Key: {resend_key[:10]}...{resend_key[-4:]}")
        
        # Email data
        data = {
            "from": "Espamoda <info@espamoda.store>",
            "to": [user_email],
            "subject": "Activate your DZKeyz Account",
            "html": f"""
            <div style='font-family:Arial,sans-serif;padding:20px;background:#fff;border-radius:8px;border:1px solid #eee;max-width:600px;margin:auto'>
                <h2 style='color:#111;margin-bottom:20px'>Welcome to DZKeyz 🔑</h2>
                <p style='font-size:16px;color:#333;margin-bottom:20px'>Hi {user_name},</p>
                <p style='font-size:16px;color:#333;margin-bottom:20px'>Click the button below to activate your account and start shopping securely:</p>
                <div style='text-align:center;margin:30px 0'>
                    <a href="{activation_link}" style='background:#111;color:#fff;padding:12px 24px;border-radius:6px;text-decoration:none;font-weight:bold;display:inline-block'>Activate Account</a>
                </div>
                <p style='font-size:14px;color:#666;margin-top:30px'>If you didn't create this account, you can safely ignore this email.</p>
                <hr style='border:none;border-top:1px solid #eee;margin:20px 0'>
                <p style='font-size:12px;color:#999;text-align:center'>DZKeyz - Your trusted digital game store</p>
            </div>
            """,
            "text": f"Welcome to DZKeyz! Please visit this link to activate your account: {activation_link}"
        }
        
        # Send via Resend API
        headers = {
            "Authorization": f"Bearer {resend_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post("https://api.resend.com/emails", json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Email sent successfully! ID: {result.get('id', 'Unknown')}")
            return True
        else:
            print(f"❌ Email sending failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_email(to, subject, body, customer_name=None, email_type="general", attachment_path=None):
    """Send email using Resend.com official Python SDK with professional formatting"""
    try:
        # Load environment variables manually (more reliable)
        env_vars = {}
        try:
            with open('.env', 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_vars[key.strip()] = value.strip()
        except Exception as e:
            print(f"❌ Error loading .env: {e}")
            return False
        
        # Get Resend configuration
        api_key = env_vars.get('RESEND_API_KEY') or os.getenv('RESEND_API_KEY')
        from_email = env_vars.get('MAIL_FROM') or os.getenv('MAIL_FROM', 'info@espamoda.store')
        from_name = env_vars.get('MAIL_NAME') or os.getenv('MAIL_NAME', 'Espamoda')
        
        print(f"📧 Sending email via Resend.com SDK to: {to}")
        print(f"📧 From: {from_name} <{from_email}>")
        print(f"📧 Subject: {subject}")
        print(f"📧 API Key: {api_key[:10] + '...' + api_key[-4:] if api_key else 'MISSING'}")
        
        if not api_key:
            print("❌ Email sending failed: Missing RESEND_API_KEY in .env")
            return False
        
        if not from_email:
            print("❌ Email sending failed: Missing MAIL_FROM in .env")
            return False
        
        # Set Resend API key
        resend.api_key = api_key
        
        # Format the email content professionally
        formatted_body = format_professional_email(customer_name, body, email_type)
        
        # Convert to HTML for better formatting
        # Convert newlines for HTML (can't use backslashes in f-strings)
        html_formatted_body = formatted_body.replace('\n\n', '</p><p style="margin: 15px 0;">').replace('\n', '<br>')
        
        html_body = f"""
        <div style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="border-bottom: 3px solid #667eea; padding-bottom: 20px; margin-bottom: 20px;">
                <h2 style="color: #333; margin: 0;">{from_name}</h2>
            </div>
            <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                {html_formatted_body}
            </div>
            <div style="text-align: center; padding: 20px; color: #666; font-size: 14px; border-top: 1px solid #eee; margin-top: 30px;">
                <p>This email was sent from <strong>{from_name}</strong></p>
                <p>Powered by Resend.com for better email delivery!</p>
            </div>
        </div>
        """
        
        # Email parameters using official Resend format
        params: resend.Emails.SendParams = {
            "from": f"{from_name} <{from_email}>",
            "to": [to],
            "subject": subject,
            "html": html_body,
            "text": formatted_body
        }
        
        # Add attachment if provided
        if attachment_path and os.path.exists(attachment_path):
            try:
                with open(attachment_path, 'rb') as f:
                    attachment_content = f.read()
                
                attachment_filename = os.path.basename(attachment_path)
                
                params["attachments"] = [{
                    "filename": attachment_filename,
                    "content": attachment_content
                }]
                
                print(f"📎 Adding attachment: {attachment_filename} ({len(attachment_content)} bytes)")
                
            except Exception as attachment_error:
                print(f"⚠️ Failed to attach file {attachment_path}: {attachment_error}")
                # Continue without attachment
        elif attachment_path:
            print(f"⚠️ Attachment file not found: {attachment_path}")
        
        print("📧 Sending email via Resend.com SDK...")
        
        # Send the email using official SDK format
        email_response = resend.Emails.send(params)
        
        email_id = email_response.get('id', 'Unknown')
        
        print(f"✅ Email sent successfully to {to}")
        print(f"📧 Email ID: {email_id}")
        print("📧 Resend.com SDK - excellent deliverability!")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def send_bot_message(chat_id, message):
    """Send a message from the bot to a specific chat"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token:
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        response = requests.post(url, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Failed to send bot message: {e}")
        return False

def send_telegram_notification(message, order_id=None, payment_proof_path=None):
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    admin_id = os.getenv('TELEGRAM_ADMIN_ID')
    
    if not bot_token or not admin_id:
        return False
    
    # Create inline keyboard if order_id is provided
    keyboard = None
    if order_id:
        keyboard = {
            "inline_keyboard": [[
                {"text": "✅ Confirm", "callback_data": f"confirm_{order_id}"},
                {"text": "❌ Reject", "callback_data": f"reject_{order_id}"}
            ]]
        }
    
    # Try to send with payment proof image first
    if payment_proof_path and os.path.exists(payment_proof_path):
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
            
            with open(payment_proof_path, 'rb') as photo:
                files = {'photo': photo}
                data = {
                    'chat_id': admin_id,
                    'caption': message
                }
                
                if keyboard:
                    data['reply_markup'] = json.dumps(keyboard)
                
                response = requests.post(url, files=files, data=data)
                
                if response.status_code == 200:
                    return True
                else:
                    print(f"Failed to send photo: {response.status_code} - {response.text}")
        
        except Exception as e:
            print(f"Failed to send payment proof image: {e}")
    
    # Fallback to text message
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        data = {
            "chat_id": admin_id,
            "text": message
        }
        
        if keyboard:
            data["reply_markup"] = keyboard
        
        response = requests.post(url, json=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram notification failed: {e}")
        return False

# Authentication decorators
def admin_required(f):
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/health')
def health_check():
    """Simple health check endpoint for debugging"""
    try:
        # Test database connection
        conn = get_db()
        conn.execute('SELECT 1').fetchone()
        conn.close()
        db_status = "OK"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
    
    return {
        "status": "OK",
        "database": db_status,
        "environment": {
            "PORT": os.environ.get('PORT', 'Not set'),
            "SECRET_KEY": "Set" if os.environ.get('SECRET_KEY') else "Not set",
            "STORE_NAME": os.environ.get('STORE_NAME', 'Not set')
        }
    }

@app.route('/')
def index():
    try:
        conn = get_db()
        
        # Get visible products only
        products_raw = conn.execute('''
            SELECT p.*, c.name as category_name, c.icon as category_icon
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_visible = TRUE AND (p.stock_count > 0 OR p.type != 'key')
            ORDER BY p.is_featured DESC, p.created_at DESC
        ''').fetchall()
    except Exception as e:
        # If database fails, show a simple page
        return f"<h1>DZ Keyz Store</h1><p>Setting up... Database error: {str(e)}</p><p><a href='/health'>Health Check</a></p>"
    
    products = []
    for product in products_raw:
        product_dict = dict(product)
        product_dict['image_urls'] = get_product_images(product['images'])
        product_dict['main_image'] = product_dict['image_urls'][0] if product_dict['image_urls'] else None
        product_dict['tags'] = get_product_tags(product['id'])
        
        # Check stock status for key products
        if product['type'] == 'key' and product.get('stock_limit'):
            available_keys = conn.execute(
                'SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                (product['id'],)
            ).fetchone()[0]
            product_dict['available_stock'] = available_keys
            product_dict['is_in_stock'] = available_keys > 0
        else:
            product_dict['available_stock'] = None
            product_dict['is_in_stock'] = True
            
        products.append(product_dict)
    
    # Get visible bundles
    bundles = []
    bundles_raw = conn.execute('SELECT * FROM bundles WHERE is_visible = TRUE ORDER BY created_at DESC').fetchall()
    for bundle in bundles_raw:
        bundle_dict = dict(bundle)
        bundle_dict['image_urls'] = get_product_images(bundle['images'])
        bundle_dict['main_image'] = bundle_dict['image_urls'][0] if bundle_dict['image_urls'] else None
        bundle_dict['original_price'] = conn.execute('''
            SELECT SUM(p.price_dzd) FROM products p
            JOIN bundle_products bp ON p.id = bp.product_id
            WHERE bp.bundle_id = ?
        ''', (bundle['id'],)).fetchone()[0] or 0
        bundle_dict['final_price'] = calculate_bundle_price(bundle['id'])
        bundle_dict['savings'] = bundle_dict['original_price'] - bundle_dict['final_price']
        bundles.append(bundle_dict)
    
    # Get categories for filtering
    categories = get_categories()
    
    conn.close()
    return render_template('index.html', products=products, bundles=bundles, categories=categories)

@app.route('/product/<int:product_id>')
def product_details(product_id):
    conn = get_db()
    product_raw = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if not product_raw:
        flash('Product not found', 'error')
        return redirect(url_for('index'))
    
    # Convert to dict and add image data
    product = dict(product_raw)
    product['image_urls'] = get_product_images(product['images'])
    product['main_image'] = product['image_urls'][0] if product['image_urls'] else None
    
    # Get related products (same type, excluding current product)
    related_products_raw = conn.execute('''SELECT * FROM products 
                                          WHERE type = ? AND id != ? AND stock_count > 0 
                                          ORDER BY created_at DESC LIMIT 3''', 
                                       (product['type'], product_id)).fetchall()
    
    related_products = []
    for related in related_products_raw:
        related_dict = dict(related)
        related_dict['image_urls'] = get_product_images(related['images'])
        related_dict['main_image'] = related_dict['image_urls'][0] if related_dict['image_urls'] else None
        related_products.append(related_dict)
    
    conn.close()
    
    return render_template('product_details.html', product=product, related_products=related_products)

@app.route('/buy/<int:product_id>')
def buy_product(product_id):
    conn = get_db()
    product_raw = conn.execute('SELECT * FROM products WHERE id = ? AND stock_count > 0', (product_id,)).fetchone()
    conn.close()
    
    if not product_raw:
        flash('Product not found or out of stock', 'error')
        return redirect(url_for('index'))
    
    # Convert to dict and add image data
    product = dict(product_raw)
    product['image_urls'] = get_product_images(product['images'])
    product['main_image'] = product['image_urls'][0] if product['image_urls'] else None
    
    # Get payment configuration from environment variables
    payment_config = {
        'baridimob_number': os.getenv('BARIDIMOB_NUMBER', '0123456789'),
        'ccp_account': os.getenv('CCP_ACCOUNT', '1234567890'),
        'ccp_key': os.getenv('CCP_KEY', '12')
    }
    
    return render_template('buy.html', product=product, payment_config=payment_config)

@app.route('/submit_order', methods=['POST'])
def submit_order():
    product_id = request.form.get('product_id')
    buyer_name = request.form.get('buyer_name')
    email = request.form.get('email')
    phone = request.form.get('phone')
    telegram_username = request.form.get('telegram_username')
    payment_method = request.form.get('payment_method')
    transaction_id = request.form.get('transaction_id')
    
    # Validate payment proof is required
    if 'payment_proof' not in request.files or not request.files['payment_proof'].filename:
        flash('Payment proof is required to process your order.', 'error')
        return redirect(url_for('buy_product', product_id=product_id))
    
    # Handle file upload
    payment_proof_path = None
    file = request.files['payment_proof']
    if file and file.filename:
        filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        # Store just the filename, not the full path
        payment_proof_path = filename
    
    # Get user_id if logged in
    user_id = session.get('user_id')
    
    # Insert order
    conn = get_db()
    cursor = conn.execute('''INSERT INTO orders 
                            (product_id, user_id, buyer_name, email, phone, telegram_username, payment_method, 
                             payment_proof_path, transaction_id) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                         (product_id, user_id, buyer_name, email, phone, telegram_username, payment_method,
                          payment_proof_path, transaction_id))
    order_id = cursor.lastrowid
    
    # Get product info for notification
    product = conn.execute('SELECT name, price_dzd FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.commit()
    conn.close()
    
    # Log action
    log_action(order_id, 'order_created', f'buyer_{buyer_name}')
    
    # Send Telegram notification
    message = f"""🛒 New Order #{order_id}
    
Product: {product['name']}
Price: {product['price_dzd']} DZD
Buyer: {buyer_name}
Email: {email}
Phone: {phone}
Telegram: @{telegram_username or 'Not provided'}
Payment: {payment_method.upper()}
Transaction ID: {transaction_id or 'Not provided'}
"""
    
    send_telegram_notification(message, order_id, payment_proof_path)
    
    # Send order confirmation email to buyer
    if email:
        store_name = os.getenv('STORE_NAME', 'Digital Store')
        email_subject = f"Order Received - {store_name}"
        email_body = f"""Thank you for your order! We have received your payment and are processing your request.

Order Details:
- Order ID: #{order_id}
- Product: {product['name']}
- Price: {product['price_dzd']} DZD
- Payment Method: {payment_method.upper()}

Your order is currently being reviewed by our team. You will receive another email once your order is confirmed and your product is ready.

If you have any questions, please contact our support team."""
        
        send_email(email, email_subject, email_body, buyer_name, "order_received")
    
    flash('Payment received. Waiting for admin confirmation.', 'success')
    print(f"✅ Order {order_id} created successfully, redirecting to confirmation page")
    return redirect(url_for('order_confirmation', order_id=order_id))

@app.route('/contact', methods=['POST'])
def contact_form():
    """Handle contact form submissions"""
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()
        
        # Handle file upload if present
        uploaded_file = request.files.get('attachment')
        file_info = None
        
        if uploaded_file and uploaded_file.filename:
            # Save the uploaded file
            filename = secure_filename(uploaded_file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_filename = f"contact_{timestamp}_{filename}"
            file_path = os.path.join('uploads', safe_filename)
            uploaded_file.save(file_path)
            file_info = {
                'filename': filename,
                'path': file_path,
                'size': os.path.getsize(file_path)
            }
        
        # Store contact message in database
        conn = get_db()
        conn.execute('''
            INSERT INTO contact_messages (name, email, subject, message, attachment_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (name, email, subject, message, file_info['path'] if file_info else None, datetime.now()))
        conn.commit()
        conn.close()
        
        # Send notification (if configured)
        try:
            if os.getenv('CONTACT_EMAIL'):
                # Here you could add email notification logic
                pass
        except Exception as e:
            print(f"Failed to send contact notification: {e}")
        
        return jsonify({
            'success': True,
            'message': '✅ Your message has been sent successfully! We\'ll get back to you soon.'
        })
        
    except Exception as e:
        print(f"Contact form error: {e}")
        return jsonify({
            'success': False,
            'message': '❌ Sorry, there was an error sending your message. Please try again.'
        }), 500

@app.route('/search_products')
def search_products():
    """AJAX endpoint for smart fuzzy product search"""
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify([])
    
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        # Fallback to basic search if rapidfuzz not available
        conn = get_db()
        products = conn.execute('''
            SELECT id, name, description, price_dzd, images, type, stock_count
            FROM products 
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY name
            LIMIT 10
        ''', (f'%{query}%', f'%{query}%')).fetchall()
        conn.close()
        
        result_products = []
        for p in products:
            # Process images the same way as in other routes
            image_urls = get_product_images(p['images'])
            main_image = image_urls[0] if image_urls else None
            
            result_products.append({
                'id': p['id'],
                'name': p['name'],
                'description': p['description'] or '',
                'price_dzd': p['price_dzd'],
                'image': main_image or '',
                'type': p['type'],
                'stock_count': p['stock_count'] or 0
            })
        
        return jsonify(result_products)
    
    conn = get_db()
    products = conn.execute('''
        SELECT id, name, description, price_dzd, images, type, stock_count
        FROM products
    ''').fetchall()
    conn.close()
    
    if not products:
        return jsonify([])
    
    # Build product list for fuzzy matching
    product_list = []
    search_strings = []
    
    for p in products:
        # Process images the same way as in other routes
        image_urls = get_product_images(p['images'])
        main_image = image_urls[0] if image_urls else None
        
        product_data = {
            'id': p['id'],
            'name': p['name'],
            'description': p['description'] or '',
            'price_dzd': p['price_dzd'],
            'image': main_image or '',
            'type': p['type'],
            'stock_count': p['stock_count'] or 0
        }
        product_list.append(product_data)
        
        # Combine name and description for searching
        search_text = f"{p['name']} {p['description'] or ''}".strip()
        search_strings.append((p['id'], search_text))
    
    # Use RapidFuzz to find best matches
    try:
        results = process.extract(
            query,
            search_strings,
            scorer=fuzz.partial_ratio,
            limit=10
        )
        
        # Filter results with score > 50 and get corresponding products
        matched_products = []
        for (product_id, _), score in results:
            if score > 50:
                product = next((p for p in product_list if p['id'] == product_id), None)
                if product:
                    product['match_score'] = score
                    matched_products.append(product)
        
        # Sort by match score (highest first)
        matched_products.sort(key=lambda x: x['match_score'], reverse=True)
        
        return jsonify(matched_products)
        
    except Exception as e:
        print(f"Fuzzy search error: {e}")
        # Fallback to basic search
        basic_matches = [p for p in product_list 
                        if query.lower() in p['name'].lower() or 
                           query.lower() in p['description'].lower()]
        return jsonify(basic_matches[:10])

@app.route('/order-confirmation/<int:order_id>')
def order_confirmation(order_id):
    print(f"📄 Loading order confirmation page for order #{order_id}")
    conn = get_db()
    
    # Get order details with product info
    order = conn.execute('''SELECT o.*, p.name as product_name, p.price_dzd, p.type as product_type
                           FROM orders o 
                           JOIN products p ON o.product_id = p.id 
                           WHERE o.id = ?''', (order_id,)).fetchone()
    
    conn.close()
    
    if not order:
        print(f"❌ Order #{order_id} not found")
        flash('Order not found', 'error')
        return redirect(url_for('index'))
    
    # Convert to dict for template
    order_dict = dict(order)
    print(f"✅ Order #{order_id} found: {order_dict['product_name']} for {order_dict['buyer_name']}")
    
    return render_template('thankyou.html', order=order_dict)

# Initialize database
init_db()

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        admin = conn.execute('SELECT * FROM admin WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if admin and check_password_hash(admin['password_hash'], password):
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

# User Authentication Routes
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not name or not email or not password:
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        try:
            # Check if email already exists
            conn = get_db()
            existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            
            if existing_user:
                flash('An account with this email already exists.', 'error')
                conn.close()
                return render_template('register.html')
            
            # Generate secure activation token
            import secrets
            activation_token = secrets.token_urlsafe(32)
            
            # Create new user (inactive by default)
            password_hash = generate_password_hash(password)
            
            print(f"🔧 Creating user: {name} ({email})")
            conn.execute('''INSERT INTO users (name, email, password_hash, is_active, is_admin, activation_token) 
                           VALUES (?, ?, ?, ?, ?, ?)''',
                        (name, email, password_hash, False, False, activation_token))
            conn.commit()
            conn.close()
            
            print(f"✅ User created successfully in database")
            
            # Send activation email
            base_url = app.config.get('BASE_URL', 'https://dzkeyz.onrender.com')
            activation_link = f"{base_url}/activate/{activation_token}"
            
            email_sent = send_activation_email(email, name, activation_link)
            
            if email_sent:
                flash('🎉 Account created successfully! Please check your email to activate your account.', 'success')
            else:
                flash('Account created! However, we had trouble sending the activation email. You can request a new one from the login page.', 'warning')
            
            return redirect(url_for('login'))
            
        except Exception as e:
            print(f"❌ Registration error: {e}")
            import traceback
            traceback.print_exc()
            flash('An error occurred while creating your account. Please try again.', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            
            if not email or not password:
                flash('Email and password are required.', 'error')
                return render_template('login.html')
            
            conn = get_db()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            conn.close()
            
            if user and check_password_hash(user['password_hash'], password):
                print(f"🔧 DEBUG: Password verified for user: {user['name']}")
                
                # Check if account is activated
                try:
                    is_active = user.get('is_active', True)  # Default to True for backward compatibility
                    print(f"🔧 DEBUG: User is_active status: {is_active}")
                    
                    if not is_active:
                        flash('⚠️ Please activate your account first. Check your email for the activation link.', 'warning')
                        return render_template('login.html')
                except Exception as activation_error:
                    print(f"🔧 DEBUG: Error checking activation: {activation_error}")
                    # Continue with login if activation check fails
                
                # Set session with safe column access
                try:
                    session['user_id'] = user['id']
                    session['user_name'] = user['name']
                    session['user_email'] = user['email']
                    
                    # Safely check for is_admin column
                    try:
                        session['is_admin'] = user.get('is_admin', False)
                    except (KeyError, TypeError):
                        session['is_admin'] = False  # Default to False if column doesn't exist
                    
                    print(f"✅ Session set for user: {user['name']} (Admin: {session.get('is_admin', False)})")
                    
                    # Redirect to intended page or home
                    next_page = request.args.get('next')
                    if next_page:
                        return redirect(next_page)
                    
                    flash(f'Welcome back, {user["name"]}!', 'success')
                    return redirect(url_for('index'))
                    
                except Exception as session_error:
                    print(f"🔧 DEBUG: Session error: {session_error}")
                    raise session_error
            else:
                flash('Invalid email or password. Please check your credentials and try again.', 'error')
        
        except Exception as e:
            print(f"❌ Login error: {e}")
            import traceback
            traceback.print_exc()
            flash('An unexpected error occurred. Please try again.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('user_email', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/my-orders')
@login_required
def my_orders():
    user_id = session.get('user_id')
    
    conn = get_db()
    orders = conn.execute('''
        SELECT o.*, p.name as product_name, p.type as product_type, p.price_dzd
        FROM orders o 
        JOIN products p ON o.product_id = p.id 
        WHERE o.user_id = ? 
        ORDER BY o.created_at DESC
    ''', (user_id,)).fetchall()
    
    # Convert to list of dicts and add download tokens for file products
    orders_list = []
    for order in orders:
        order_dict = dict(order)
        
        # Add download token for confirmed file products
        if order['status'] == 'confirmed' and order['product_type'] == 'file':
            token = conn.execute('''
                SELECT token FROM download_tokens 
                WHERE order_id = ? AND download_count < max_downloads 
                AND datetime(expires_at) > datetime('now')
                ORDER BY created_at DESC LIMIT 1
            ''', (order['id'],)).fetchone()
            
            if token:
                order_dict['download_token'] = token['token']
                order_dict['download_url'] = f"{app.config['BASE_URL']}/download/{token['token']}"
        
        # Get product key for confirmed key products
        if order['status'] == 'confirmed' and order['product_type'] == 'key':
            key = conn.execute('''
                SELECT key_value FROM product_keys 
                WHERE used_by_order_id = ?
            ''', (order['id'],)).fetchone()
            
            if key:
                order_dict['product_key'] = key['key_value']
        
        orders_list.append(order_dict)
    
    conn.close()
    
    return render_template('my_orders.html', orders=orders_list)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Email address is required.', 'error')
            return render_template('forgot_password.html')
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user:
            # Generate a simple reset token (in production, use more secure method)
            import secrets
            reset_token = secrets.token_urlsafe(32)
            
            # Store reset token in session (simple approach)
            session['reset_token'] = reset_token
            session['reset_email'] = email
            session['reset_expires'] = (datetime.now() + timedelta(hours=1)).isoformat()
            
            # Send reset email if email is configured
            if os.getenv('RESEND_API_KEY'):
                reset_url = f"{app.config['BASE_URL']}/reset-password?token={reset_token}"
                subject = f"Password Reset - {app.config['STORE_NAME']}"
                body = f"""You requested a password reset for your account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour.

If you didn't request this reset, please ignore this email.

Best regards,
{app.config['STORE_NAME']} Team"""
                
                send_email(email, subject, body, user['name'], "password_reset")
                flash('Password reset instructions have been sent to your email.', 'success')
            else:
                # Fallback if email not configured
                flash(f'Password reset link: /reset-password?token={reset_token}', 'info')
        else:
            # Don't reveal if email exists or not (security)
            flash('If an account with that email exists, password reset instructions have been sent.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    token = request.args.get('token') or request.form.get('token')
    
    if not token or session.get('reset_token') != token:
        flash('Invalid or expired reset link.', 'error')
        return redirect(url_for('login'))
    
    # Check if token is expired
    if session.get('reset_expires'):
        try:
            expires = datetime.fromisoformat(session['reset_expires'])
            if datetime.now() > expires:
                flash('Reset link has expired. Please request a new one.', 'error')
                return redirect(url_for('forgot_password'))
        except:
            flash('Invalid reset link.', 'error')
            return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not password or len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('reset_password.html', token=token)
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        # Update password
        email = session.get('reset_email')
        if email:
            password_hash = generate_password_hash(password)
            conn = get_db()
            conn.execute('UPDATE users SET password_hash = ? WHERE email = ?', (password_hash, email))
            conn.commit()
            conn.close()
            
            # Clear reset session data
            session.pop('reset_token', None)
            session.pop('reset_email', None)
            session.pop('reset_expires', None)
            
            flash('Password has been reset successfully! Please log in with your new password.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Invalid reset session.', 'error')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/activate/<token>')
def activate_account(token):
    """Activate user account with token"""
    try:
        if not token:
            flash('Invalid activation link.', 'error')
            return redirect(url_for('activate_error'))
        
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE activation_token = ?', (token,)).fetchone()
        
        if not user:
            conn.close()
            flash('Invalid or expired activation link.', 'error')
            return redirect(url_for('activate_error'))
        
        if user['is_active']:
            conn.close()
            flash('Your account is already activated! You can log in now.', 'info')
            return redirect(url_for('activate_success'))
        
        # Activate the account
        conn.execute('UPDATE users SET is_active = ?, activation_token = NULL WHERE id = ?', 
                    (True, user['id']))
        conn.commit()
        conn.close()
        
        print(f"✅ Account activated for user: {user['name']} ({user['email']})")
        flash('🎉 Account activated successfully! You can now log in.', 'success')
        return redirect(url_for('activate_success'))
        
    except Exception as e:
        print(f"❌ Activation error: {e}")
        import traceback
        traceback.print_exc()
        flash('An error occurred during activation. Please try again.', 'error')
        return redirect(url_for('activate_error'))

@app.route('/activate-success')
def activate_success():
    """Account activation success page"""
    return render_template('activate_success.html')

@app.route('/activate-error')
def activate_error():
    """Account activation error page"""
    return render_template('activate_error.html')

@app.route('/resend-activation', methods=['GET', 'POST'])
def resend_activation():
    """Resend activation email for unactivated accounts"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash('Email address is required.', 'error')
            return render_template('resend_activation.html')
        
        try:
            conn = get_db()
            user = conn.execute('SELECT * FROM users WHERE email = ? AND is_active = FALSE', (email,)).fetchone()
            
            if user:
                # Generate new secure activation token
                import secrets
                new_token = secrets.token_urlsafe(32)
                conn.execute('UPDATE users SET activation_token = ? WHERE id = ?', (new_token, user['id']))
                conn.commit()
                
                # Send new activation email
                base_url = app.config.get('BASE_URL', 'https://dzkeyz.onrender.com')
                activation_link = f"{base_url}/activate/{new_token}"
                
                email_sent = send_activation_email(email, user['name'], activation_link)
                
                if email_sent:
                    flash('✅ Activation email sent! Please check your inbox and spam folder.', 'success')
                else:
                    flash('We had trouble sending the email. Please try again in a few minutes.', 'warning')
            else:
                # Don't reveal if email exists or not (security)
                flash('If an unactivated account with that email exists, we\'ve sent a new activation email.', 'info')
            
            conn.close()
            
        except Exception as e:
            print(f"❌ Resend activation error: {e}")
            flash('An error occurred. Please try again.', 'error')
        
        return redirect(url_for('login'))
    
    return render_template('resend_activation.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db()
    
    # Get orders with product info and user info
    orders_raw = conn.execute('''SELECT o.*, p.name as product_name, p.price_dzd,
                                        u.name as user_name, u.email as user_email
                                FROM orders o 
                                JOIN products p ON o.product_id = p.id 
                                LEFT JOIN users u ON o.user_id = u.id
                                ORDER BY o.created_at DESC''').fetchall()
    
    # Convert to list of dicts and handle datetime conversion
    orders = []
    for order in orders_raw:
        order_dict = dict(order)
        # Convert created_at string to datetime if needed
        if order_dict.get('created_at') and isinstance(order_dict['created_at'], str):
            try:
                # Handle different datetime string formats
                created_at_str = order_dict['created_at']
                if 'T' in created_at_str:
                    # ISO format: 2024-01-01T12:00:00
                    order_dict['created_at'] = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                else:
                    # SQLite format: 2024-01-01 12:00:00
                    order_dict['created_at'] = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                # If conversion fails, keep as string but make it display-friendly
                order_dict['created_at_display'] = order_dict['created_at'][:16] if order_dict['created_at'] else 'N/A'
        orders.append(order_dict)
    
    # Get summary stats
    total_orders = conn.execute('SELECT COUNT(*) FROM orders WHERE status = "confirmed"').fetchone()[0]
    total_revenue = conn.execute('SELECT SUM(p.price_dzd) FROM orders o JOIN products p ON o.product_id = p.id WHERE o.status = "confirmed"').fetchone()[0] or 0
    pending_orders = conn.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"').fetchone()[0]
    
    # Get products for the sidebar
    products = conn.execute('SELECT * FROM products ORDER BY created_at DESC').fetchall()
    total_products = len(products)
    
    # Get users for the sidebar
    users = conn.execute('SELECT id, name, email, is_active, created_at FROM users ORDER BY created_at DESC').fetchall()
    
    # Get recent orders (limit to 10)
    recent_orders = orders[:10] if orders else []
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         orders=orders,
                         recent_orders=recent_orders,
                         products=products,
                         users=users,
                         total_orders=total_orders,
                         total_products=total_products,
                         total_revenue=total_revenue,
                         pending_orders=pending_orders)

@app.route('/debug/test-resend')
def debug_test_resend():
    """Simple test of Resend API"""
    try:
        import resend
        
        # Get API key
        api_key = os.getenv('RESEND_API_KEY')
        if not api_key:
            return "<h2>❌ No RESEND_API_KEY found</h2>"
        
        resend.api_key = api_key
        
        # Simple test email
        params = {
            "from": "Hami Store <info@espamoda.store>",
            "to": ["yassinasagat@gmail.com"],
            "subject": "Test Email from DZKeyz",
            "html": "<h1>Test Email</h1><p>This is a test email from DZKeyz to verify Resend integration.</p>",
            "text": "Test Email - This is a test email from DZKeyz to verify Resend integration."
        }
        
        print(f"📧 Testing Resend with API key: {api_key[:10]}...")
        
        response = resend.Emails.send(params)
        
        return f"<h2>✅ Email sent successfully!</h2><p>Response: {response}</p>"
        
    except Exception as e:
        import traceback
        return f"<h2>❌ Error: {e}</h2><pre>{traceback.format_exc()}</pre>"

@app.route('/debug/email')
def debug_email():
    """Debug route to test email sending"""
    try:
        # Test basic email sending
        test_email = "yassinasagat@gmail.com"  # Use the same email from the user
        
        result = "<h2>🧪 Email Debug Test</h2>"
        
        # Check environment variables
        result += "<h3>📧 Email Configuration:</h3>"
        result += f"<p>RESEND_API_KEY: {'✅ Set' if os.getenv('RESEND_API_KEY') else '❌ Missing'}</p>"
        result += f"<p>MAIL_FROM: {os.getenv('MAIL_FROM', 'Not set')}</p>"
        result += f"<p>MAIL_NAME: {os.getenv('MAIL_NAME', 'Not set')}</p>"
        
        # Test simple email
        result += "<h3>📤 Testing Simple Email:</h3>"
        simple_success = send_html_email(
            test_email, 
            "Test Email from DZKeyz", 
            "<h2>Test Email</h2><p>This is a test email to verify email functionality.</p>",
            "Test Email - This is a test email to verify email functionality."
        )
        result += f"<p>Simple Email Result: {'✅ Success' if simple_success else '❌ Failed'}</p>"
        
        # Test activation email format
        result += "<h3>🔑 Testing Activation Email:</h3>"
        activation_link = "https://dzkeyz.onrender.com/activate/test-token-123"
        activation_html = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;background:#fff;border-radius:10px;border:1px solid #eee;">
   <h2 style="color:#111;">Welcome to DZKeyz 🔑</h2>
   <p style="font-size:16px;color:#333;">Click below to activate your account and start shopping securely:</p>
   <a href="{activation_link}" style="display:inline-block;margin-top:10px;padding:10px 20px;background-color:#111;color:#fff;text-decoration:none;border-radius:6px;">Activate Account</a>
   <p style="font-size:14px;color:#666;margin-top:20px;">If you didn't create this account, you can safely ignore this email.</p>
</div>"""
        
        activation_success = send_html_email(
            test_email,
            "Activate your DZKeyz Account - TEST",
            activation_html,
            f"Welcome to DZKeyz! Please visit this link to activate your account: {activation_link}"
        )
        result += f"<p>Activation Email Result: {'✅ Success' if activation_success else '❌ Failed'}</p>"
        
        return result
        
    except Exception as e:
        import traceback
        return f"<h2>❌ Error: {e}</h2><pre>{traceback.format_exc()}</pre>"

@app.route('/debug/activate-user/<int:user_id>')
def debug_activate_user(user_id):
    """Debug route to manually activate a user and send email"""
    try:
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user:
            return f"<h2>❌ User with ID {user_id} not found</h2>"
        
        result = f"<h2>🔧 Manual User Activation</h2>"
        result += f"<p><strong>User:</strong> {user['name']} ({user['email']})</p>"
        result += f"<p><strong>Current Status:</strong> {'Active' if user['is_active'] else 'Inactive'}</p>"
        
        if not user['is_active']:
            # Generate new activation token
            new_token = str(uuid.uuid4())
            conn.execute('UPDATE users SET activation_token = ? WHERE id = ?', (new_token, user_id))
            conn.commit()
            
            # Send activation email
            base_url = app.config.get('BASE_URL', 'https://dzkeyz.onrender.com')
            activation_link = f"{base_url}/activate/{new_token}"
            
            email_subject = "Activate your DZKeyz Account"
            email_body = f"""<div style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px;background:#fff;border-radius:10px;border:1px solid #eee;">
   <h2 style="color:#111;">Welcome to DZKeyz 🔑</h2>
   <p style="font-size:16px;color:#333;">Click below to activate your account and start shopping securely:</p>
   <a href="{activation_link}" style="display:inline-block;margin-top:10px;padding:10px 20px;background-color:#111;color:#fff;text-decoration:none;border-radius:6px;">Activate Account</a>
   <p style="font-size:14px;color:#666;margin-top:20px;">If you didn't create this account, you can safely ignore this email.</p>
</div>"""
            
            text_body = f"Welcome to DZKeyz! Please visit this link to activate your account: {activation_link}"
            
            result += f"<p><strong>New Token:</strong> {new_token}</p>"
            result += f"<p><strong>Activation Link:</strong> <a href='{activation_link}'>{activation_link}</a></p>"
            
            email_sent = send_html_email(user['email'], email_subject, email_body, text_body)
            result += f"<p><strong>Email Sent:</strong> {'✅ Success' if email_sent else '❌ Failed'}</p>"
            
            if email_sent:
                result += f"<p>✅ Activation email sent to {user['email']}</p>"
            else:
                result += f"<p>❌ Failed to send activation email to {user['email']}</p>"
        else:
            result += "<p>✅ User is already active</p>"
        
        conn.close()
        return result
        
    except Exception as e:
        import traceback
        return f"<h2>❌ Error: {e}</h2><pre>{traceback.format_exc()}</pre>"

@app.route('/debug/user-structure')
def debug_user_structure():
    """Debug route to check user database structure"""
    try:
        conn = get_db()
        
        # Get table schema
        schema = conn.execute("PRAGMA table_info(users)").fetchall()
        
        result = "<h2>🔍 Users Table Structure:</h2>"
        result += "<table border='1' style='border-collapse: collapse; margin: 20px 0;'>"
        result += "<tr><th>Column</th><th>Type</th><th>Not Null</th><th>Default</th></tr>"
        
        for col in schema:
            result += f"<tr><td>{col[1]}</td><td>{col[2]}</td><td>{col[3]}</td><td>{col[4]}</td></tr>"
        
        result += "</table>"
        
        # Get a sample user to see actual data
        users = conn.execute('SELECT * FROM users LIMIT 1').fetchall()
        if users:
            user = users[0]
            result += "<h3>📋 Sample User Data:</h3>"
            result += "<ul>"
            for key in user.keys():
                result += f"<li><strong>{key}:</strong> {user[key]} ({type(user[key]).__name__})</li>"
            result += "</ul>"
        
        conn.close()
        return result
        
    except Exception as e:
        import traceback
        return f"<h2>❌ Error: {e}</h2><pre>{traceback.format_exc()}</pre>"

@app.route('/debug/users')
def debug_users():
    """Debug route to check users in database"""
    try:
        conn = get_db()
        
        # Check if users table exists
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'").fetchall()
        if not tables:
            return "<h2>❌ Users table does not exist!</h2>"
        
        # Get all users
        users = conn.execute('SELECT * FROM users ORDER BY created_at DESC').fetchall()
        conn.close()
        
        result = f"<h2>✅ Users in Database ({len(users)} total):</h2>"
        if users:
            for user in users:
                result += f"<div style='border:1px solid #ccc; padding:10px; margin:10px;'>"
                result += f"<strong>ID:</strong> {user['id']}<br>"
                result += f"<strong>Name:</strong> {user['name']}<br>"
                result += f"<strong>Email:</strong> {user['email']}<br>"
                result += f"<strong>Active:</strong> {user['is_active']}<br>"
                result += f"<strong>Token:</strong> {user['activation_token'][:20] if user['activation_token'] else 'None'}...<br>"
                result += f"<strong>Created:</strong> {user['created_at']}<br>"
                result += f"</div>"
        else:
            result += "<p>❌ No users found in database</p>"
        
        # Also check database schema
        result += "<h3>Users Table Schema:</h3>"
        schema = conn.execute("PRAGMA table_info(users)").fetchall()
        for col in schema:
            result += f"<p>{col}</p>"
        
        return result
    except Exception as e:
        import traceback
        return f"<h2>❌ Error: {e}</h2><pre>{traceback.format_exc()}</pre>"

@app.route('/admin/users')
@admin_required
def admin_users():
    """Admin users management panel"""
    try:
        conn = get_db()
        search = request.args.get('search', '').strip()
        
        if search:
            users = conn.execute('''SELECT id, name, email, is_active, is_admin, created_at 
                                   FROM users 
                                   WHERE LOWER(name) LIKE LOWER(?) OR LOWER(email) LIKE LOWER(?)
                                   ORDER BY created_at DESC''', 
                                (f'%{search}%', f'%{search}%')).fetchall()
        else:
            users = conn.execute('''SELECT id, name, email, is_active, is_admin, created_at 
                                   FROM users 
                                   ORDER BY created_at DESC''').fetchall()
        
        conn.close()
        return render_template('admin_users.html', users=users, search=search)
    except Exception as e:
        print(f"❌ Error in admin_users route: {e}")
        import traceback
        traceback.print_exc()
        flash('Error loading users. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/users/toggle/<int:user_id>')
@admin_required
def admin_toggle_user(user_id):
    """Toggle user active status"""
    try:
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        new_status = not user['is_active']
        
        # Clear activation token when manually activating
        if new_status:
            conn.execute('UPDATE users SET is_active = ?, activation_token = NULL WHERE id = ?', 
                        (new_status, user_id))
        else:
            conn.execute('UPDATE users SET is_active = ? WHERE id = ?', (new_status, user_id))
        
        conn.commit()
        conn.close()
        
        status_text = "activated" if new_status else "deactivated"
        flash(f'✅ User {user["name"]} has been {status_text}.', 'success')
        print(f"✅ Admin {status_text} user: {user['name']} ({user['email']})")
        
    except Exception as e:
        print(f"❌ Error toggling user status: {e}")
        flash('Error updating user status. Please try again.', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/users/delete/<int:user_id>')
@admin_required
def admin_delete_user(user_id):
    """Delete user account"""
    try:
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('admin_users'))
        
        # Delete user and their orders
        conn.execute('DELETE FROM orders WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        conn.close()
        
        flash(f'✅ User {user["name"]} has been deleted.', 'success')
        print(f"✅ Admin deleted user: {user['name']} ({user['email']})")
        
    except Exception as e:
        print(f"❌ Error deleting user: {e}")
        flash('Error deleting user. Please try again.', 'error')
    
    return redirect(url_for('admin_users'))

@app.route('/admin/products')
@admin_required
def admin_products():
    conn = get_db()
    products_raw = conn.execute('''
        SELECT p.*, c.name as category_name, c.icon as category_icon
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.created_at DESC
    ''').fetchall()
    
    # Convert to list of dicts and add additional data
    products = []
    for product in products_raw:
        product_dict = dict(product)
        
        # Get order count for this product
        order_count = conn.execute('SELECT COUNT(*) FROM orders WHERE product_id = ? AND status = "confirmed"', 
                                 (product['id'],)).fetchone()[0]
        product_dict['orders'] = [None] * order_count  # Create a list with the right length for template
        
        # Get product tags
        product_dict['tags'] = get_product_tags(product['id'])
        
        # Get available stock for key products
        if product['type'] == 'key':
            available_keys = conn.execute(
                'SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                (product['id'],)
            ).fetchone()[0]
            product_dict['available_keys'] = available_keys
        
        # Get image data
        product_dict['image_urls'] = get_product_images(product['images'])
        product_dict['main_image'] = product_dict['image_urls'][0] if product_dict['image_urls'] else None
        
        products.append(product_dict)
    
    conn.close()
    try:
        return render_template('admin_products.html', products=products)
    except Exception as e:
        flash(f'Template error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    """Admin orders management page with search functionality"""
    search_query = request.args.get('search', '').strip()
    conn = get_db()
    
    # Get orders with optional search filtering
    if search_query:
        # Clean the search query - remove # symbol if present for ID search
        clean_query = search_query.replace('#', '').strip()
        
        # Search by order ID, buyer name, or email
        # Try exact ID match first, then partial matches
        orders_raw = conn.execute('''SELECT o.*, p.name as product_name, p.price_dzd, p.type as product_type,
                                            u.name as user_name, u.email as user_email
                                    FROM orders o 
                                    JOIN products p ON o.product_id = p.id 
                                    LEFT JOIN users u ON o.user_id = u.id
                                    WHERE o.id = ? 
                                       OR CAST(o.id AS TEXT) LIKE ? 
                                       OR o.buyer_name LIKE ? 
                                       OR o.email LIKE ?
                                       OR u.name LIKE ?
                                       OR u.email LIKE ?
                                    ORDER BY o.created_at DESC''', 
                                 (clean_query if clean_query.isdigit() else -1, 
                                  f'%{clean_query}%', f'%{search_query}%', f'%{search_query}%',
                                  f'%{search_query}%', f'%{search_query}%')).fetchall()
    else:
        # Get all orders with product info and user info
        orders_raw = conn.execute('''SELECT o.*, p.name as product_name, p.price_dzd, p.type as product_type,
                                            u.name as user_name, u.email as user_email
                                    FROM orders o 
                                    JOIN products p ON o.product_id = p.id 
                                    LEFT JOIN users u ON o.user_id = u.id
                                    ORDER BY o.created_at DESC''').fetchall()
    
    # Convert to list of dicts and handle datetime conversion
    orders = []
    for order in orders_raw:
        order_dict = dict(order)
        # Convert created_at string to datetime if needed
        if order_dict.get('created_at') and isinstance(order_dict['created_at'], str):
            try:
                # Handle different datetime string formats
                created_at_str = order_dict['created_at']
                if 'T' in created_at_str:
                    order_dict['created_at'] = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                else:
                    order_dict['created_at'] = datetime.strptime(created_at_str, '%Y-%m-%d %H:%M:%S')
            except Exception as e:
                order_dict['created_at_display'] = order_dict['created_at'][:16] if order_dict['created_at'] else 'N/A'
        orders.append(order_dict)
    
    # Get summary stats
    total_orders = len(orders)
    pending_orders = len([o for o in orders if o['status'] == 'pending'])
    confirmed_orders = len([o for o in orders if o['status'] == 'confirmed'])
    rejected_orders = len([o for o in orders if o['status'] == 'rejected'])
    
    conn.close()
    
    try:
        return render_template('admin_orders.html', 
                             orders=orders,
                             total_orders=total_orders,
                             pending_orders=pending_orders,
                             confirmed_orders=confirmed_orders,
                             rejected_orders=rejected_orders,
                             search_query=search_query)
    except Exception as e:
        flash(f'Template error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_product', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price_dzd = float(request.form.get('price_dzd'))
        product_type = request.form.get('type')
        category_id = request.form.get('category_id')
        tag_ids = request.form.getlist('tag_ids')
        is_visible = 'is_visible' in request.form
        is_featured = 'is_featured' in request.form
        stock_limit = request.form.get('stock_limit')
        
        # Convert empty strings to None for database
        category_id = int(category_id) if category_id else None
        stock_limit = int(stock_limit) if stock_limit else None
        
        # Handle stock count based on product type
        if product_type == 'key':
            stock_count = 0  # Will be updated after adding keys
        else:
            # Digital files have unlimited stock (set to 999999 to represent unlimited)
            stock_count = 999999
        
        file_or_key_path = None
        
        # Handle product images
        product_images = request.files.getlist('product_images')
        images_json = save_product_images(product_images)
        
        if product_type == 'file' and 'product_file' in request.files:
            file = request.files['product_file']
            if file and file.filename:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['PRODUCTS_FOLDER'], filename)
                file.save(file_path)
                file_or_key_path = file_path
        elif product_type == 'key':
            key_content = request.form.get('key_content')
            file_or_key_path = 'MANAGED_KEYS'  # Placeholder for key products
        
        conn = get_db()
        cursor = conn.execute('''INSERT INTO products 
                               (name, description, price_dzd, stock_count, type, file_or_key_path, images, 
                                category_id, is_visible, is_featured, stock_limit)
                               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                            (name, description, price_dzd, stock_count, product_type, file_or_key_path, 
                             images_json, category_id, is_visible, is_featured, stock_limit))
        product_id = cursor.lastrowid
        
        # Add tags to product
        for tag_id in tag_ids:
            if tag_id:
                conn.execute('INSERT INTO product_tags (product_id, tag_id) VALUES (?, ?)',
                           (product_id, int(tag_id)))
        
        # If it's a key product, store individual keys
        if product_type == 'key' and key_content:
            keys = [key.strip() for key in key_content.split('\n') if key.strip()]
            for key_value in keys:
                conn.execute('''INSERT INTO product_keys (product_id, key_value) VALUES (?, ?)''',
                           (product_id, key_value))
            
            # Update stock count to match actual number of keys
            actual_stock = len(keys)
            conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (actual_stock, product_id))
            print(f"✅ Added {actual_stock} keys for product '{name}'")
        
        conn.commit()
        conn.close()
        
        flash('Product added successfully', 'success')
        return redirect(url_for('admin_products'))
    
    try:
        # Get categories and tags for the form
        categories = get_categories()
        tags = get_tags()
        return render_template('add_product.html', categories=categories, tags=tags)
    except Exception as e:
        flash(f'Template error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_product/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    conn = get_db()
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price_dzd = float(request.form.get('price_dzd'))
        
        # Get current product info
        product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
        if not product:
            flash('Product not found', 'error')
            conn.close()
            return redirect(url_for('admin_products'))
        
        # Handle product images
        product_images = request.files.getlist('product_images')
        if product_images and any(img.filename for img in product_images):
            # Save new images
            new_images_json = save_product_images(product_images)
            if new_images_json:
                # Get existing images
                existing_images = product['images'] or '[]'
                try:
                    existing_list = json.loads(existing_images)
                except json.JSONDecodeError:
                    # Handle old comma-separated format
                    existing_list = [img.strip() for img in existing_images.split(',') if img.strip()]
                
                # Combine existing and new images
                new_list = json.loads(new_images_json)
                combined_list = existing_list + new_list
                combined_json = json.dumps(combined_list)
                
                # Update product with new images
                conn.execute('''UPDATE products SET name = ?, description = ?, price_dzd = ?, images = ? WHERE id = ?''',
                            (name, description, price_dzd, combined_json, product_id))
            else:
                # Update without changing images
                conn.execute('''UPDATE products SET name = ?, description = ?, price_dzd = ? WHERE id = ?''',
                            (name, description, price_dzd, product_id))
        else:
            # Update basic product info without changing images
            conn.execute('''UPDATE products SET name = ?, description = ?, price_dzd = ? WHERE id = ?''',
                        (name, description, price_dzd, product_id))
        
        # Handle KEY product updates
        if product['type'] == 'key':
            # Add new keys
            key_content = request.form.get('key_content')
            if key_content:
                existing_keys = conn.execute('SELECT key_value FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                           (product_id,)).fetchall()
                existing_key_values = [row['key_value'] for row in existing_keys]
                
                new_keys = [key.strip() for key in key_content.split('\n') if key.strip()]
                added_count = 0
                for key_value in new_keys:
                    if key_value not in existing_key_values:
                        conn.execute('''INSERT INTO product_keys (product_id, key_value) VALUES (?, ?)''',
                                   (product_id, key_value))
                        added_count += 1
                
                if added_count > 0:
                    flash(f'Added {added_count} new keys', 'success')
            
            # Update stock count for key products
            total_available = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                         (product_id,)).fetchone()[0]
            conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (total_available, product_id))
        
        # Handle FILE product updates
        elif product['type'] == 'file':
            # Check if new file was uploaded
            if 'product_file' in request.files and request.files['product_file'].filename:
                file = request.files['product_file']
                if file and file.filename:
                    # Delete old file if it exists
                    if product['file_or_key_path'] and os.path.exists(product['file_or_key_path']):
                        try:
                            os.remove(product['file_or_key_path'])
                            print(f"✅ Deleted old file: {product['file_or_key_path']}")
                        except Exception as e:
                            print(f"⚠️ Could not delete old file: {e}")
                    
                    # Save new file
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config['PRODUCTS_FOLDER'], filename)
                    file.save(file_path)
                    
                    # Update file path in database
                    conn.execute('UPDATE products SET file_or_key_path = ? WHERE id = ?', (file_path, product_id))
                    flash(f'File updated successfully: {filename}', 'success')
            
            # Update stock for file products if provided
            new_stock = request.form.get('file_stock')
            if new_stock:
                try:
                    stock_count = int(new_stock)
                    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (stock_count, product_id))
                    flash(f'Stock updated to {stock_count}', 'success')
                except ValueError:
                    flash('Invalid stock count', 'error')
        
        conn.commit()
        conn.close()
        
        flash('Product updated successfully', 'success')
        return redirect(url_for('admin_products'))
    
    # GET request - show edit form
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if not product:
        flash('Product not found', 'error')
        return redirect(url_for('admin_products'))
    
    # Get existing keys for key products
    existing_keys = []
    if product['type'] == 'key':
        key_rows = conn.execute('SELECT id, key_value, is_used FROM product_keys WHERE product_id = ? ORDER BY created_at',
                              (product_id,)).fetchall()
        existing_keys = [{'id': row['id'], 'value': row['key_value'], 'used': row['is_used']} for row in key_rows]
    
    conn.close()
    
    try:
        return render_template('edit_product.html', product=product, existing_keys=existing_keys)
    except Exception as e:
        flash(f'Template error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_key/<int:key_id>', methods=['POST'])
@admin_required
def delete_key(key_id):
    """Delete an individual key from a product"""
    conn = get_db()
    
    # Get key info
    key_info = conn.execute('SELECT product_id, key_value, is_used FROM product_keys WHERE id = ?', (key_id,)).fetchone()
    
    if not key_info:
        flash('Key not found', 'error')
        conn.close()
        return redirect(url_for('admin_products'))
    
    if key_info['is_used']:
        flash('Cannot delete used key', 'error')
        conn.close()
        return redirect(url_for('edit_product', product_id=key_info['product_id']))
    
    # Delete the key
    conn.execute('DELETE FROM product_keys WHERE id = ?', (key_id,))
    
    # Update stock count
    remaining_keys = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                (key_info['product_id'],)).fetchone()[0]
    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?', (remaining_keys, key_info['product_id']))
    
    conn.commit()
    conn.close()
    
    flash(f'Key "{key_info["key_value"]}" deleted successfully', 'success')
    return redirect(url_for('edit_product', product_id=key_info['product_id']))

@app.route('/admin/delete_product/<int:product_id>', methods=['POST'])
@admin_required
def delete_product(product_id):
    conn = get_db()
    
    # Check if product has any orders
    orders = conn.execute('SELECT COUNT(*) FROM orders WHERE product_id = ?', (product_id,)).fetchone()[0]
    
    if orders > 0:
        flash('Cannot delete product with existing orders', 'error')
        conn.close()
        return redirect(url_for('admin_products'))
    
    # Get product info for cleanup
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if product:
        # Delete associated keys
        conn.execute('DELETE FROM product_keys WHERE product_id = ?', (product_id,))
        
        # Delete product file if it exists
        if product['type'] == 'file' and product['file_or_key_path'] and os.path.exists(product['file_or_key_path']):
            try:
                os.remove(product['file_or_key_path'])
            except Exception as e:
                print(f"Warning: Could not delete file {product['file_or_key_path']}: {e}")
        
        # Delete product images
        if product['images']:
            delete_product_images(product['images'])
        
        # Delete product
        conn.execute('DELETE FROM products WHERE id = ?', (product_id,))
        conn.commit()
        
        flash(f'Product "{product["name"]}" deleted successfully', 'success')
    else:
        flash('Product not found', 'error')
    
    conn.close()
    return redirect(url_for('admin_products'))

@app.route('/admin/remove_image/<int:product_id>/<filename>', methods=['POST'])
@admin_required
def remove_image(product_id, filename):
    conn = get_db()
    
    # Get current product
    product = conn.execute('SELECT images FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if product and product['images']:
        try:
            # Parse JSON images
            image_list = json.loads(product['images'])
            # Remove filename from list
            image_list = [img for img in image_list if img != filename]
            new_images_json = json.dumps(image_list) if image_list else None
        except json.JSONDecodeError:
            # Handle old comma-separated format
            image_list = [img.strip() for img in product['images'].split(',') if img.strip() != filename]
            new_images_json = json.dumps(image_list) if image_list else None
        
        # Update database
        conn.execute('UPDATE products SET images = ? WHERE id = ?', (new_images_json, product_id))
        conn.commit()
        
        # Delete file from filesystem
        file_path = os.path.join('static', 'products', filename)
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Warning: Could not delete image file {filename}: {e}")
    
    conn.close()
    return jsonify({'success': True})

@app.route('/admin/reset_store', methods=['GET', 'POST'])
@admin_required
def reset_store():
    if request.method == 'POST':
        confirmation = request.form.get('confirmation')
        if confirmation == 'RESET_MY_STORE':
            conn = get_db()
            
            try:
                # Get all product files before deletion
                products_with_files = conn.execute('SELECT file_or_key_path FROM products WHERE type = "file" AND file_or_key_path IS NOT NULL').fetchall()
                
                # Delete all orders first
                conn.execute('DELETE FROM orders')
                print("✅ Deleted all orders")
                
                # Delete all audit logs
                conn.execute('DELETE FROM audit_log')
                print("✅ Deleted all audit logs")
                
                # Delete all product keys
                conn.execute('DELETE FROM product_keys')
                print("✅ Deleted all product keys")
                
                # Delete product files from filesystem
                for product in products_with_files:
                    file_path = product['file_or_key_path']
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                            print(f"✅ Deleted file: {file_path}")
                        except Exception as e:
                            print(f"⚠️ Could not delete file {file_path}: {e}")
                
                # Delete all products
                conn.execute('DELETE FROM products')
                print("✅ Deleted all products")
                
                # Clean up receipt files
                receipts_dir = 'receipts'
                if os.path.exists(receipts_dir):
                    for filename in os.listdir(receipts_dir):
                        file_path = os.path.join(receipts_dir, filename)
                        try:
                            os.remove(file_path)
                            print(f"✅ Deleted receipt: {filename}")
                        except Exception as e:
                            print(f"⚠️ Could not delete receipt {filename}: {e}")
                
                # Clean up payment proof files
                uploads_dir = 'uploads'
                if os.path.exists(uploads_dir):
                    for filename in os.listdir(uploads_dir):
                        file_path = os.path.join(uploads_dir, filename)
                        try:
                            os.remove(file_path)
                            print(f"✅ Deleted upload: {filename}")
                        except Exception as e:
                            print(f"⚠️ Could not delete upload {filename}: {e}")
                
                conn.commit()
                conn.close()
                
                flash('🎉 Store reset successfully! You can now start fresh with new products.', 'success')
                return redirect(url_for('admin_dashboard'))
                
            except Exception as e:
                conn.rollback()
                conn.close()
                flash(f'Error resetting store: {e}', 'error')
                return redirect(url_for('reset_store'))
        else:
            flash('Incorrect confirmation text. Please type "RESET_MY_STORE" exactly.', 'error')
    
    try:
        return render_template('admin_reset_store.html')
    except Exception as e:
        flash(f'Template error: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_all_orders', methods=['POST'])
@admin_required
def delete_all_orders():
    """Delete all orders only (keep products)"""
    confirmation = request.form.get('confirmation')
    if confirmation == 'DELETE_ALL_ORDERS':
        conn = get_db()
        
        try:
            # Delete all audit logs first (foreign key constraint)
            conn.execute('DELETE FROM audit_log')
            
            # Delete all orders
            orders_count = conn.execute('SELECT COUNT(*) FROM orders').fetchone()[0]
            conn.execute('DELETE FROM orders')
            
            # Clean up receipt files
            receipts_dir = 'receipts'
            if os.path.exists(receipts_dir):
                for filename in os.listdir(receipts_dir):
                    file_path = os.path.join(receipts_dir, filename)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"⚠️ Could not delete receipt {filename}: {e}")
            
            # Clean up payment proof files
            uploads_dir = 'uploads'
            if os.path.exists(uploads_dir):
                for filename in os.listdir(uploads_dir):
                    file_path = os.path.join(uploads_dir, filename)
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"⚠️ Could not delete upload {filename}: {e}")
            
            conn.commit()
            conn.close()
            
            flash(f'✅ Deleted {orders_count} orders successfully! You can now delete products if needed.', 'success')
        except Exception as e:
            conn.rollback()
            conn.close()
            flash(f'Error deleting orders: {e}', 'error')
    else:
        flash('Incorrect confirmation text. Please type "DELETE_ALL_ORDERS" exactly.', 'error')
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/confirm_order/<int:order_id>')
@admin_required
def confirm_order(order_id):
    conn = get_db()
    
    # Get order and product info
    order = conn.execute('''SELECT o.*, p.name as product_name, p.type, p.file_or_key_path, p.stock_count, p.price_dzd
                           FROM orders o 
                           JOIN products p ON o.product_id = p.id 
                           WHERE o.id = ?''', (order_id,)).fetchone()
    
    if not order or order['status'] != 'pending':
        flash('Order not found or already processed', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Update order status
    confirmation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    conn.execute('UPDATE orders SET status = "confirmed", confirmed_at = ? WHERE id = ?',
                (confirmation_time, order_id))
    
    # Decrease stock (for key products, this is handled in get_available_key)
    if order['type'] != 'key':
        conn.execute('UPDATE products SET stock_count = stock_count - 1 WHERE id = ?',
                    (order['product_id'],))
    else:
        # For key products, update stock to reflect available unused keys
        available_keys = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                    (order['product_id'],)).fetchone()[0]
        conn.execute('UPDATE products SET stock_count = ? WHERE id = ?',
                    (available_keys, order['product_id']))
    
    conn.commit()
    
    # Get updated order data for receipt generation and delivery
    updated_order = conn.execute('''SELECT o.*, p.name as product_name, p.type, p.file_or_key_path, p.price_dzd
                                   FROM orders o 
                                   JOIN products p ON o.product_id = p.id 
                                   WHERE o.id = ?''', (order_id,)).fetchone()
    
    conn.close()
    
    # Log action
    log_action(order_id, 'order_confirmed', 'admin')
    
    # Send product to buyer (receipt will be generated in deliver_product)
    deliver_product(updated_order)  # Use updated_order instead of order
    
    flash('Order confirmed, product delivered, and receipt generated', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject_order/<int:order_id>')
@admin_required
def reject_order(order_id):
    conn = get_db()
    
    # Get order info before rejecting
    order = conn.execute('''SELECT o.*, p.name as product_name
                           FROM orders o 
                           JOIN products p ON o.product_id = p.id 
                           WHERE o.id = ?''', (order_id,)).fetchone()
    
    conn.execute('UPDATE orders SET status = "rejected" WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    
    # Notify buyer if order exists
    if order:
        notify_buyer_rejection(order)
    
    log_action(order_id, 'order_rejected', 'admin')
    
    flash('Order rejected and buyer notified', 'success')
    return redirect(url_for('admin_dashboard'))

def send_telegram_message_to_user(telegram_identifier, message):
    """Send a direct message to a user via Telegram"""
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token or not telegram_identifier:
        print(f"❌ Missing bot token or telegram identifier")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
        # Try different formats for chat_id
        chat_formats = []
        
        # If it looks like a chat ID (numbers), use it directly
        if telegram_identifier.isdigit():
            chat_formats.append(telegram_identifier)
        # If it starts with @, try both with and without @
        elif telegram_identifier.startswith('@'):
            chat_formats.append(telegram_identifier)
            chat_formats.append(telegram_identifier[1:])  # Remove @
        else:
            # Try both with and without @
            chat_formats.append(f"@{telegram_identifier}")
            chat_formats.append(telegram_identifier)
        
        # Try each format
        for chat_id in chat_formats:
            try:
                data = {
                    "chat_id": chat_id,
                    "text": message
                }
                response = requests.post(url, json=data)
                
                if response.status_code == 200:
                    print(f"✅ Message sent successfully to {chat_id}")
                    return True
                else:
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                    error_description = error_data.get('description', 'Unknown error')
                    print(f"❌ Failed to send to {chat_id}: {response.status_code} - {error_description}")
                    
            except Exception as e:
                print(f"❌ Error trying {chat_id}: {e}")
                continue
        
        print(f"❌ All attempts failed for {telegram_identifier}")
        return False
        
    except Exception as e:
        print(f"❌ Failed to send message to user {telegram_identifier}: {e}")
        return False

def notify_buyer_rejection(order):
    """Notify buyer that their order was rejected"""
    # Send professional rejection email
    if order['email']:
        print(f"📧 Sending rejection email to {order['email']}")
        store_name = os.getenv('STORE_NAME', 'Digital Store')
        email_subject = f"Order Update - {store_name}"
        email_body = f"""We regret to inform you that your recent order could not be processed.

Order Details:
- Order ID: #{order['id']}
- Product: {order['product_name']}
- Submitted by: {order['buyer_name']}

Reason for rejection:
Unfortunately, we were unable to verify your payment. This could be due to:
- Payment screenshot was unclear or incomplete
- Payment amount did not match the order total
- Payment was sent to incorrect account details
- Technical issues with payment verification

Next Steps:
If you believe this is an error, please contact our support team with your order ID and payment details. We're here to help resolve any issues.

We apologize for any inconvenience caused."""
        
        send_email(order['email'], email_subject, email_body, order['buyer_name'], "order_rejection")
    else:
        print("📧 No email address provided for rejection notification")
    
    # Send Telegram notification if username provided
    if order['telegram_username']:
        message = f"""❌ Order #{order['id']} Rejected

Unfortunately, your payment for "{order['product_name']}" could not be verified.

Please contact support if you believe this is an error.
Order ID: #{order['id']}
Buyer: {order['buyer_name']}"""
        
        send_telegram_message_to_user(order['telegram_username'], message)
    else:
        print("📱 No Telegram username provided for rejection notification")

def get_available_key(product_id, order_id):
    """Get an available key for the product and mark it as used"""
    conn = get_db()
    
    # Get an unused key
    key_row = conn.execute('''SELECT id, key_value FROM product_keys 
                             WHERE product_id = ? AND is_used = FALSE 
                             ORDER BY created_at ASC LIMIT 1''', (product_id,)).fetchone()
    
    if key_row:
        # Mark key as used
        conn.execute('''UPDATE product_keys 
                       SET is_used = TRUE, used_by_order_id = ?, used_at = CURRENT_TIMESTAMP 
                       WHERE id = ?''', (order_id, key_row['id']))
        
        # Update product stock to reflect remaining available keys
        available_keys = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                    (product_id,)).fetchone()[0]
        conn.execute('UPDATE products SET stock_count = ? WHERE id = ?',
                    (available_keys, product_id))
        
        conn.commit()
        conn.close()
        return key_row['key_value']
    
    conn.close()
    return None

def cleanup_expired_tokens():
    """Clean up expired download tokens (optional maintenance)"""
    from datetime import datetime
    
    conn = get_db()
    deleted = conn.execute('''DELETE FROM download_tokens 
                             WHERE expires_at < ?''', 
                          (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),)).rowcount
    conn.commit()
    conn.close()
    
    if deleted > 0:
        print(f"🧹 Cleaned up {deleted} expired download tokens")
    
    return deleted

def generate_download_token(order_id, product_id, file_path):
    """Generate a secure download token for file products"""
    import uuid
    from datetime import datetime, timedelta
    
    # Clean up expired tokens (optional)
    cleanup_expired_tokens()
    
    token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(hours=48)  # 48 hours expiry
    
    conn = get_db()
    conn.execute('''INSERT INTO download_tokens 
                   (token, order_id, product_id, file_path, expires_at)
                   VALUES (?, ?, ?, ?, ?)''',
                (token, order_id, product_id, file_path, expires_at.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()
    
    print(f"✅ Generated download token for order #{order_id}: {token}")
    return token

def deliver_product(order):
    """Deliver product to buyer via Telegram and email"""
    print(f"🔄 Delivering product for order #{order['id']}")
    
    # Get product key once if it's a key product
    product_key = None
    if order['type'] == 'key':
        product_key = get_available_key(order['product_id'], order['id'])
        if not product_key:
            print(f"❌ No available keys for product {order['product_id']} in order #{order['id']}")
    
    # Prepare messages
    if order['type'] == 'key':
        if product_key:
            telegram_message = f"""✅ Your order #{order['id']} has been confirmed!

Product: {order['product_name']}
Your Key: {product_key}

Thank you for your purchase!"""
            key_info = f"Your Product Key: {product_key}"
        else:
            telegram_message = f"""✅ Your order #{order['id']} has been confirmed!

Product: {order['product_name']}
⚠️ Key delivery issue - please contact support immediately.

Thank you for your purchase!"""
            key_info = "⚠️ Key delivery issue - please contact support immediately."
    else:
        # For file products, generate download link
        file_name = os.path.basename(order['file_or_key_path']) if order['file_or_key_path'] else 'your digital product'
        
        # Generate secure download token
        if order['file_or_key_path'] and os.path.exists(order['file_or_key_path']):
            download_token = generate_download_token(order['id'], order['product_id'], order['file_or_key_path'])
            
            # Get the base URL from app config
            base_url = app.config['BASE_URL']
            download_url = f"{base_url}/download/{download_token}"
            
            telegram_message = f"""✅ Your order #{order['id']} has been confirmed!

Product: {order['product_name']}
File: {file_name}

Download your product here: {download_url}
(Link expires in 48 hours)

Thank you for your purchase!"""
            
            key_info = f"Download your product here: {download_url}\n\n(This link expires in 48 hours and allows up to 3 downloads)"
        else:
            # Fallback if file doesn't exist
            telegram_message = f"""✅ Your order #{order['id']} has been confirmed!

Product: {order['product_name']}
⚠️ File delivery issue - please contact support immediately.

Thank you for your purchase!"""
            key_info = "⚠️ File delivery issue - please contact support immediately."
    
    # Send via Telegram if username provided
    if order['telegram_username']:
        print(f"� Sendding Telegram message to @{order['telegram_username']}")
        send_telegram_message_to_user(order['telegram_username'], telegram_message)
    else:
        print("📱 No Telegram username provided")
    
    # Send confirmation email with receipt attachment
    if order['email']:
        print(f"📧 Sending confirmation email to {order['email']}")
        store_name = os.getenv('STORE_NAME', 'Digital Store')
        email_subject = f"Your Order Confirmation from {store_name}"
        
        email_body = f"""Your order has been confirmed and your product is ready!

Order Details:
- Order ID: #{order['id']}
- Product: {order['product_name']}
- Price: {order['price_dzd'] if 'price_dzd' in order.keys() else 'N/A'} DZD
- Payment Method: {order['payment_method'].upper()}

{key_info}

📄 Your official receipt is attached to this email for your records.

Thank you for choosing {store_name}!"""
        
        # Generate receipt if not already generated
        receipt_path = None
        if 'receipt_path' in order and order['receipt_path'] and os.path.exists(order['receipt_path']):
            receipt_path = order['receipt_path']
            print(f"📄 Using existing receipt: {receipt_path}")
        else:
            # Generate new receipt
            print(f"📄 Generating new receipt for order #{order['id']}")
            receipt_path = generate_receipt_pdf(dict(order))
            
            if receipt_path:
                # Update order with receipt path in database
                conn = get_db()
                conn.execute('UPDATE orders SET receipt_path = ? WHERE id = ?', (receipt_path, order['id']))
                conn.commit()
                conn.close()
                print(f"📄 Receipt generated and saved: {receipt_path}")
        
        # Send email with receipt attachment
        send_email(order['email'], email_subject, email_body, order['buyer_name'], "order_confirmation", receipt_path)
    else:
        print("📧 No email address provided")
    
    # Send notification to admin about delivery
    admin_message = f"✅ Product delivered to {order['buyer_name']} for order #{order['id']}"
    send_telegram_notification(admin_message)
    print(f"✅ Product delivery completed for order #{order['id']}")

@app.route('/webhook/telegram', methods=['POST'])
def telegram_webhook():
    """Handle Telegram bot callbacks and messages"""
    print("🔔 Telegram webhook received")
    data = request.get_json()
    print(f"📨 Webhook data: {data}")
    
    # Handle regular messages (like /start, /chatid)
    if 'message' in data:
        message = data['message']
        chat_id = message['chat']['id']
        text = message.get('text', '').lower()
        user_first_name = message['from'].get('first_name', 'Customer')
        
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if text == '/start':
            welcome_message = f"""👋 Welcome to our store, {user_first_name}!

🛍️ This bot will send you order confirmations and product deliveries.

📋 Your Chat ID: `{chat_id}`
(You can use this instead of your username when placing orders)

🔔 You're now set up to receive notifications!

Visit our store to make your first purchase."""
            
            send_bot_message(chat_id, welcome_message)
            
        elif text in ['/chatid', '/id']:
            id_message = f"""📋 Your Telegram Chat ID: `{chat_id}`

💡 You can use this Chat ID when placing orders for guaranteed message delivery.

Copy this number: {chat_id}"""
            
            send_bot_message(chat_id, id_message)
    
    # Handle callback queries (admin buttons)
    if 'callback_query' in data:
        callback_data = data['callback_query']['data']
        chat_id = data['callback_query']['message']['chat']['id']
        print(f"🔘 Callback data: {callback_data}")
        
        if callback_data.startswith('confirm_'):
            order_id = int(callback_data.split('_')[1])
            print(f"✅ Confirming order #{order_id}")
            
            conn = get_db()
            order = conn.execute('''SELECT o.*, p.name as product_name, p.type, p.file_or_key_path, p.price_dzd
                                   FROM orders o 
                                   JOIN products p ON o.product_id = p.id 
                                   WHERE o.id = ?''', (order_id,)).fetchone()
            
            if order and order['status'] == 'pending':
                # Confirm order
                confirmation_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                conn.execute('UPDATE orders SET status = "confirmed", confirmed_at = ? WHERE id = ?',
                            (confirmation_time, order_id))
                # Decrease stock (for key products, this is handled in get_available_key)
                if order['type'] != 'key':
                    conn.execute('UPDATE products SET stock_count = stock_count - 1 WHERE id = ?',
                                (order['product_id'],))
                else:
                    # For key products, update stock to reflect available unused keys
                    available_keys = conn.execute('SELECT COUNT(*) FROM product_keys WHERE product_id = ? AND is_used = FALSE',
                                                (order['product_id'],)).fetchone()[0]
                    conn.execute('UPDATE products SET stock_count = ? WHERE id = ?',
                                (available_keys, order['product_id']))
                conn.commit()
                
                # Get updated order data for delivery
                updated_order = conn.execute('''SELECT o.*, p.name as product_name, p.type, p.file_or_key_path, p.price_dzd
                                               FROM orders o 
                                               JOIN products p ON o.product_id = p.id 
                                               WHERE o.id = ?''', (order_id,)).fetchone()
                
                log_action(order_id, 'order_confirmed', 'telegram_admin')
                deliver_product(updated_order)  # Receipt will be generated in deliver_product
                
                # Send confirmation to admin
                bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
                response_data = {
                    "chat_id": chat_id,
                    "text": f"✅ Order #{order_id} confirmed, product delivered, and receipt generated!"
                }
                requests.post(url, json=response_data)
            
            conn.close()
            
        elif callback_data.startswith('reject_'):
            order_id = int(callback_data.split('_')[1])
            
            conn = get_db()
            
            # Get order info before rejecting
            order = conn.execute('''SELECT o.*, p.name as product_name
                                   FROM orders o 
                                   JOIN products p ON o.product_id = p.id 
                                   WHERE o.id = ?''', (order_id,)).fetchone()
            
            conn.execute('UPDATE orders SET status = "rejected" WHERE id = ?', (order_id,))
            conn.commit()
            conn.close()
            
            # Notify buyer if order exists
            if order:
                notify_buyer_rejection(order)
            
            log_action(order_id, 'order_rejected', 'telegram_admin')
            
            # Send confirmation to admin
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            response_data = {
                "chat_id": chat_id,
                "text": f"❌ Order #{order_id} rejected and buyer notified!"
            }
            requests.post(url, json=response_data)
    
    return jsonify({"status": "ok"})

@app.route('/admin/analytics')
@admin_required
def admin_analytics():
    """Analytics and insights dashboard"""
    conn = get_db()
    
    # Get filter parameter
    days_filter = request.args.get('days', 'all')
    date_filter = ""
    if days_filter != 'all':
        try:
            days = int(days_filter)
            date_filter = f"AND o.confirmed_at >= DATE('now', '-{days} days')"
        except ValueError:
            days_filter = 'all'
    
    # Basic stats with optional date filtering
    total_orders = conn.execute(f'SELECT COUNT(*) FROM orders o WHERE o.status = "confirmed" {date_filter.replace("o.confirmed_at", "confirmed_at")}').fetchone()[0]
    total_revenue = conn.execute(f'SELECT SUM(p.price_dzd) FROM orders o JOIN products p ON o.product_id = p.id WHERE o.status = "confirmed" {date_filter}').fetchone()[0] or 0
    total_products_sold = conn.execute(f'SELECT COUNT(*) FROM orders o WHERE o.status = "confirmed" {date_filter.replace("o.confirmed_at", "confirmed_at")}').fetchone()[0]
    
    # Top buyer by total amount spent
    top_buyer = conn.execute('''
        SELECT o.buyer_name, o.email, COUNT(*) as order_count, SUM(p.price_dzd) as total_spent
        FROM orders o 
        JOIN products p ON o.product_id = p.id 
        WHERE o.status = "confirmed"
        GROUP BY o.email
        ORDER BY total_spent DESC
        LIMIT 1
    ''').fetchone()
    
    # Remaining inventory (total available stock)
    remaining_inventory = conn.execute('SELECT SUM(stock_count) FROM products').fetchone()[0] or 0
    
    # Daily revenue with date filtering
    revenue_days = 30 if days_filter == 'all' else min(int(days_filter) if days_filter != 'all' else 30, 30)
    daily_revenue = conn.execute(f'''
        SELECT DATE(o.confirmed_at) as date, SUM(p.price_dzd) as revenue
        FROM orders o 
        JOIN products p ON o.product_id = p.id 
        WHERE o.status = "confirmed" 
        AND o.confirmed_at >= DATE('now', '-{revenue_days} days')
        GROUP BY DATE(o.confirmed_at)
        ORDER BY date
    ''').fetchall()
    
    # Sales per product
    sales_per_product = conn.execute('''
        SELECT p.name, COUNT(o.id) as quantity_sold, SUM(p.price_dzd) as revenue
        FROM products p
        LEFT JOIN orders o ON p.id = o.product_id AND o.status = "confirmed"
        GROUP BY p.id, p.name
        ORDER BY quantity_sold DESC
    ''').fetchall()
    
    # Top buyers table with date filtering
    top_buyers = conn.execute(f'''
        SELECT o.buyer_name, o.email, COUNT(*) as total_purchases, SUM(p.price_dzd) as total_spent
        FROM orders o 
        JOIN products p ON o.product_id = p.id 
        WHERE o.status = "confirmed" {date_filter}
        GROUP BY o.email
        ORDER BY total_spent DESC
        LIMIT 10
    ''').fetchall()
    
    # Most sold products table
    most_sold_products = conn.execute('''
        SELECT p.name, COUNT(o.id) as quantity_sold, SUM(p.price_dzd) as revenue
        FROM products p
        LEFT JOIN orders o ON p.id = o.product_id AND o.status = "confirmed"
        GROUP BY p.id, p.name
        HAVING COUNT(o.id) > 0
        ORDER BY quantity_sold DESC
        LIMIT 10
    ''').fetchall()
    
    # Recent activity with date filtering
    recent_activity = conn.execute(f'''
        SELECT o.id, o.buyer_name, p.name as product_name, p.price_dzd, o.confirmed_at
        FROM orders o 
        JOIN products p ON o.product_id = p.id 
        WHERE o.status = "confirmed" {date_filter}
        ORDER BY o.confirmed_at DESC
        LIMIT 10
    ''').fetchall()
    
    # Monthly stats for trend analysis
    monthly_stats = conn.execute('''
        SELECT 
            strftime('%Y-%m', o.confirmed_at) as month,
            COUNT(*) as orders,
            SUM(p.price_dzd) as revenue
        FROM orders o 
        JOIN products p ON o.product_id = p.id 
        WHERE o.status = "confirmed"
        GROUP BY strftime('%Y-%m', o.confirmed_at)
        ORDER BY month DESC
        LIMIT 12
    ''').fetchall()
    
    conn.close()
    
    # Convert to lists for JSON serialization
    daily_revenue_data = [{'date': row['date'], 'revenue': float(row['revenue'])} for row in daily_revenue]
    sales_per_product_data = [{'name': row['name'], 'quantity': row['quantity_sold'], 'revenue': float(row['revenue'] or 0)} for row in sales_per_product]
    monthly_stats_data = [{'month': row['month'], 'orders': row['orders'], 'revenue': float(row['revenue'])} for row in monthly_stats]
    
    return render_template('admin_analytics.html',
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         total_products_sold=total_products_sold,
                         top_buyer=top_buyer,
                         remaining_inventory=remaining_inventory,
                         daily_revenue=daily_revenue_data,
                         sales_per_product=sales_per_product_data,
                         top_buyers=top_buyers,
                         most_sold_products=most_sold_products,
                         recent_activity=recent_activity,
                         monthly_stats=monthly_stats_data,
                         current_filter=days_filter)

@app.route('/admin/export_sales')
@admin_required
def export_sales():
    import csv
    import io
    
    conn = get_db()
    orders = conn.execute('''SELECT o.*, p.name as product_name, p.price_dzd 
                            FROM orders o 
                            JOIN products p ON o.product_id = p.id 
                            WHERE o.status = "confirmed"
                            ORDER BY o.confirmed_at DESC''').fetchall()
    conn.close()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Order ID', 'Product', 'Price (DZD)', 'Buyer Name', 'Email', 'Phone', 'Payment Method', 'Confirmed At', 'Receipt Generated'])
    
    for order in orders:
        writer.writerow([
            order['id'], order['product_name'], order['price_dzd'],
            order['buyer_name'], order['email'], order['phone'] or 'N/A', order['payment_method'],
            order['confirmed_at'], 'Yes' if 'receipt_path' in order.keys() and order['receipt_path'] else 'No'
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='sales_export.csv'
    )

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded payment proof files (public access for admin viewing)"""
    # Check if user is admin (but don't redirect, just return 403)
    if not session.get('admin_logged_in'):
        print(f"🔒 Unauthorized access attempt to: {filename}")
        return jsonify({'error': 'Unauthorized'}), 403
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    print(f"🔍 Admin requesting file: {filename}")
    print(f"🔍 Full file path: {file_path}")
    print(f"🔍 File exists: {os.path.exists(file_path)}")
    
    if not os.path.exists(file_path):
        print(f"❌ Payment proof file not found: {file_path}")
        # List files in uploads directory for debugging
        if os.path.exists(app.config['UPLOAD_FOLDER']):
            files = os.listdir(app.config['UPLOAD_FOLDER'])
            print(f"🔍 Files in uploads directory: {files}")
        else:
            print(f"❌ Uploads directory doesn't exist: {app.config['UPLOAD_FOLDER']}")
        
        return jsonify({'error': 'File not found'}), 404
    
    try:
        print(f"✅ Serving file to admin: {file_path}")
        return send_file(file_path)
    except Exception as e:
        print(f"❌ Error serving payment proof file: {e}")
        return jsonify({'error': 'Error loading file'}), 500

@app.route('/admin/download_receipt/<int:order_id>')
@admin_required
def download_receipt(order_id):
    """Download PDF receipt for confirmed order"""
    conn = get_db()
    order = conn.execute('SELECT receipt_path FROM orders WHERE id = ? AND status = "confirmed"', (order_id,)).fetchone()
    conn.close()
    
    if not order or not order['receipt_path']:
        flash('Receipt not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if not os.path.exists(order['receipt_path']):
        flash('Receipt file not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    return send_file(order['receipt_path'], as_attachment=True, download_name=f"receipt_{order_id}.pdf")

@app.route('/admin/payment-proof/<filename>')
@admin_required
def admin_payment_proof(filename):
    """Serve payment proof images for admin viewing with proper headers"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    print(f"🖼️ Admin payment proof request: {filename}")
    print(f"🖼️ File path: {file_path}")
    print(f"🖼️ File exists: {os.path.exists(file_path)}")
    
    if not os.path.exists(file_path):
        print(f"❌ Payment proof not found: {file_path}")
        return jsonify({'error': 'Payment proof not found'}), 404
    
    try:
        print(f"✅ Serving payment proof: {file_path}")
        # Send file with proper headers for image display
        response = send_file(file_path)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        return response
    except Exception as e:
        print(f"❌ Error serving payment proof: {e}")
        return jsonify({'error': 'Error loading payment proof'}), 500

@app.route('/test-upload/<filename>')
def test_upload(filename):
    """Test route to serve uploads without authentication (for debugging)"""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    print(f"🧪 Test route - trying to serve: {file_path}")
    
    if os.path.exists(file_path):
        print(f"✅ Test route - file exists, serving: {file_path}")
        return send_file(file_path)
    else:
        print(f"❌ Test route - file not found: {file_path}")
        return f"File not found: {file_path}", 404

@app.route('/admin/download-tokens')
@admin_required
def admin_download_tokens():
    """View and manage download tokens"""
    conn = get_db()
    
    tokens = conn.execute('''
        SELECT dt.*, o.buyer_name, o.email, p.name as product_name
        FROM download_tokens dt
        JOIN orders o ON dt.order_id = o.id
        JOIN products p ON dt.product_id = p.id
        ORDER BY dt.created_at DESC
        LIMIT 50
    ''').fetchall()
    
    conn.close()
    
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Download Tokens - Admin</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css">
    </head>
    <body class="bg-light">
        <div class="container py-4">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h2><i class="bi bi-download me-2"></i>Download Tokens</h2>
                <a href="{{ url_for('admin_orders') }}" class="btn btn-outline-primary">← Back to Orders</a>
            </div>
            
            {% if tokens %}
            <div class="card">
                <div class="table-responsive">
                    <table class="table table-hover mb-0">
                        <thead class="table-light">
                            <tr>
                                <th>Token</th>
                                <th>Order</th>
                                <th>Customer</th>
                                <th>Product</th>
                                <th>Downloads</th>
                                <th>Status</th>
                                <th>Expires</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for token in tokens %}
                            <tr>
                                <td><code>{{ token.token[:8] }}...</code></td>
                                <td>#{{ token.order_id }}</td>
                                <td>{{ token.buyer_name }}</td>
                                <td>{{ token.product_name }}</td>
                                <td>{{ token.download_count }}/{{ token.max_downloads }}</td>
                                <td>
                                    {% if token.download_count >= token.max_downloads %}
                                        <span class="badge bg-danger">Exhausted</span>
                                    {% else %}
                                        <span class="badge bg-success">Active</span>
                                    {% endif %}
                                </td>
                                <td>{{ token.expires_at[:16] }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            {% else %}
            <div class="text-center py-5">
                <i class="bi bi-download text-muted" style="font-size: 4rem;"></i>
                <h4 class="text-muted mt-3">No Download Tokens</h4>
                <p class="text-muted">Download tokens will appear here when file products are delivered.</p>
            </div>
            {% endif %}
        </div>
    </body>
    </html>
    ''', tokens=tokens)

@app.route('/admin/debug/uploads')
@admin_required
def debug_uploads():
    """Debug route to check uploads directory"""
    upload_folder = app.config['UPLOAD_FOLDER']
    
    debug_info = {
        'upload_folder': upload_folder,
        'folder_exists': os.path.exists(upload_folder),
        'files': []
    }
    
    if os.path.exists(upload_folder):
        try:
            files = os.listdir(upload_folder)
            for file in files:
                file_path = os.path.join(upload_folder, file)
                debug_info['files'].append({
                    'name': file,
                    'path': file_path,
                    'exists': os.path.exists(file_path),
                    'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
                })
        except Exception as e:
            debug_info['error'] = str(e)
    
    return jsonify(debug_info)

@app.route('/admin/analytics/api')
@admin_required
def analytics_api():
    """API endpoint for real-time analytics data"""
    conn = get_db()
    
    # Get basic stats
    stats = {
        'total_orders': conn.execute('SELECT COUNT(*) FROM orders WHERE status = "confirmed"').fetchone()[0],
        'total_revenue': conn.execute('SELECT SUM(p.price_dzd) FROM orders o JOIN products p ON o.product_id = p.id WHERE o.status = "confirmed"').fetchone()[0] or 0,
        'pending_orders': conn.execute('SELECT COUNT(*) FROM orders WHERE status = "pending"').fetchone()[0],
        'remaining_inventory': conn.execute('SELECT SUM(stock_count) FROM products').fetchone()[0] or 0
    }
    
    conn.close()
    return jsonify(stats)

@app.route('/admin/contact-messages')
@admin_required
def admin_contact_messages():
    """Admin page to view contact messages"""
    conn = get_db()
    messages = conn.execute('''
        SELECT * FROM contact_messages 
        ORDER BY created_at DESC
    ''').fetchall()
    conn.close()
    
    # Convert to list of dicts for easier template handling
    messages_list = []
    for msg in messages:
        msg_dict = dict(msg)
        # Format datetime for display
        if msg_dict.get('created_at'):
            try:
                if isinstance(msg_dict['created_at'], str):
                    msg_dict['created_at'] = datetime.fromisoformat(msg_dict['created_at'].replace('Z', '+00:00'))
            except:
                pass
        messages_list.append(msg_dict)
    
    return render_template('admin_contact_messages.html', messages=messages_list)

@app.route('/admin/mark-message-read/<int:message_id>', methods=['POST'])
@admin_required
def mark_message_read(message_id):
    """Mark a contact message as read"""
    conn = get_db()
    conn.execute('UPDATE contact_messages SET status = ? WHERE id = ?', ('read', message_id))
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

@app.route('/admin/categories')
@admin_required
def admin_categories():
    """Admin categories management page"""
    categories = get_categories()
    return render_template('admin_categories.html', categories=categories)

@app.route('/admin/add_category', methods=['POST'])
@admin_required
def add_category():
    """Add a new category"""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    icon = request.form.get('icon', '').strip()
    
    if not name:
        flash('Category name is required', 'error')
        return redirect(url_for('admin_categories'))
    
    try:
        conn = get_db()
        conn.execute('INSERT INTO categories (name, description, icon) VALUES (?, ?, ?)',
                    (name, description, icon))
        conn.commit()
        conn.close()
        flash(f'Category "{name}" added successfully', 'success')
    except sqlite3.IntegrityError:
        flash('Category name already exists', 'error')
    except Exception as e:
        flash(f'Error adding category: {str(e)}', 'error')
    
    return redirect(url_for('admin_categories'))

@app.route('/admin/tags')
@admin_required
def admin_tags():
    """Admin tags management page"""
    tags = get_tags()
    return render_template('admin_tags.html', tags=tags)

@app.route('/admin/add_tag', methods=['POST'])
@admin_required
def add_tag():
    """Add a new tag"""
    name = request.form.get('name', '').strip()
    color = request.form.get('color', '#007bff').strip()
    
    if not name:
        flash('Tag name is required', 'error')
        return redirect(url_for('admin_tags'))
    
    try:
        conn = get_db()
        conn.execute('INSERT INTO tags (name, color) VALUES (?, ?)', (name, color))
        conn.commit()
        conn.close()
        flash(f'Tag "{name}" added successfully', 'success')
    except sqlite3.IntegrityError:
        flash('Tag name already exists', 'error')
    except Exception as e:
        flash(f'Error adding tag: {str(e)}', 'error')
    
    return redirect(url_for('admin_tags'))

@app.route('/admin/bundles')
@admin_required
def admin_bundles():
    """Admin bundles management page"""
    bundles = get_bundles()
    products = conn.execute('SELECT id, name, price_dzd FROM products WHERE is_visible = TRUE').fetchall()
    return render_template('admin_bundles.html', bundles=bundles, products=products)

@app.route('/admin/add_bundle', methods=['GET', 'POST'])
@admin_required
def add_bundle():
    """Add a new bundle"""
    if request.method == 'GET':
        conn = get_db()
        products = conn.execute('SELECT id, name, price_dzd FROM products WHERE is_visible = TRUE').fetchall()
        conn.close()
        return render_template('admin_add_bundle.html', products=products)
    
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    discount_type = request.form.get('discount_type', 'percentage')
    discount_value = float(request.form.get('discount_value', 0))
    product_ids = request.form.getlist('product_ids')
    is_visible = 'is_visible' in request.form
    
    if not name or not product_ids:
        flash('Bundle name and at least one product are required', 'error')
        return redirect(url_for('add_bundle'))
    
    try:
        conn = get_db()
        
        # Create bundle
        if discount_type == 'percentage':
            cursor = conn.execute('INSERT INTO bundles (name, description, discount_percentage, is_visible) VALUES (?, ?, ?, ?)',
                                (name, description, discount_value, is_visible))
        else:
            cursor = conn.execute('INSERT INTO bundles (name, description, discount_amount, is_visible) VALUES (?, ?, ?, ?)',
                                (name, description, discount_value, is_visible))
        
        bundle_id = cursor.lastrowid
        
        # Add products to bundle
        for product_id in product_ids:
            conn.execute('INSERT INTO bundle_products (bundle_id, product_id) VALUES (?, ?)',
                        (bundle_id, int(product_id)))
        
        conn.commit()
        conn.close()
        flash(f'Bundle "{name}" created successfully', 'success')
        return redirect(url_for('admin_bundles'))
        
    except Exception as e:
        flash(f'Error creating bundle: {str(e)}', 'error')
        return redirect(url_for('add_bundle'))

@app.route('/admin/toggle_product_visibility/<int:product_id>', methods=['POST'])
@admin_required
def toggle_product_visibility(product_id):
    """Toggle product visibility"""
    try:
        conn = get_db()
        current_visibility = conn.execute('SELECT is_visible FROM products WHERE id = ?', (product_id,)).fetchone()
        
        if current_visibility:
            new_visibility = not current_visibility[0]
            conn.execute('UPDATE products SET is_visible = ? WHERE id = ?', (new_visibility, product_id))
            conn.commit()
            conn.close()
            
            status = "visible" if new_visibility else "hidden"
            return jsonify({'success': True, 'status': status, 'is_visible': new_visibility})
        else:
            return jsonify({'success': False, 'message': 'Product not found'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/download/<token>')
def secure_download(token):
    """Secure download route using tokens"""
    from datetime import datetime
    
    conn = get_db()
    
    # Get token info
    token_info = conn.execute('''
        SELECT dt.*, o.buyer_name, o.email, p.name as product_name
        FROM download_tokens dt
        JOIN orders o ON dt.order_id = o.id
        JOIN products p ON dt.product_id = p.id
        WHERE dt.token = ?
    ''', (token,)).fetchone()
    
    if not token_info:
        conn.close()
        return render_template_string('''
        <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">❌ Invalid Download Link</h2>
            <p>This download link is not valid or has been removed.</p>
            <p><a href="/" style="color: #007bff;">← Back to Store</a></p>
        </div>
        '''), 404
    
    # Check if token is expired
    expires_at = datetime.strptime(token_info['expires_at'], '%Y-%m-%d %H:%M:%S')
    if datetime.now() > expires_at:
        conn.close()
        return render_template_string('''
        <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">⏰ Download Link Expired</h2>
            <p>This download link has expired (48 hours limit).</p>
            <p>Please contact support for a new download link.</p>
            <p><a href="/" style="color: #007bff;">← Back to Store</a></p>
        </div>
        '''), 410
    
    # Check download limit
    if token_info['download_count'] >= token_info['max_downloads']:
        conn.close()
        return render_template_string('''
        <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">📥 Download Limit Reached</h2>
            <p>This download link has reached its maximum usage limit.</p>
            <p>Please contact support if you need additional downloads.</p>
            <p><a href="/" style="color: #007bff;">← Back to Store</a></p>
        </div>
        '''), 429
    
    # Check if file exists
    if not os.path.exists(token_info['file_path']):
        conn.close()
        return render_template_string('''
        <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">📁 File Not Found</h2>
            <p>The requested file is no longer available.</p>
            <p>Please contact support for assistance.</p>
            <p><a href="/" style="color: #007bff;">← Back to Store</a></p>
        </div>
        '''), 404
    
    # Update download count
    new_count = token_info['download_count'] + 1
    conn.execute('''UPDATE download_tokens 
                   SET download_count = ?, used_at = CURRENT_TIMESTAMP 
                   WHERE token = ?''', (new_count, token))
    conn.commit()
    conn.close()
    
    # Log the download
    print(f"📥 Secure download: {token_info['buyer_name']} downloading {token_info['product_name']} (#{new_count}/{token_info['max_downloads']})")
    
    # Serve the file
    try:
        original_filename = os.path.basename(token_info['file_path'])
        download_name = f"{token_info['product_name']}_{original_filename}"
        
        return send_file(
            token_info['file_path'], 
            as_attachment=True, 
            download_name=download_name,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        print(f"❌ Error serving download: {e}")
        return render_template_string('''
        <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">⚠️ Download Error</h2>
            <p>There was an error processing your download.</p>
            <p>Please contact support for assistance.</p>
            <p><a href="/" style="color: #007bff;">← Back to Store</a></p>
        </div>
        '''), 500

@app.route('/admin/download_product/<int:order_id>')
@admin_required
def download_product_file(order_id):
    """Download product file for confirmed order (admin only)"""
    conn = get_db()
    order = conn.execute('''SELECT o.*, p.name as product_name, p.type, p.file_or_key_path 
                           FROM orders o 
                           JOIN products p ON o.product_id = p.id 
                           WHERE o.id = ? AND o.status = "confirmed" AND p.type = "file"''', (order_id,)).fetchone()
    conn.close()
    
    if not order:
        flash('Order not found or not confirmed', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if not order['file_or_key_path'] or not os.path.exists(order['file_or_key_path']):
        flash('Product file not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    # Get original filename
    original_filename = os.path.basename(order['file_or_key_path'])
    download_name = f"{order['product_name']}_{original_filename}"
    
    return send_file(order['file_or_key_path'], as_attachment=True, download_name=download_name)

if __name__ == '__main__':
    try:
        # Initialize database on startup
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️ Database initialization warning: {e}")
        # Continue anyway - database might already exist
    
    # Get port from environment variable (for Render) or default to 5000
    port = int(os.environ.get('PORT', 5000))
    
    # Run the app
    app.run(debug=False, host='0.0.0.0', port=port)