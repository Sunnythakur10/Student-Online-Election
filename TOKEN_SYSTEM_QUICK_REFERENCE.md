# Email Login Token System - Quick Reference

## For Other AI Agents / Developers

### What Was Changed
Session-based email login replaced with **signed, expiring, single-use database tokens**.

---

## Core Components

### 1. LoginToken Model (`voting/models.py`)
```python
class LoginToken(models.Model):
    user = ForeignKey(CustomUser)           # Who the token is for
    token = CharField(max_length=64)        # Cryptographically secure random token
    created_at = DateTimeField()            # When created
    expires_at = DateTimeField()            # When it expires (default: +15 min)
    is_used = BooleanField(default=False)   # Single-use flag
    used_at = DateTimeField(null=True)      # When used
```

**Key Methods:**
- `LoginToken.create_token(user, expiry_minutes=15)` → Creates new token
- `token.is_valid()` → Returns True if not expired and not used
- `token.mark_as_used()` → Marks token as used (call after successful login)
- `LoginToken.cleanup_expired()` → Removes old tokens

---

## Token Flow

### Sending Login Link (`send_verification_view`)
```python
# 1. User enters email
user = CustomUser.objects.get(email=email)

# 2. Create database token record
login_token = LoginToken.create_token(user, expiry_minutes=15)

# 3. Sign the token (prevents tampering)
from django.core.signing import Signer
signer = Signer()
signed_token = signer.sign(login_token.token)

# 4. Build URL
url = f"{base_url}/verify-login/?token={signed_token}"

# 5. Send email
send_mail('Login Link', f'Click: {url}', ...)
```

### Verifying Login (`verify_login_view`)
```python
# 1. Get signed token from URL
signed_token = request.GET.get('token')

# 2. Verify signature and extract token
from django.core.signing import Signer, BadSignature
signer = Signer()
token = signer.unsign(signed_token)  # Raises BadSignature if tampered

# 3. Look up in database
login_token = LoginToken.objects.get(token=token)

# 4. Validate
if not login_token.is_valid():
    # Token expired or already used
    return error

# 5. Mark as used (single-use enforcement)
login_token.mark_as_used()

# 6. Log user in
login(request, login_token.user)
```

---

## Security Features

| Feature | Implementation | Benefit |
|---------|---------------|---------|
| **Cryptographic Signing** | Django's `Signer` with SECRET_KEY | Detects URL tampering |
| **Single-Use** | `is_used` flag + database constraint | Prevents token reuse |
| **Expiry** | `expires_at` timestamp (15 min default) | Time-limited validity |
| **Stateless** | Database storage, no session | Works across devices/restarts |
| **Secure Random** | `secrets.token_urlsafe(48)` | Unpredictable tokens |

---

## Common Operations

### Check Token Status
```python
token = LoginToken.objects.get(token='...')
print(f"Valid: {token.is_valid()}")
print(f"Used: {token.is_used}")
print(f"Expired: {token.expires_at < timezone.now()}")
```

### Clean Up Old Tokens
```bash
# Via management command
python manage.py cleanup_login_tokens

# Via Python
LoginToken.cleanup_expired()
```

### View Tokens in Admin
Navigate to: `/admin/voting/logintoken/`

---

## Error Messages

| Scenario | User Sees |
|----------|-----------|
| No token in URL | "No token provided." |
| Tampered token | "Invalid or tampered login link." |
| Token not in DB | "Invalid login link." |
| Token expired | "This login link has expired." |
| Token already used | "This login link has already been used." |
| Success | "Welcome back, [name]!" |

---

## Migration Notes

### What Changed:
- **Removed**: `request.session['verification_token']`
- **Removed**: `request.session['verification_email']`
- **Added**: `LoginToken` database model
- **Added**: Token signing with `Signer`

### Backward Compatibility:
- URL structure unchanged: `/verify-login/?token=...`
- Email format same (just different token format)
- No frontend changes needed

---

## Configuration

### Adjust Token Expiry
In `send_verification_view`:
```python
# Default: 15 minutes
login_token = LoginToken.create_token(user, expiry_minutes=15)

# Custom: 30 minutes
login_token = LoginToken.create_token(user, expiry_minutes=30)
```

### Adjust Cleanup Threshold
```bash
# Default: 7 days
python manage.py cleanup_login_tokens

# Custom: 30 days
python manage.py cleanup_login_tokens --days 30
```

---

## Database Schema

```sql
CREATE TABLE voting_logintoken (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    token VARCHAR(64) NOT NULL UNIQUE,
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    is_used BOOLEAN DEFAULT 0,
    used_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES voting_customuser(id)
);

CREATE INDEX idx_token_used ON voting_logintoken(token, is_used);
CREATE INDEX idx_expires ON voting_logintoken(expires_at);
```

---

## Testing Checklist

```python
# Create token
user = CustomUser.objects.get(email='test@example.com')
token = LoginToken.create_token(user)

# Verify it's valid
assert token.is_valid() == True

# Sign it
from django.core.signing import Signer
signer = Signer()
signed = signer.sign(token.token)

# Unsign and verify
unsigned = signer.unsign(signed)
assert unsigned == token.token

# Mark as used
token.mark_as_used()
assert token.is_valid() == False
```

---

## Troubleshooting

### "Invalid or tampered login link"
- SECRET_KEY changed after token was generated
- Token was manually edited in URL
- Solution: Request new login link

### "This login link has expired"
- More than 15 minutes since generation
- Solution: Request new login link

### "This login link has already been used"
- User clicked link twice
- Solution: Request new login link

### Token not found in database
- Database was cleared
- Token record deleted
- Solution: Request new login link

---

## Performance

- **Token Creation**: O(1) - single INSERT
- **Token Lookup**: O(1) - indexed query on `token` field
- **Token Validation**: O(1) - in-memory checks
- **Cleanup**: O(n) - batch DELETE with WHERE clause

**Expected Load:**
- 1000 users × 2 login attempts/day = 2000 tokens/day
- With 7-day retention: ~14,000 tokens in DB
- Negligible performance impact

---

## Production Recommendations

1. **Set up SECRET_KEY properly:**
   ```python
   # In settings.py
   SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'fallback-for-dev')
   ```

2. **Schedule cleanup:**
   ```bash
   # Cron: Daily at 3 AM
   0 3 * * * /path/to/venv/bin/python /path/to/manage.py cleanup_login_tokens
   ```

3. **Monitor token usage:**
   ```python
   # Add to monitoring dashboard
   active_tokens = LoginToken.objects.filter(
       is_used=False,
       expires_at__gt=timezone.now()
   ).count()
   ```

4. **Add rate limiting:**
   ```python
   # Prevent abuse: max 3 tokens per email per hour
   recent_tokens = LoginToken.objects.filter(
       user__email=email,
       created_at__gte=timezone.now() - timedelta(hours=1)
   ).count()
   
   if recent_tokens >= 3:
       return error("Too many requests")
   ```

---

## Files Modified

1. `voting/models.py` - Added LoginToken model
2. `voting/views.py` - Updated send/verify views
3. `voting/admin.py` - Added LoginTokenAdmin
4. `voting/migrations/0007_logintoken.py` - Database migration
5. `voting/management/commands/cleanup_login_tokens.py` - Cleanup utility

---

## Summary for AI Agents

**What to know:**
- Email login now uses database-backed tokens instead of sessions
- Tokens are signed (prevents tampering), expire after 15 min, single-use
- No session dependency means tokens work across devices/browsers
- Cleanup command available: `python manage.py cleanup_login_tokens`
- Admin interface at `/admin/voting/logintoken/`

**Common tasks:**
- Create token: `LoginToken.create_token(user, expiry_minutes=15)`
- Validate token: `token.is_valid()`
- Mark used: `token.mark_as_used()`
- Clean up: `LoginToken.cleanup_expired()` or management command

**Error handling:** Check `is_used`, `expires_at`, signature validity
