# 🛍️ Digital Products Store - Algerian Payment System

A comprehensive Flask web application for selling digital products (software keys, digital files, accounts) with integrated Algerian payment methods (Baridimob and CCP), Telegram bot automation, and user account management.

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![Flask](https://img.shields.io/badge/flask-v2.0+-green.svg)
![Bootstrap](https://img.shields.io/badge/bootstrap-v5.3-purple.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ✨ Features

### 🛒 **Customer Experience**
- **Modern Storefront**: Clean, professional Bootstrap 5 design
- **Smart Search**: Fuzzy search with typo tolerance
- **User Accounts**: Registration, login, order tracking
- **Product Categories**: Organized browsing with tags and categories
- **Secure Checkout**: Payment proof upload with validation
- **Instant Delivery**: Products delivered via Telegram/Email
- **Professional Receipts**: Automatic PDF receipt generation

### 🔧 **Admin Management**
- **Complete Dashboard**: Sales analytics, order management
- **Telegram Integration**: One-click order confirmation via bot
- **Advanced Product Management**: Categories, tags, bundles, stock tracking
- **Individual Key Management**: Add/remove license keys individually
- **File Product Support**: Upload and manage digital files
- **Professional Analytics**: Charts, revenue tracking, customer insights
- **CSV Export**: Complete sales data export

### 📱 **Telegram Bot Features**
- **Admin Notifications**: Instant order alerts with payment proof images
- **One-Click Actions**: ✅ Confirm / ❌ Reject buttons in Telegram
- **Customer Delivery**: Automatic product delivery to buyers
- **Bot Commands**: `/start`, `/chatid` for customer setup

### 📧 **Email System**
- **Professional Templates**: Branded emails with HTML formatting
- **Order Confirmations**: Automatic email notifications
- **Product Delivery**: Keys/download links sent via email
- **Receipt Attachments**: PDF receipts attached to confirmation emails

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Telegram Bot Token
- Email service (Resend.com recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/digital-store.git
   cd digital-store
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the store**
   - Store: http://localhost:5000
   - Admin: http://localhost:5000/admin (admin/admin123)

## ⚙️ Configuration

### Environment Variables (.env)
```env
# Flask Configuration
SECRET_KEY=your-secret-key-change-this-in-production
STORE_NAME=Your Store Name
BASE_URL=http://localhost:5000

# Telegram Bot
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_ADMIN_ID=your-telegram-user-id

# Email Configuration (Resend.com)
RESEND_API_KEY=your-resend-api-key
MAIL_FROM=noreply@yourdomain.com
MAIL_NAME=Your Store Name

# Payment Configuration
BARIDIMOB_NUMBER=your-baridimob-number
CCP_ACCOUNT=your-ccp-account
CCP_KEY=your-ccp-key

# Contact Information
CONTACT_EMAIL=support@yourdomain.com
TELEGRAM_LINK=https://t.me/YourBot
```

### Telegram Bot Setup

1. **Create a bot with @BotFather**
   ```
   /newbot
   Choose a name: Your Store Bot
   Choose a username: YourStoreBot
   ```

2. **Get your Telegram User ID**
   - Message @userinfobot to get your user ID
   - Add it to `TELEGRAM_ADMIN_ID` in .env

3. **Set webhook (for production)**
   ```bash
   curl -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://yourdomain.com/webhook/telegram"}'
   ```

## 📊 Product Types Supported

### 🔑 **License Keys**
- Individual key management
- Automatic assignment (one key per customer)
- Stock tracking with real-time updates
- Usage tracking and audit trail

### 📁 **Digital Files**
- Secure file upload and storage
- Automatic download link generation
- Time-limited access (48 hours, 3 downloads)
- File replacement and version management

### 📦 **Product Bundles**
- Multi-product combinations
- Percentage or fixed amount discounts
- Bundle-specific imagery
- Automatic savings calculation

## 🎨 User Interface

### **Modern Design**
- Bootstrap 5 responsive framework
- Clean, professional appearance
- Mobile-first design approach
- Consistent branding throughout

### **Advanced Features**
- Smart search with typo tolerance
- Category and tag filtering
- Real-time stock indicators
- Professional checkout flow

## 🔒 Security Features

- **Password Security**: Werkzeug password hashing
- **Session Management**: Secure Flask sessions
- **Input Validation**: Server-side validation
- **SQL Injection Protection**: Parameterized queries
- **File Upload Security**: Type and size validation
- **Download Security**: Time-limited tokens

## 📱 Mobile Experience

- Fully responsive design
- Touch-friendly interface
- Mobile-optimized forms
- Fast loading performance

## 🛠️ Tech Stack

- **Backend**: Flask (Python)
- **Database**: SQLite
- **Frontend**: Bootstrap 5, JavaScript
- **Email**: Resend.com API
- **Bot**: Telegram Bot API
- **PDF**: ReportLab
- **Search**: RapidFuzz

## 📁 Project Structure

```
digital-store/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── my_orders.html
│   └── admin/
├── static/               # Static files (CSS, JS, images)
├── uploads/              # Payment proof uploads (gitignored)
├── products/             # Digital product files (gitignored)
├── receipts/             # Generated receipts (gitignored)
└── docs/                 # Documentation files
```

## 🔄 Order Workflow

### Customer Journey
1. **Browse** → Smart search, categories, featured items
2. **Select** → View details, check stock availability
3. **Register/Login** → Create account or continue as guest
4. **Purchase** → Fill form, upload payment proof
5. **Payment** → Follow Baridimob/CCP instructions
6. **Confirmation** → Admin verifies and confirms
7. **Delivery** → Instant product delivery via Telegram/Email
8. **Receipt** → Professional PDF receipt generated

### Admin Workflow
1. **Notification** → Telegram alert with payment proof image
2. **Review** → Check payment details and proof
3. **Action** → ✅ Confirm or ❌ Reject via Telegram
4. **Automation** → Product delivery and receipt generation
5. **Analytics** → Track performance and revenue

## 📈 Analytics & Reporting

- Real-time dashboard with key metrics
- Interactive charts (Chart.js)
- Customer behavior analysis
- Product performance tracking
- Revenue analytics
- CSV data export

## 🌟 Advanced Features

- **Smart Search**: Typo-tolerant product search
- **User Accounts**: Registration and order tracking
- **Bundle System**: Product combinations with discounts
- **Category Management**: Organized product browsing
- **Tag System**: Flexible product labeling
- **Stock Management**: Real-time inventory tracking
- **Professional Receipts**: Branded PDF generation
- **Contact System**: Customer support integration

## 🚀 Deployment

### Production Deployment
1. Use a production WSGI server (Gunicorn)
2. Set up reverse proxy (Nginx)
3. Configure HTTPS with SSL certificates
4. Set up proper file permissions
5. Use environment variables for sensitive data
6. Configure database backups
7. Set up monitoring and logging

### Docker Deployment (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` folder for detailed guides
- **Issues**: Report bugs via GitHub Issues
- **Email**: Contact support@yourdomain.com
- **Telegram**: Join our support channel

## 🎯 Roadmap

- [ ] Multi-language support
- [ ] Advanced analytics dashboard
- [ ] Customer loyalty program
- [ ] API for third-party integrations
- [ ] Mobile app (React Native)
- [ ] Advanced inventory management
- [ ] Multi-vendor support

## ⭐ Acknowledgments

- Bootstrap team for the amazing CSS framework
- Flask community for the excellent web framework
- Telegram for the powerful Bot API
- All contributors and users of this project

---

**Made with ❤️ for the Algerian digital marketplace**

*This project aims to provide a complete, professional solution for selling digital products in Algeria with local payment method integration.*