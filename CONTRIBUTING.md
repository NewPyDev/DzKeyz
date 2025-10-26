# Contributing to DZKeyz

Thank you for your interest in contributing to DZKeyz! This document provides guidelines and information for contributors.

## 🤝 How to Contribute

### Reporting Issues
- Use the [GitHub Issues](https://github.com/NewPyDev/DzKeyz/issues) page
- Search existing issues before creating a new one
- Provide detailed information including:
  - Steps to reproduce
  - Expected vs actual behavior
  - Environment details (OS, Python version, etc.)
  - Screenshots if applicable

### Suggesting Features
- Open a [GitHub Discussion](https://github.com/NewPyDev/DzKeyz/discussions) for feature requests
- Explain the use case and benefits
- Consider implementation complexity
- Be open to feedback and discussion

### Code Contributions

#### Getting Started
1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature/fix
4. Make your changes
5. Test thoroughly
6. Submit a pull request

#### Development Setup
```bash
# Clone your fork
git clone https://github.com/yourusername/DzKeyz.git
cd DzKeyz

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your settings

# Run the application
python app.py
```

#### Code Style Guidelines
- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and small
- Use type hints where appropriate

#### Frontend Guidelines
- Use Bootstrap 5.3 classes consistently
- Ensure mobile responsiveness
- Follow existing design patterns
- Test on multiple screen sizes
- Use semantic HTML elements

#### Database Changes
- Always provide migration scripts
- Test with existing data
- Document schema changes
- Consider backward compatibility

## 🧪 Testing

### Manual Testing
- Test all user flows (registration, login, purchase, etc.)
- Verify admin functionality
- Check email sending
- Test on different devices and browsers

### Automated Testing
- Write unit tests for new functions
- Test edge cases and error conditions
- Ensure tests pass before submitting PR

## 📝 Pull Request Process

1. **Branch Naming**
   - `feature/description` for new features
   - `fix/description` for bug fixes
   - `docs/description` for documentation

2. **Commit Messages**
   - Use clear, descriptive messages
   - Start with a verb (Add, Fix, Update, etc.)
   - Keep first line under 50 characters
   - Add detailed description if needed

3. **Pull Request Description**
   - Explain what changes were made
   - Reference related issues
   - Include screenshots for UI changes
   - List any breaking changes

4. **Review Process**
   - All PRs require review
   - Address feedback promptly
   - Keep discussions respectful
   - Be open to suggestions

## 🏗️ Architecture Guidelines

### File Structure
```
DzKeyz/
├── app.py              # Main application file
├── templates/          # HTML templates
├── static/            # CSS, JS, images
├── uploads/           # User uploaded files
├── products/          # Product files
├── receipts/          # Generated receipts
└── requirements.txt   # Python dependencies
```

### Adding New Features

#### Database Changes
1. Add table creation in `init_db()` function
2. Handle existing databases with ALTER TABLE
3. Update relevant queries throughout the app

#### New Routes
1. Add route function with proper decorators
2. Handle both GET and POST methods
3. Include error handling and logging
4. Add corresponding templates

#### Templates
1. Extend appropriate base template
2. Use consistent Bootstrap classes
3. Include proper meta tags
4. Ensure accessibility compliance

#### JavaScript
1. Use vanilla JavaScript (no jQuery)
2. Handle errors gracefully
3. Provide user feedback
4. Follow existing patterns

## 🔒 Security Considerations

- Never commit sensitive data (API keys, passwords)
- Validate all user inputs
- Use parameterized queries for database
- Implement proper authentication checks
- Follow OWASP security guidelines

## 📚 Documentation

- Update README.md for new features
- Add inline comments for complex code
- Update configuration examples
- Include usage examples

## 🎯 Priority Areas

We especially welcome contributions in these areas:

### High Priority
- Bug fixes and security improvements
- Performance optimizations
- Mobile responsiveness improvements
- Accessibility enhancements

### Medium Priority
- New payment method integrations
- Additional language support
- Enhanced admin features
- API development

### Low Priority
- UI/UX improvements
- Additional themes
- Third-party integrations
- Advanced analytics

## 🌍 Community

- Be respectful and inclusive
- Help other contributors
- Share knowledge and experience
- Follow the code of conduct

## 📞 Getting Help

- **Questions**: Use [GitHub Discussions](https://github.com/NewPyDev/DzKeyz/discussions)
- **Issues**: Use [GitHub Issues](https://github.com/NewPyDev/DzKeyz/issues)
- **Chat**: Join our community channels

## 🏆 Recognition

Contributors will be:
- Listed in the README.md
- Mentioned in release notes
- Invited to join the core team (for significant contributions)

Thank you for helping make DZKeyz better! 🚀