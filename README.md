# 🏢 AMBP - Asset Management Business Platform

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?style=for-the-badge&logo=postgresql)
![Google Sheets](https://img.shields.io/badge/Google_Sheets-API-green?style=for-the-badge&logo=googlesheets)

**Modern Asset Management System with Real-time Sync & Mobile-First Design**

[🚀 Live Demo](https://your-app.onrender.com) • [📖 Documentation](#documentation) • [🐛 Report Bug](https://github.com/yourusername/ambp/issues)

</div>

---

## ✨ Features

### 🎯 **Core Functionality**
- 📊 **Real-time Dashboard** - Interactive charts and analytics
- 📱 **Mobile-First Design** - PWA ready with offline support
- 🔄 **Google Sheets Sync** - Bidirectional data synchronization
- 🏷️ **Smart Asset Tagging** - Auto-generated asset codes
- 📍 **Asset Relocation** - Track movement with full audit trail
- 🔍 **Advanced Search** - Multi-field intelligent search

### 🛡️ **Security & Access**
- 👥 **Role-Based Access** - Admin/User permissions
- 🔐 **Session Management** - Secure authentication
- 📝 **Audit Logging** - Complete activity tracking
- 🔒 **Data Protection** - Environment-based secrets

### 📈 **Analytics & Reporting**
- 📊 **Financial Tracking** - Depreciation & book values
- 📅 **Purchase History** - 5-year trend analysis
- 🏢 **Multi-location Support** - Company-wide asset tracking
- 📤 **Export Capabilities** - Excel/CSV data export

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Google Sheets API credentials

### 1️⃣ Clone & Setup
```bash
git clone https://github.com/yourusername/ambp.git
cd ambp
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2️⃣ Environment Configuration
```bash
cp .env.example .env
# Edit .env with your credentials
```

Required environment variables:
```env
DATABASE_URL=postgresql://user:password@localhost/ambp
GOOGLE_CREDS_JSON={"type": "service_account", ...}
GOOGLE_SHEET_ID=your_sheet_id_here
SECRET_KEY=your_secret_key_here
```

### 3️⃣ Database Setup
```bash
# Initialize database
python -c "from app.database.database import init_db; init_db()"

# Create admin user
python -c "from app.routes.setup_admin import create_admin; create_admin()"
```

### 4️⃣ Run Application
```bash
uvicorn app.main:app --reload
```

Visit `http://localhost:8000` 🎉

---

## 📱 Mobile App (PWA)

### Install as App
1. Open in Chrome/Safari on mobile
2. Tap "Add to Home Screen"
3. Enjoy native app experience!

### Features
- 📷 **Camera Integration** - Barcode scanning (planned)
- 🔄 **Offline Support** - Works without internet
- 📱 **Native Feel** - Full-screen, splash screen
- 🔔 **Push Notifications** - Real-time updates

---

## 🏗️ Architecture

```
📁 app/
├── 🚀 main.py              # FastAPI application
├── ⚙️ config.py            # Configuration settings
├── 🔧 init.py              # App initialization
├── 📊 database/            # Database layer
│   ├── database.py         # PostgreSQL connection
│   ├── dependencies.py     # Auth dependencies
│   └── base.py            # SQLAlchemy base
├── 🛣️ routes/              # API endpoints
│   ├── auth.py            # Authentication
│   ├── assets.py          # Asset management
│   ├── relocation.py      # Asset movement
│   └── user.py            # User management
├── 🎨 templates/           # Jinja2 templates
├── 🔧 utils/               # Utilities
│   ├── models.py          # Database models
│   ├── sheets.py          # Google Sheets API
│   ├── auth.py            # Authentication logic
│   └── flash.py           # Flash messages
└── 📁 static/              # CSS, JS, images
```

---

## 🔧 Configuration

### Google Sheets Setup
1. Create Google Cloud Project
2. Enable Sheets API
3. Create Service Account
4. Share sheet with service account email
5. Add credentials to environment

### Database Schema
- **Users** - Authentication & roles
- **Assets** - Complete asset information
- **Log_Relocation** - Movement tracking
- **Log_Status** - Status change history

---

## 🚀 Deployment

### Render.com (Recommended)
```bash
# Build Command
pip install -r requirements.txt

# Start Command
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables
Set these in your deployment platform:
- `DATABASE_URL`
- `GOOGLE_CREDS_JSON`
- `GOOGLE_SHEET_ID`
- `SECRET_KEY`

---

## 📊 API Documentation

### Authentication
```http
POST /login
Content-Type: application/x-www-form-urlencoded

username=admin&password=password
```

### Assets
```http
GET /assets?status=Active&search=laptop
GET /assets/{id}/detail
POST /assets/{id}/status
DELETE /assets/{id}/delete
```

### Relocation
```http
POST /relocate/search
POST /relocate/move
GET /relocate/logs
```

---

## 🤝 Contributing

1. **Fork** the repository
2. **Create** feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** changes (`git commit -m 'Add amazing feature'`)
4. **Push** to branch (`git push origin feature/amazing-feature`)
5. **Open** Pull Request

### Development Setup
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Code formatting
black app/
isort app/

# Linting
flake8 app/
```

---

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Reliable database system
- **Google Sheets API** - Seamless data integration
- **Render.com** - Easy deployment platform

---

<div align="center">

**Made with ❤️ for efficient asset management**

[⭐ Star this repo](https://github.com/yourusername/ambp) • [🐛 Report issues](https://github.com/yourusername/ambp/issues) • [💬 Discussions](https://github.com/yourusername/ambp/discussions)

</div>