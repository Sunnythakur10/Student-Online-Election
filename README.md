# Student Online Election System

A secure Django-based online voting platform for student elections with role-based access control, email authentication, and real-time results.

## 🎯 Features

### Core Functionality
- **Three User Roles**: Voters, Candidates, and Admins
- **Secure Email Login**: Passwordless authentication with signed, expiring tokens
- **Time-Bound Elections**: Scheduled voting periods with automatic status checking
- **One Vote Per Election**: Database-enforced single-vote constraint
- **Real-Time Results**: Vote counting with percentage breakdowns and turnout statistics
- **Admin Management**: Full election and candidate management interface

### Security Features
- **Signed URL Tokens**: Cryptographically signed login links prevent tampering
- **Single-Use Enforcement**: Login tokens can only be used once
- **Time-Based Expiry**: Tokens expire after 15 minutes
- **Stateless Authentication**: No session dependency, works across devices
- **Role-Based Access Control**: Custom decorators enforce permissions
- **CSRF Protection**: Django middleware enabled

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Virtual environment (`.venv` included)
- SQLite (included with Python)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Suhanikhanna26/Student-Online-Election-.git
   cd Student-Online-Election-
   ```

2. **Activate virtual environment:**
   ```bash
   # Windows
   .venv\Scripts\activate
   
   # Linux/Mac
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install django djangorestframework django-cors-headers
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create sample data (optional):**
   ```bash
   python manage.py create_sample_data
   ```

6. **Run the development server:**
   ```bash
   python manage.py runserver 127.0.0.1:8000
   ```

7. **Access the application:**
   - Main site: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## 📚 Documentation

- **[Implementation Complete](IMPLEMENTATION_COMPLETE.md)** - Latest features and status
- **[Email Login Implementation](EMAIL_LOGIN_IMPLEMENTATION.md)** - Detailed token system documentation
- **[Quick Reference Guide](TOKEN_SYSTEM_QUICK_REFERENCE.md)** - Developer quick reference

## 🏗️ Project Structure

```
Student-Online-Election-/
├── voting/                      # Main application
│   ├── models.py               # Database models (User, Election, Vote, LoginToken)
│   ├── views.py                # View functions and business logic
│   ├── urls.py                 # URL routing
│   ├── admin.py                # Django admin configuration
│   ├── forms.py                # Form classes
│   ├── signals.py              # Signal handlers for profile creation
│   ├── templates/voting/       # HTML templates
│   └── management/commands/    # Custom management commands
│       ├── create_sample_data.py
│       └── cleanup_login_tokens.py
├── voting_system/              # Project settings
│   ├── settings.py             # Django configuration
│   ├── urls.py                 # Root URL configuration
│   └── wsgi.py                 # WSGI configuration
├── db.sqlite3                  # SQLite database
└── manage.py                   # Django management script
```

## 🗃️ Database Models

### CustomUser
Extended Django user model with:
- Role (voter/candidate/admin)
- Branch (CSE, ECE, ME, CE, EE)
- Year of study (1-4)
- Email as username field

### VoterProfile
- Linked to CustomUser
- Tracks voting status
- Email verification status

### CandidateProfile
- Linked to CustomUser
- Campaign manifesto
- Campaign slogan
- Vote count (denormalized)

### Election
- Name, start/end dates
- Active status
- Methods for checking voting window

### Vote
- Links voter, candidate, and election
- Unique constraint: one vote per (voter, election)
- Auto-updates candidate vote counts

### LoginToken (NEW)
- Secure email login tokens
- Expiry enforcement (15 min default)
- Single-use flag
- Cryptographically signed

## 👤 User Roles

### Voters
- Register with email, branch, and year
- Receive passwordless login links via email
- Vote in active elections
- View results after election ends

### Candidates
- Promoted by admins from eligible voters (3rd/4th year)
- Edit campaign manifesto and slogan
- View personal vote counts in real-time
- Access candidate dashboard

### Admins
- Create and manage elections
- Promote voters to candidates
- Activate/deactivate elections (only one active at a time)
- View results anytime
- Manage users via Django admin

## 🔑 Email Login System

The system uses a **secure, stateless token-based email login**:

1. User enters email on login page
2. System generates cryptographically secure token
3. Token signed with Django's Signer (prevents tampering)
4. Email sent with signed token URL
5. Token valid for 15 minutes
6. Token can only be used once
7. After successful login, token marked as used

### Benefits:
- No password to remember
- Works across devices (no session dependency)
- Secure against tampering
- Automatic expiry
- Single-use enforcement

### Management:
```bash
# Clean up old tokens
python manage.py cleanup_login_tokens

# Preview cleanup
python manage.py cleanup_login_tokens --dry-run

# Custom retention period
python manage.py cleanup_login_tokens --days 30
```

## 🗳️ Election Management

### Creating Elections
1. Admin logs in
2. Navigate to "Manage Elections"
3. Create new election with:
   - Name
   - Start date/time
   - End date/time
4. System automatically deactivates other elections
5. Voting opens when current time is within start/end window

### Election Status
- **Active**: Marked as active by admin
- **Open for Voting**: Active AND current time within start/end dates
- **Ended**: Current time past end date

## 📊 Results System

### Access Control:
- **Admins**: View results anytime
- **Others**: View results only after election ends

### Displayed Information:
- Vote count per candidate
- Percentage distribution
- Total votes cast
- Total eligible voters
- Voter turnout percentage
- Results sorted by vote count (descending)

## 🛠️ Management Commands

### Create Sample Data
```bash
python manage.py create_sample_data
```
Creates:
- Admin user: `admin@example.com` / `admin123`
- Sample voters (3 users)
- Sample candidates (3 users)
- Sample election

### Clean Up Login Tokens
```bash
python manage.py cleanup_login_tokens [--days N] [--dry-run]
```
Removes expired and used tokens older than N days (default: 7)

## 🔧 Configuration

### Email Settings
For development (console backend):
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

For production (SMTP):
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
```

### Secret Key
**Important for production:**
```python
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'dev-key-change-in-production')
```

## 🧪 Testing

Run comprehensive tests:
```bash
python manage.py test
```

Test email login system:
```python
from voting.models import LoginToken
token = LoginToken.create_token(user, expiry_minutes=15)
assert token.is_valid() == True
```

## 📝 API Endpoints

Current endpoints (server-rendered HTML):
- `/` - Login page
- `/register/` - Registration
- `/send-verification/` - Request email login link
- `/verify-login/` - Verify token and login
- `/dashboard/` - User dashboard (role-aware)
- `/vote/` - Voting page (voters only)
- `/submit-vote/` - Submit vote
- `/results/` - Election results
- `/candidate/dashboard/` - Candidate dashboard
- `/candidate/profile/` - Edit candidate profile
- `/admin-panel/` - Admin user management
- `/manage-elections/` - Admin election management

## 🚀 Production Deployment

### Checklist:
- [ ] Set `SECRET_KEY` from environment variable
- [ ] Configure production email backend (SMTP)
- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up static files serving
- [ ] Set up database backup
- [ ] Schedule daily token cleanup (cron/task scheduler)
- [ ] Configure HTTPS/SSL
- [ ] Set up monitoring

### Recommended Cron Job:
```bash
# Clean up tokens daily at 3 AM
0 3 * * * /path/to/venv/bin/python /path/to/manage.py cleanup_login_tokens
```

## 🐛 Troubleshooting

### Common Issues:

**"No active elections"**
- Check election dates are in the past (start) and future (end)
- Verify election is marked as active

**"Invalid login link"**
- Token may have expired (15 min limit)
- Token may have been used already
- Request new login link

**Email not sending**
- Check email backend configuration
- In development, emails print to console

**Missing VoterProfile**
- Signals should auto-create profiles
- Manually create via Django admin if needed

## 📊 Database Schema

Key relationships:
```
CustomUser (1) → (1) VoterProfile
CustomUser (1) → (1) CandidateProfile
CustomUser (1) → (N) LoginToken

Election (1) → (N) Vote
VoterProfile (1) → (N) Vote
CandidateProfile (1) → (N) Vote
```

Constraints:
- Unique: (voter, election) on Vote table
- Unique: token on LoginToken table
- Unique: email on CustomUser

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📜 License

This project is open source and available under the MIT License.

## 👥 Authors

- **Suhani Khanna** - [GitHub](https://github.com/Suhanikhanna26)

## 🙏 Acknowledgments

- Django framework
- Django REST Framework
- django-cors-headers

## 📞 Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/Suhanikhanna26/Student-Online-Election-/issues)
- Documentation: See docs folder for detailed guides

## 🔄 Recent Updates

### Latest (October 2025)
- ✅ Implemented secure email login with signed tokens
- ✅ Added token expiry and single-use enforcement
- ✅ Created token cleanup management command
- ✅ Added comprehensive admin interface for token management
- ✅ Removed session dependency (stateless authentication)

See [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) for full details.

---

**Status:** ✅ Production Ready  
**Version:** 2.0  
**Last Updated:** October 31, 2025
