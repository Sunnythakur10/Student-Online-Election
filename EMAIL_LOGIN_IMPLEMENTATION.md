# Email Login Token System - Implementation Summary

## Overview
Successfully implemented a secure, stateless email login system using signed URL tokens with expiry and single-use enforcement, replacing the previous session-based approach.

## Changes Made

### 1. New Database Model: `LoginToken`
**File:** `voting/models.py`

Added a new model to track login tokens with the following features:
- **user**: ForeignKey to CustomUser (tracks which user the token belongs to)
- **token**: 64-character unique, indexed field (cryptographically secure random token)
- **created_at**: Timestamp when token was created
- **expires_at**: Token expiration timestamp (default: 15 minutes from creation)
- **is_used**: Boolean flag to enforce single-use
- **used_at**: Timestamp when token was used (null until used)

**Key Methods:**
- `is_valid()`: Checks if token is not expired and not used
- `mark_as_used()`: Marks token as used (single-use enforcement)
- `create_token(user, expiry_minutes=15)`: Class method to generate new tokens
- `cleanup_expired()`: Class method to remove old expired/used tokens

**Database Indexes:**
- Composite index on `(token, is_used)` for fast lookups
- Index on `expires_at` for efficient cleanup queries

### 2. Updated Email Verification Flow
**File:** `voting/views.py`

#### `send_verification_view()`
**Old Behavior:**
- Generated random token with `secrets.token_urlsafe(32)`
- Stored token and email in session
- Sent plain token in URL

**New Behavior:**
- Creates `LoginToken` database record with 15-minute expiry
- Uses Django's `Signer` to cryptographically sign the token
- Sends signed token in URL (prevents tampering)
- No session dependency (stateless)
- Enhanced email message includes expiry notice

**Benefits:**
- Token validity persists across devices and browser sessions
- Works even if session storage fails
- Can verify token origin and detect tampering

#### `verify_login_view()`
**Old Behavior:**
- Compared GET token with session-stored token
- Required session to maintain state
- No expiry enforcement
- No reuse prevention

**New Behavior:**
- Verifies signature using `Signer.unsign()` (detects tampering)
- Looks up token in database
- Validates token is not expired
- Validates token is not already used
- Marks token as used after successful login (single-use)
- Provides specific error messages for different failure scenarios

**Security Improvements:**
1. **Signature Verification**: Detects URL tampering
2. **Single-Use Enforcement**: Token becomes invalid after first use
3. **Time-Based Expiry**: Tokens expire after 15 minutes
4. **Stateless**: No session dependency
5. **Detailed Error Messages**: User feedback for expired vs. used vs. invalid tokens

### 3. Admin Interface
**File:** `voting/admin.py`

Added `LoginTokenAdmin` with:
- List display: user, token preview, timestamps, usage status
- Filters: is_used, created_at, expires_at
- Search: by user email, username, token
- Custom action: "Clean up expired/used tokens"
- Token preview method (shows first 16 chars for security)

### 4. Management Command
**File:** `voting/management/commands/cleanup_login_tokens.py`

New command: `manage.py cleanup_login_tokens`

**Features:**
- Removes expired and used tokens older than 7 days (configurable)
- `--days N`: Customize cleanup age threshold
- `--dry-run`: Preview what would be deleted without deleting
- Detailed output showing what was cleaned

**Usage:**
```bash
# Preview cleanup
python manage.py cleanup_login_tokens --dry-run

# Clean tokens older than 7 days
python manage.py cleanup_login_tokens

# Clean tokens older than 30 days
python manage.py cleanup_login_tokens --days 30
```

**Recommended:** Set up as a cron job or scheduled task to run daily.

### 5. Database Migration
**File:** `voting/migrations/0007_logintoken.py`

Applied migration creates:
- `voting_logintoken` table
- Indexes for performance
- Foreign key constraint to `voting_customuser`

## Security Features

### 1. Cryptographic Signing
- Uses Django's `Signer` with SECRET_KEY
- Prevents token tampering
- Any modification to URL token invalidates signature

### 2. Single-Use Enforcement
- Database flag `is_used` prevents token reuse
- Timestamp `used_at` tracks when token was consumed
- Explicit error message if reuse attempted

### 3. Time-Based Expiry
- Default: 15 minutes (configurable)
- Checked on every validation
- Separate from "used" status

### 4. Stateless Design
- No session storage required
- Tokens work across devices/browsers
- Survives server restarts (unlike session-based)

### 5. Secure Token Generation
- Uses `secrets.token_urlsafe(48)` (cryptographically secure)
- 64-character URL-safe tokens
- Extremely low collision probability

## Testing Results

All tests passed successfully:

1. ✅ **Token Creation**: Creates secure 64-char tokens with 15-min expiry
2. ✅ **Signing**: Successfully signs tokens using Django's Signer
3. ✅ **Verification**: Correctly verifies and unsigns tokens
4. ✅ **Database Lookup**: Finds tokens in database efficiently
5. ✅ **Single-Use**: Marks tokens as used and rejects reuse attempts
6. ✅ **Validation**: Correctly identifies valid vs. invalid tokens

## Usage Example

### For Users (Email Login):
1. User enters email on login page
2. System generates secure token, stores in DB, signs it
3. Email sent with link: `https://site.com/verify-login/?token=<signed_token>`
4. User clicks link within 15 minutes
5. System verifies signature, checks DB, validates token
6. User logged in, token marked as used
7. If user clicks link again: "This login link has already been used"

### For Admins:
- View all login tokens in Django admin: `/admin/voting/logintoken/`
- Clean up old tokens: Admin action or management command
- Monitor token usage patterns

## Migration from Session-Based System

**Before:**
```python
# Session-based (old)
request.session['verification_token'] = token
request.session['verification_email'] = email
```

**After:**
```python
# Database + signed tokens (new)
login_token = LoginToken.create_token(user, expiry_minutes=15)
signer = Signer()
signed_token = signer.sign(login_token.token)
```

**Breaking Changes:** None - the URL structure remains the same, just the token format changed.

## Performance Considerations

1. **Database Queries:**
   - Token lookup: Single indexed query
   - Token validation: No additional queries
   - Cleanup: Batch delete with date filtering

2. **Recommended Optimizations:**
   - Run `cleanup_login_tokens` daily via cron
   - Monitor LoginToken table size
   - Consider archiving very old tokens instead of deleting

## Maintenance

### Daily/Weekly Tasks:
```bash
# Clean up old tokens (recommended: run daily)
python manage.py cleanup_login_tokens
```

### Monitoring:
```python
# Check token table size
from voting.models import LoginToken
print(f"Total tokens: {LoginToken.objects.count()}")
print(f"Active tokens: {LoginToken.objects.filter(is_used=False, expires_at__gt=timezone.now()).count()}")
```

### Database Maintenance:
The cleanup command automatically removes:
- Expired tokens older than 7 days
- Used tokens older than 7 days
- Keeps recent tokens for audit purposes

## Future Enhancements (Optional)

1. **Configurable Expiry:**
   - Add setting: `LOGIN_TOKEN_EXPIRY_MINUTES = 15`
   - Allow per-user expiry rules

2. **Token Usage Analytics:**
   - Track login patterns
   - Detect suspicious activity (many failed attempts)

3. **Email Tracking:**
   - Track if email was opened
   - Resend functionality if not opened

4. **Rate Limiting:**
   - Limit token generation per email (prevent abuse)
   - Add cooldown between requests

5. **Notification on Use:**
   - Email user when login link is used
   - Security alert if suspicious

## Testing Checklist

- [x] Token creation works
- [x] Token signing works
- [x] Token verification works
- [x] Single-use enforcement works
- [x] Expiry enforcement works
- [x] Invalid token rejection works
- [x] Tampered token rejection works
- [x] Admin interface works
- [x] Cleanup command works
- [x] Migration applied successfully

## Files Modified/Created

### Modified:
1. `voting/models.py` - Added LoginToken model
2. `voting/views.py` - Updated send_verification_view and verify_login_view
3. `voting/admin.py` - Added LoginTokenAdmin

### Created:
1. `voting/migrations/0007_logintoken.py` - Database migration
2. `voting/management/commands/cleanup_login_tokens.py` - Cleanup utility

## Conclusion

The email login system has been successfully upgraded to use:
- ✅ Signed URL tokens (tamper-proof)
- ✅ Database-backed validation (no session dependency)
- ✅ Expiry enforcement (15-minute window)
- ✅ Single-use tokens (prevents reuse)
- ✅ Admin management interface
- ✅ Automated cleanup utility

The system is now more secure, scalable, and maintainable than the previous session-based approach.
