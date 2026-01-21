# Two-Step Registration System Documentation

## Overview

The registration system has been updated to implement a two-step verification process:

1. **Step 1: User Registration** - Users register without a password
2. **Step 2: Admin Acceptance & Password Setup** - Admin approves users, who then set their password

## System Architecture

### Modified Components

#### 1. Models (`account/models.py`)
- **Doctor model** now includes:
  - `is_accepted` (Boolean): Tracks whether a doctor's account has been approved
  - `accepted_at` (DateTime): Timestamp of when the doctor was accepted
  - Made other fields optional (nullable) since they're not needed during registration

#### 2. Serializers (`account/serializers.py`)
- **RegisterSerializer**: Used during registration - requires: speciality, full_name, email, phone_number (NO password)
- **SetPasswordSerializer**: Used when accepted user sets password - requires: password, password_confirm (with validation)
- **AcceptUserSerializer**: Used by admin - requires: user_id, action (accept/reject)

#### 3. API Endpoints (`account/json_api.py`)

##### Registration Endpoint
```
POST /api/auth/register
```
**Request Body:**
```json
{
  "full_name": "Dr. John Doe",
  "email": "john@example.com",
  "phone_number": "+212612345678",
  "speciality": "eyes"
}
```

**Response (201 Created):**
```json
{
  "status": "success",
  "message": "Registration successful! Please wait for admin approval...",
  "user": {
    "id": 1,
    "email": "john@example.com",
    "full_name": "Dr. John Doe",
    "speciality": "eyes",
    "is_active": false,
    "is_accepted": false
  }
}
```

**Key Behaviors:**
- User is created with `is_active=False` (cannot login yet)
- No password is set initially
- Email is used as the username
- Doctor profile is created with `is_accepted=False`

##### Accept User Endpoint (Admin Only)
```
POST /api/auth/accept-user
```

**Authentication:** Required (Admin/Staff user)

**Request Body:**
```json
{
  "user_id": 1,
  "action": "accept"
}
```

**Valid Actions:**
- `"accept"` - Approve the user and send password setup email
- `"reject"` - Reject and delete the user account

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "User {name} has been accepted. Acceptance email sent.",
  "user": {
    "id": 1,
    "email": "john@example.com",
    "full_name": "Dr. John Doe",
    "is_accepted": true,
    "is_active": false
  }
}
```

**Key Behaviors:**
- Sets `is_accepted=True` and `accepted_at` to current timestamp
- Generates a secure token (24-hour expiry)
- Sends acceptance email with password setup link
- Link format: `{FRONTEND_URL}/set-password/{uid}/{token}/`

##### Set Password Endpoint
```
POST /api/auth/set-password
```

**Authentication:** Not required (uses token-based validation)

**Request Body:**
```json
{
  "uid": "MQ==",
  "token": "1a2b3c4d5e6f...",
  "password": "SecurePassword123!",
  "password_confirm": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "status": "success",
  "message": "Password set successfully! You can now log in.",
  "user": {
    "id": 1,
    "email": "john@example.com",
    "full_name": "Dr. John Doe",
    "is_active": true
  }
}
```

**Key Behaviors:**
- Validates token (24-hour expiry)
- Validates password confirmation match
- Sets user password and activates account (`is_active=True`)
- Sends confirmation email

## User Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. Doctor Registers                                             │
│    POST /api/auth/register                                      │
│    - No password required                                       │
│    - User inactive (is_active=False)                            │
│    - Doctor not accepted (is_accepted=False)                    │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Waiting for Admin Review                                     │
│    - User can see application status                            │
│    - Cannot login yet                                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Admin Reviews & Accepts User                                 │
│    POST /api/auth/accept-user                                   │
│    - Sets is_accepted=True                                      │
│    - Sends acceptance email with password setup link            │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. User Receives Email & Sets Password                          │
│    POST /api/auth/set-password                                  │
│    - Validates token                                            │
│    - Sets password                                              │
│    - Activates account (is_active=True)                         │
└─────────────────────┬───────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. User Can Now Login                                           │
│    POST /api/auth/login                                         │
│    - User is fully active                                       │
│    - Can access all doctor features                             │
└─────────────────────────────────────────────────────────────────┘
```

## Email Templates

### Acceptance Email (Sent by Admin)
Sent when admin accepts a user. Contains:
- Congratulations message
- Password setup link with token
- Token expiry information (24 hours)

### Password Setup Confirmation Email
Sent after user successfully sets password. Contains:
- Confirmation that password was set
- Login URL
- Security notice about contacting support if unauthorized

## Configuration

### Required Settings

Add to `settings.py`:

```python
# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # or your email backend
EMAIL_HOST = 'your-email-host'
EMAIL_PORT = 587  # or 465 for SSL
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-email-password'
DEFAULT_FROM_EMAIL = 'noreply@yourdomain.com'

# Frontend URL for password setup link
FRONTEND_URL = 'http://localhost:3000'  # Change in production
```

## Frontend Integration

### 1. Registration Page
```javascript
// POST /api/auth/register
const registerUser = async (formData) => {
  const response = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      full_name: formData.fullName,
      email: formData.email,
      phone_number: formData.phoneNumber,
      speciality: formData.speciality
    })
  });
  return response.json();
};
```

### 2. Pending Approval Status Page
Display message that registration is pending admin approval.

### 3. Set Password Page
Triggered from email link: `/set-password/{uid}/{token}/`

```javascript
// POST /api/auth/set-password
const setPassword = async (uid, token, password, passwordConfirm) => {
  const response = await fetch('/api/auth/set-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      uid: uid,
      token: token,
      password: password,
      password_confirm: passwordConfirm
    })
  });
  return response.json();
};
```

## Admin Panel Features

### Pending Users List
Create an endpoint to list pending users:

```python
# Optional: Add this to json_api.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_pending_users_api(request):
    if not request.user.is_staff:
        return Response({"error": "Admin only"}, status=403)
    
    pending = Doctor.objects.filter(is_accepted=False)
    # Return serialized list of pending doctors
```

### Admin Accept/Reject
Use the `/api/auth/accept-user` endpoint with admin credentials.

## Security Features

1. **Token-based Verification**: Uses Django's PasswordResetTokenGenerator
2. **Token Expiry**: 24 hours
3. **Inactive Accounts**: Unaccepted users cannot login
4. **Email Verification**: Setup link sent only to registered email
5. **Password Confirmation**: Prevents accidental typos

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "User already exists" | Email/phone already registered | Use different email/phone |
| "Permission denied" | Non-admin trying to accept user | Use admin account |
| "Invalid or expired token" | Token expired (>24hrs) | Request new acceptance link |
| "Passwords do not match" | Password confirmation mismatch | Re-enter passwords carefully |
| "Your account has not been accepted" | Trying to set password before approval | Wait for admin approval |

## Database Migration

Run migrations to add new fields:

```bash
python manage.py migrate account
```

The migration file `0002_doctor_acceptance_fields.py` adds:
- `is_accepted` field to Doctor model
- `accepted_at` field to Doctor model
- Makes optional: img, number_of_phone, instagram_account, inpe, ville

## Testing

### Test Registration
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Dr. Test",
    "email": "test@example.com",
    "phone_number": "+212612345678",
    "speciality": "eyes"
  }'
```

### Test Accept User (as admin)
```bash
curl -X POST http://localhost:8000/api/auth/accept-user \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -d '{
    "user_id": 1,
    "action": "accept"
  }'
```

## Troubleshooting

### Emails not sending
- Check EMAIL settings in settings.py
- Verify email credentials
- Check mail logs: `logger.error(f"Error sending email: {e}")`

### Token validation fails
- Ensure FRONTEND_URL is correct in settings
- Token expires after 24 hours
- Check user ID encoding/decoding

### User still inactive after password setup
- Verify token validation passed
- Check that user profile's `is_accepted=True`
- Check database directly

## Future Enhancements

1. Add SMS verification
2. Implement email-based approval notifications
3. Add bulk user acceptance
4. Add user status dashboard
5. Implement password strength requirements
6. Add 2FA (Two-Factor Authentication)
