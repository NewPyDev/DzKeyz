# 🔑 DZKeyz - Premium Digital Store Platform

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A modern, feature-rich digital marketplace built with Flask for selling digital products, game keys, software licenses, and digital downloads. Designed for entrepreneurs and businesses looking to create a professional online store with advanced customization and automation features.

## ✨ Features Overview

### 🛍️ **Core E-commerce**
- **Product Management** - Digital keys, file downloads, and bundles
- **Secure Checkout** - Multiple payment methods (BaridiMob, CCP)
- **Order Management** - Complete order lifecycle with receipts
- **User Accounts** - Registration, login, order history
- **Admin Dashboard** - Comprehensive store management

### 🎨 **Advanced Customization**
- **Custom Branding** - Logo, colors, fonts, and themes
- **Landing Pages** - Create promotional campaigns and special offers
- **Responsive Design** - Mobile-first, professional UI
- **Dynamic Theming** - Real-time brand customization

### 🤖 **AI-Powered Features**
- **AI Product Descriptions** - OpenAI integration for professional copywriting
- **Smart Fallbacks** - Template-based descriptions when AI unavailable
- **Context-Aware** - Uses product details for relevant content

### 🔐 **Authentication & Security**
- **Email Verification** - Secure account activation system
- **Social Login** - Google and Discord OAuth 2.0 integration
- **Password Security** - Bcrypt hashing and secure sessions
- **Admin Protection** - Role-based access control

### 📧 **Communication**
- **Email System** - Resend.com integration for transactional emails
- **Professional Templates** - Branded email designs
- **Contact Forms** - Customer support with file attachments
- **Telegram Integration** - Order notifications and support

### 📊 **Management Tools**
- **User Management** - Admin panel for customer accounts
- **Analytics Dashboard** - Sales and performance metrics
- **Inventory Control** - Stock management for digital keys
- **Audit Logging** - Complete order and action history

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SQLite (included)
- Resend.com account (for emails)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/NewPyDev/DzKeyz.git
cd DzKeyz
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your settings
```

4. **Initialize the database**
```bash
python app.py
```

5. **Access your store**
- **Store**: http://localhost:5000
- **Admin**: http://localhost:5000/admin (admin/admin123)

## ⚙️ Configuration

### Required Environment Variables

```env
# Basic Configuration
SECRET_KEY=your-secret-key-here
STORE_NAME=Your Store Name
BASE_URL=https://yourstore.com

# Email Configuration (Resend.com)
RESEND_API_KEY=re_your_api_key
MAIL_FROM=noreply@yourstore.com
MAIL_NAME=Your Store Name

# Payment Configuration
BARIDIMOB_RIP=your_rip_number
CCP_ACCOUNT=your_ccp_account

# Contact Information
CONTACT_EMAIL=support@yourstore.com
TELEGRAM_LINK=https://t.me/yoursupport
TELEGRAM_BOT_TOKEN=your_bot_token

# Social Login (Optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
DISCORD_CLIENT_ID=your_discord_client_id
DISCORD_CLIENT_SECRET=your_discord_client_secret

# AI Features (Optional)
OPENAI_API_KEY=your_openai_api_key
```

## 🎯 Key Features Breakdown

### 🛒 **Product Types**
- **Digital Keys** - Game keys, software licenses with stock management
- **File Downloads** - Digital products with secure download links
- **Bundles** - Multiple products packaged together

### 🎨 **Branding System**
- **Logo Upload** - Custom store branding
- **Color Schemes** - Primary, secondary, background colors
- **Typography** - 6 Google Fonts options
- **Live Preview** - See changes before applying
- **Preset Themes** - Quick professional themes

### 🧭 **Landing Pages**
- **Campaign Pages** - Create `/promo/summer-sale` style pages
- **Product Showcases** - Feature specific products
- **Banner Images** - Professional promotional graphics
- **SEO Friendly** - Custom URLs and meta tags

### 🤖 **AI Integration**
- **Smart Descriptions** - Generate professional product descriptions
- **Context Aware** - Uses product name, category, and tags
- **Fallback System** - Works even without OpenAI API
- **One-Click Generation** - Integrated into product forms

### 🔐 **Social Authentication**
- **Google Login** - OAuth 2.0 integration
- **Discord Login** - Gaming community friendly
- **Auto Account Creation** - No email verification needed
- **Account Linking** - Connect social to existing accounts

### 📧 **Email System**
- **Transactional Emails** - Order confirmations, receipts
- **Account Activation** - Secure email verification
- **Professional Design** - Branded email templates
- **Reliable Delivery** - Resend.com integration

## 🏗️ Architecture

### Technology Stack
- **Backend**: Flask (Python)
- **Database**: SQLite with row factory
- **Frontend**: Bootstrap 5.3, Vanilla JavaScript
- **Email**: Resend.com API
- **Authentication**: Flask-Session, OAuth 2.0
- **AI**: OpenAI GPT-3.5-turbo
- **Payments**: Custom integration (BaridiMob, CCP)

### Database Schema
- **Users** - Customer accounts with social login support
- **Products** - Digital items with categories and tags
- **Orders** - Complete order lifecycle management
- **Landing Pages** - Custom promotional pages
- **Store Settings** - Branding and configuration
- **Audit Logs** - Complete action history

## 📱 Screenshots

### Store Front
- Modern, responsive design
- Product grid with search and filtering
- Professional checkout process
- Mobile-optimized experience

### Admin Dashboard
- Comprehensive management interface
- Real-time analytics and metrics
- User and order management
- Branding customization tools

### Social Features
- One-click social login
- Professional email templates
- Custom landing pages
- AI-generated content

## 🚀 Deployment

### Render.com (Recommended)
1. Fork this repository
2. Connect to Render.com
3. Add environment variables
4. Deploy automatically

### Manual Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=production

# Run with Gunicorn
gunicorn --bind 0.0.0.0:$PORT app:app
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
```bash
# Clone and setup
git clone https://github.com/NewPyDev/DzKeyz.git
cd DzKeyz
pip install -r requirements.txt

# Run in development mode
python app.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/NewPyDev/DzKeyz/wiki)
- **Issues**: [GitHub Issues](https://github.com/NewPyDev/DzKeyz/issues)
- **Discussions**: [GitHub Discussions](https://github.com/NewPyDev/DzKeyz/discussions)
- **Email**: support@dzkeyz.com

## 🌟 Acknowledgments

- **Flask** - The web framework that powers DZKeyz
- **Bootstrap** - For the responsive UI components
- **Resend.com** - Reliable email delivery service
- **OpenAI** - AI-powered content generation
- **Contributors** - Everyone who helped build this platform

## 🔮 Roadmap

- [ ] **Multi-language Support** - Internationalization
- [ ] **Advanced Analytics** - Detailed sales reports
- [ ] **API Integration** - RESTful API for third-party apps
- [ ] **Mobile App** - Native mobile applications
- [ ] **Cryptocurrency Payments** - Bitcoin, Ethereum support
- [ ] **Affiliate System** - Partner and referral programs

---

**Built with ❤️ for digital entrepreneurs worldwide**

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/NewPyDev/DzKeyz?style=social)
![GitHub forks](https://img.shields.io/github/forks/NewPyDev/DzKeyz?style=social)
![GitHub issues](https://img.shields.io/github/issues/NewPyDev/DzKeyz)
![GitHub pull requests](https://img.shields.io/github/issues-pr/NewPyDev/DzKeyz)

**⭐ Star this repository if you find it useful!**