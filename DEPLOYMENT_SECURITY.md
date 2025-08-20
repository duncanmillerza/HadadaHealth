# HadadaHealth Security Deployment Guide

## 🚨 **CRITICAL: Security Configuration Required**

This application requires proper security configuration before deployment. **DO NOT deploy without completing these steps.**

---

## 🔐 **Environment Variables Setup**

### Required Environment Variables

#### `SESSION_SECRET_KEY` (CRITICAL)
**Purpose:** Secures user sessions and prevents session forgery attacks.

**Requirements:**
- Must be at least 32 characters long
- Must be cryptographically secure (use the generator below)
- Must be unique for each environment (dev/staging/prod)
- Must be kept secret and secure

**Generate a secure key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example:**
```bash
SESSION_SECRET_KEY=zrMAVrCnDd3n4VBGn6xUGttPwU08eWpSg1CeaItlW7k
```

### Optional Environment Variables

#### `ENVIRONMENT`
- Values: `development`, `staging`, `production`
- Default: `development`
- Production enables additional security features

#### `DEBUG`
- Values: `true`, `false`
- Default: `false` in production
- Should always be `false` in production

#### `DATABASE_PATH`
- Path to SQLite database file
- Default: `data/bookings.db`

#### `OPENROUTER_API_KEY`
- API key for AI features
- Optional unless using AI functionality

---

## 🚀 **Deployment Steps**

### 1. Development Environment
```bash
# Copy environment template
cp .env.example .env

# Generate secure session key
python -c "import secrets; print('SESSION_SECRET_KEY=' + secrets.token_urlsafe(32))" >> .env

# Update other values as needed
nano .env
```

### 2. Production Environment

#### Option A: Environment Variables
```bash
export SESSION_SECRET_KEY="your-generated-key-here"
export ENVIRONMENT="production"
export DEBUG="false"
export DATABASE_PATH="/path/to/production/database.db"
```

#### Option B: Production .env file
```bash
# Create production .env (secure the file with proper permissions)
touch .env
chmod 600 .env

# Add configuration
echo "SESSION_SECRET_KEY=your-generated-key-here" >> .env
echo "ENVIRONMENT=production" >> .env
echo "DEBUG=false" >> .env
```

### 3. Security Validation
The application will automatically validate security configuration at startup:

```
🔐 Validating security configuration...
✅ Session secret key loaded (length: 43 characters)
✅ Session key meets minimum security requirements
🌍 Environment: production
🔒 Production mode: Enhanced security settings active
```

---

## 🔒 **Security Features**

### Automatic Security Enhancements

#### Development Mode
- Standard session security
- Debug information available
- Relaxed cookie policies

#### Production Mode
- HTTPS-only cookies (requires HTTPS deployment)
- Strict same-site policy
- Enhanced session security
- No debug information exposed

### Session Security
- Cryptographically secure session keys
- Automatic session validation
- Secure cookie attributes in production
- Protection against session forgery

---

## 🛡️ **Security Checklist**

### Pre-Deployment Security Checklist
- [ ] Generated unique session secret key for this environment
- [ ] Verified key is at least 32 characters long
- [ ] Set `ENVIRONMENT=production` for production deployment
- [ ] Set `DEBUG=false` for production
- [ ] Secured .env file with proper permissions (600)
- [ ] Verified no secrets are committed to version control
- [ ] Tested application startup with security validation
- [ ] Configured HTTPS for production deployment
- [ ] Implemented proper backup procedures for environment configuration

### Post-Deployment Security Verification
- [ ] Verified security validation messages appear in logs
- [ ] Confirmed session cookies have secure attributes
- [ ] Tested user authentication functionality
- [ ] Verified no hardcoded secrets in deployed code
- [ ] Confirmed debug mode is disabled
- [ ] Tested session security (no session forgery possible)

---

## 🔄 **Key Rotation Procedures**

### When to Rotate Keys
- **Immediately:** If key is compromised or exposed
- **Regularly:** Every 90 days for production environments
- **Before:** Major releases or security updates
- **After:** Security incidents or staff changes

### How to Rotate Keys

#### 1. Generate New Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 2. Update Environment
```bash
# Update environment variable
export SESSION_SECRET_KEY="new-key-here"

# OR update .env file
sed -i 's/SESSION_SECRET_KEY=.*/SESSION_SECRET_KEY=new-key-here/' .env
```

#### 3. Restart Application
```bash
# Restart to load new key
systemctl restart hadadahealth  # or your deployment method
```

#### 4. Verify
- Check logs for successful security validation
- Test user authentication
- Verify all users need to re-authenticate (expected behavior)

---

## 🚨 **Security Incident Response**

### If Session Key Compromised

#### Immediate Actions (within 1 hour)
1. **Rotate session key immediately**
2. **Restart application**
3. **Invalidate all active sessions** (users must re-login)
4. **Review access logs for suspicious activity**
5. **Document incident timeline**

#### Investigation (within 24 hours)
1. **Identify how key was compromised**
2. **Review all system access during exposure period**
3. **Check for unauthorized data access**
4. **Assess impact on patient data (POPIA compliance)**

#### Recovery Actions
1. **Implement additional security measures**
2. **Update security procedures**
3. **Staff security training if needed**
4. **Consider legal/compliance notification requirements**

---

## 📊 **Monitoring and Alerting**

### Security Monitoring
Monitor these events in production:
- Failed security validation on startup
- Session-related errors
- Unusual authentication patterns
- Configuration changes

### Log Examples

#### Successful Startup
```
🔐 Validating security configuration...
✅ Session secret key loaded (length: 43 characters)
✅ Session key meets minimum security requirements
🔒 Production mode: Enhanced security settings active
```

#### Security Failure
```
❌ Configuration Error: SESSION_SECRET_KEY environment variable is required
🔧 To fix this:
1. Create a .env file in the project root
2. Add: SESSION_SECRET_KEY=<your-generated-key>
3. Generate a key with: python -c 'import secrets; print(secrets.token_urlsafe(32))'
```

---

## 🆘 **Troubleshooting**

### Common Issues

#### "SESSION_SECRET_KEY environment variable is required"
**Cause:** Missing or empty SESSION_SECRET_KEY
**Solution:**
```bash
python -c "import secrets; print('SESSION_SECRET_KEY=' + secrets.token_urlsafe(32))"
# Add output to .env file
```

#### "SESSION_SECRET_KEY must be at least 32 characters long"
**Cause:** Key too short for security requirements
**Solution:** Generate a new key using the command above

#### "Security configuration validation failed"
**Cause:** Multiple configuration issues
**Solution:** Check all environment variables and restart application

#### Application won't start
**Cause:** Security validation prevents insecure deployment
**Solution:** This is intentional - fix the security configuration first

### Support Contacts
For security-related deployment issues:
1. Check this documentation first
2. Review application startup logs
3. Verify environment variable configuration
4. Contact development team if needed

## 🗂️ **Database File Security**

### Critical Database File Permissions

**CRITICAL**: Database files must be secured to prevent unauthorized access to patient data.

#### Required File Permissions

```bash
# Secure the data directory (owner access only)
chmod 700 data/

# Secure all database files (owner read/write only)
chmod 600 data/bookings.db
chmod 600 data/icd10_with_pmb.db
```

#### Automated Security Setup

Run the provided security script to automatically secure database files:

```bash
./secure_database.sh
```

This script will:
- Create data directory with secure permissions (700)
- Set database file permissions to 600 (owner only)
- Verify all permissions are correctly applied
- Display security status confirmation

#### Manual Verification

Check database file permissions:
```bash
ls -la data/
```

Expected output:
```
drwx------  4 user  group   128 date data/
-rw-------  1 user  group  196608 date bookings.db
-rw-------  1 user  group   13MB  date icd10_with_pmb.db
```

#### Production Deployment Notes

- **Dedicated User**: Run application as dedicated user, not root
- **File Ownership**: Ensure database files owned by application user
- **Backup Security**: Maintain same permissions on database backups
- **System Monitoring**: Monitor for unauthorized file permission changes

### POPIA Compliance Requirements

The database contains sensitive patient information subject to POPIA regulations:
- **Personal Information**: Names, contact details, ID numbers
- **Medical Records**: Treatment notes, diagnoses, medical history
- **Financial Data**: Billing information, medical aid details

**Failure to secure database files = POPIA violation + potential data breach**

---

**⚠️ REMEMBER: This security configuration is critical for protecting patient data and maintaining POPIA compliance. Never skip or bypass security validation.**