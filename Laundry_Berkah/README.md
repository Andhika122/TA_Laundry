# 🧺 Laundry Berkah - Laundry Management System

Modern Laundry Management System built with Flask, SQLAlchemy, and Bootstrap 5.

## 📋 Prasyarat

- Python 3.8+
- MySQL/TiDB Database
- pip (Python Package Manager)

## 🚀 Setup & Installation

### 1. Clone Repository
```bash
cd c:\Users\krist\OneDrive\Documents\Tugas Kampus\Tugas PA\laundry\Laundry_Berkah
```

### 2. Create Virtual Environment
```bash
python -m venv venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Setup Environment Variables
The `.env` file is already configured with:
- TiDB Database credentials
- Cloudinary API keys
- Resend Email API
- Admin credentials

### 6. Initialize Database
```bash
flask init-db
```

### 7. Run Development Server
```bash
python app.py
```

### 8. Run Automated Tests
```bash
run_tests.cmd
```

The application will start at `http://localhost:5000`

## 🔐 Login Credentials

```
Username: admin
Password: admin
```

## 📁 Project Structure

```
Laundry_Berkah/
├── app/
│   ├── auth/              # Authentication module
│   ├── dashboard/         # Dashboard module
│   ├── pelanggan/         # Customer management
│   ├── transaksi/         # Transaction module
│   ├── laundry/           # Laundry process workflow
│   ├── layanan/           # Service/Package management
│   ├── laporan/           # Reporting module
│   ├── akun/              # Account management
│   ├── api/               # REST API endpoints
│   ├── models/            # SQLAlchemy models
│   ├── utils/             # Utility functions
│   ├── static/            # CSS, JS, Images
│   └── templates/         # HTML templates
├── database/              # Database scripts
├── instance/              # Instance-specific config
├── config.py              # Flask configuration
├── app.py                 # Application entry point
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
└── README.md              # This file
```

## 🗄️ Database Schema

### Tables
- `role` - User roles (Admin, Kasir, Operator)
- `user` - User accounts
- `pelanggan` - Customer data
- `layanan` - Services/Packages
- `transaksi` - Transactions
- `detail_transaksi` - Transaction items
- `pembayaran` - Payment records
- `status` - Status history
- `parfum` - Fragrance options
- `promo` - Promotions

## 🔄 Application Workflow

### Transaction Status Workflow
```
Antrian → Cuci → Pengeringan → Setrika → Packing → Siap Ambil → Selesai
```

### Core Modules

#### 🔐 Auth Module
- User login/logout
- Session management
- Password hashing with Werkzeug

#### 📊 Dashboard
- Real-time statistics
- Transaction overview
- Revenue tracking

#### 👥 Pelanggan (Customer)
- CRUD operations
- Customer search
- Transaction history
- Customer details

#### 💼 Transaksi (Transaction)
- Create new transactions
- Select services
- Add fragrance options
- Apply promotions
- Calculate totals

#### 👔 Laundry Process
- Queue management (Antrian)
- Washing (Cuci)
- Drying (Pengeringan)
- Ironing (Setrika)
- Packing (Packing)
- Ready for pickup (Siap Ambil)
- Completed (Selesai)

#### 💰 Pembayaran (Payment)
- Payment methods (Cash, Transfer, QRIS)
- Change calculation
- Payment status tracking

#### 📋 Laporan (Reports)
- Daily reports
- Monthly reports
- Revenue analysis
- Customer analytics
- PDF export

#### ⚙️ Settings/Account
- User profile management
- Password change
- Employee management
- Role management

## 🛠️ Technology Stack

- **Backend:** Flask 3.0.0
- **Database:** SQLAlchemy 2.0.23 + TiDB MySQL
- **Frontend:** Bootstrap 5.3.0 + Vanilla JavaScript
- **Authentication:** Werkzeug Security
- **File Upload:** Cloudinary
- **Email:** Resend API

## 🔧 Configuration

### Environment Variables (.env)

```env
SECRET_KEY=your-secret-key
FLASK_ENV=development

# TiDB Database
TIDB_HOST=gateway01.ap-southeast-1.prod.aws.tidbcloud.com
TIDB_PORT=4000
TIDB_USER=your-username
TIDB_PASSWORD=your-password
TIDB_DB=db_laundry
TIDB_SSL_CA=/path/to/ca.pem

# Cloudinary
CLOUDINARY_CLOUD_NAME=xxx
CLOUDINARY_API_KEY=xxx
CLOUDINARY_API_SECRET=xxx

# Resend Email
RESEND_API_KEY=xxx
RESEND_FROM_EMAIL=xxx@resend.dev
CONTACT_RECIPIENT_EMAIL=xxx@email.com

# Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
```

## 📚 API Endpoints

### Auth
- `POST /auth/login` - Login
- `GET /auth/logout` - Logout

### Dashboard
- `GET /dashboard/` - Dashboard

### Pelanggan
- `GET /pelanggan/` - List customers
- `POST /pelanggan/tambah` - Add customer
- `GET /pelanggan/<id>/edit` - Edit customer
- `DELETE /pelanggan/<id>` - Delete customer

### Transaksi
- `GET /transaksi/` - List transactions
- `POST /transaksi/baru` - Create transaction
- `GET /transaksi/<id>` - Transaction detail

### Laundry
- `GET /laundry/antrian` - Queue
- `GET /laundry/cuci` - Washing
- `GET /laundry/pengeringan` - Drying
- `GET /laundry/setrika` - Ironing

### Laporan
- `GET /laporan/` - Reports

### Akun
- `GET /akun/profile` - User profile

### API
- `GET /api/status` - API status

## 🧪 Testing

Run tests with pytest:
```bash
pytest
```

## 📝 Coding Standards

- PEP 8 compliant Python code
- Consistent naming conventions
- Comprehensive comments
- Clean architecture with separation of concerns
- Blueprint-based modular structure

## 🤝 Contributing

Maintain clean code and follow the established patterns.

## 📄 License

This project is part of a campus assignment (Tugas PA).

## 🆘 Troubleshooting

### Database Connection Error
- Verify TiDB credentials in `.env`
- Check SSL CA certificate path
- Ensure database exists

### Module Not Found Error
- Activate virtual environment
- Install requirements: `pip install -r requirements.txt`
- Check Python path configuration

### Port Already in Use
- Change port in `app.py` from 5000 to another port

## 📞 Support

For issues or questions, contact the development team.

---

**Status:** Tahap 1 - Konfigurasi Flask ✓  
**Next:** Tahap 2 - Login & Dashboard Implementation
