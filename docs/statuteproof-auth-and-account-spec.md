# StatuteProof — Auth and Account System Specification

**Version:** 1.0  
**Date:** 2026-06-12  
**Status:** Implementation-ready  
**Not legal advice. Internal spec only.**

---

## Overview

This document specifies the complete authentication, organization, and account system for StatuteProof. The current system uses a single-user JWT based on API_USERNAME/API_PASSWORD_HASH environment variables. This spec replaces it with a multi-user, multi-organization system suitable for pilot customers.

---

## 1. Database Schema

### Table: users

```sql
CREATE TABLE users (
  id                          INTEGER PRIMARY KEY AUTOINCREMENT,
  email                       TEXT NOT NULL UNIQUE,
  password_hash               TEXT NOT NULL,
  first_name                  TEXT NOT NULL,
  last_name                   TEXT NOT NULL,
  job_title                   TEXT,
  email_verified              INTEGER NOT NULL DEFAULT 0,
  email_verification_token    TEXT UNIQUE,
  email_verification_expires  DATETIME,
  password_reset_token        TEXT UNIQUE,
  password_reset_expires      DATETIME,
  last_login_at               DATETIME,
  created_at                  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at                  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_email_token ON users (email_verification_token);
CREATE INDEX idx_users_reset_token ON users (password_reset_token);
```

**Security notes:**
- password_hash: bcrypt, minimum 12 rounds. Never store plaintext passwords.
- email_verification_token: 32-byte random hex, single-use, expires 24 hours
- password_reset_token: 32-byte random hex, single-use, expires 1 hour
- Tokens deleted on use (set to NULL)

### Table: organizations

```sql
CREATE TABLE organizations (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  name                  TEXT NOT NULL,
  company_type          TEXT,
  jurisdiction          TEXT DEFAULT 'AE',
  plan_id               INTEGER REFERENCES subscription_plans(id),
  max_sources           INTEGER NOT NULL DEFAULT 5,
  max_custom_sources    INTEGER NOT NULL DEFAULT 0,
  max_users             INTEGER NOT NULL DEFAULT 2,
  max_client_profiles   INTEGER NOT NULL DEFAULT 1,
  api_access            INTEGER NOT NULL DEFAULT 0,
  white_label           INTEGER NOT NULL DEFAULT 0,
  created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### Table: memberships

```sql
CREATE TABLE memberships (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id               INTEGER NOT NULL REFERENCES users(id),
  org_id                INTEGER NOT NULL REFERENCES organizations(id),
  role                  TEXT NOT NULL CHECK (role IN ('owner','admin','compliance_user','reviewer','auditor')),
  invited_by_user_id    INTEGER REFERENCES users(id),
  invite_token          TEXT UNIQUE,
  invite_token_expires  DATETIME,
  invite_accepted_at    DATETIME,
  created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, org_id)
);

CREATE INDEX idx_memberships_user ON memberships (user_id);
CREATE INDEX idx_memberships_org ON memberships (org_id);
CREATE INDEX idx_memberships_invite_token ON memberships (invite_token);
```

### Table: subscription_plans

```sql
CREATE TABLE subscription_plans (
  id                    INTEGER PRIMARY KEY AUTOINCREMENT,
  plan_name             TEXT NOT NULL,
  plan_slug             TEXT NOT NULL UNIQUE,
  monthly_price_usd     INTEGER NOT NULL DEFAULT 0,
  max_sources           INTEGER NOT NULL DEFAULT 5,
  max_custom_sources    INTEGER NOT NULL DEFAULT 0,
  max_users             INTEGER NOT NULL DEFAULT 2,
  max_client_profiles   INTEGER NOT NULL DEFAULT 1,
  api_access            INTEGER NOT NULL DEFAULT 0,
  white_label           INTEGER NOT NULL DEFAULT 0,
  created_at            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Seed data
INSERT INTO subscription_plans (plan_name, plan_slug, monthly_price_usd, max_sources, max_custom_sources, max_users, max_client_profiles, api_access, white_label)
VALUES
  ('Free Source Readiness Review', 'free_review', 0, 0, 0, 1, 1, 0, 0),
  ('Founding Pilot', 'founding_pilot', 299, 5, 0, 2, 1, 0, 0),
  ('UAE VASP Pack', 'uae_vasp', 699, 13, 5, 5, 1, 0, 0),
  ('Compliance Consultant Pack', 'consultant', 1499, 13, 25, 10, 5, 1, 1);
```

### Table: user_legal_acknowledgements

```sql
CREATE TABLE user_legal_acknowledgements (
  id              INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id         INTEGER NOT NULL REFERENCES users(id),
  ack_type        TEXT NOT NULL,
  ack_text        TEXT NOT NULL,
  accepted        INTEGER NOT NULL DEFAULT 1,
  accepted_at     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  ip_address      TEXT,
  user_agent      TEXT
);

CREATE INDEX idx_legal_acks_user ON user_legal_acknowledgements (user_id, ack_type);
```

---

## 2. API Endpoints

### POST /api/v1/auth/register

**Auth:** None  
**Rate limit:** 5 registrations per IP per hour

**Request body:**
```json
{
  "email": "mlro@example.com",
  "password": "Secure12!@",
  "first_name": "Aisha",
  "last_name": "Al-Rahman",
  "job_title": "MLRO",
  "company_name": "Example VASP LLC",
  "company_type": "VASP",
  "country": "AE",
  "terms_accepted": true,
  "not_legal_advice_ack": true
}
```

**Validation:**
- email: valid format, not already registered (return 409 if duplicate — do not reveal whether email exists; use generic error)
- password: min 12 chars, at least 1 uppercase, 1 digit, 1 special character
- first_name, last_name, company_name: required, max 100 chars
- terms_accepted: must be true
- not_legal_advice_ack: must be true

**On success:**
1. Create User record with hashed password
2. Create Organization record
3. Create Membership record (role: owner)
4. Store legal acknowledgements in user_legal_acknowledgements table
5. Generate email_verification_token (32-byte random hex, expires 24h)
6. Send verification email
7. Return 201 with: `{ "user_id": 1, "org_id": 1, "message": "Verification email sent to [email]" }`

**Errors:**
- 400: Validation error (password too weak, missing required field, terms not accepted)
- 409: "An account with this email already exists" — only use this generic message, do not distinguish "exists but unverified"
- 429: "Too many registration attempts. Please try again later."

---

### POST /api/v1/auth/verify-email

**Auth:** None

**Request body:**
```json
{ "token": "abc123...32hexchars" }
```

**On success:** Mark email_verified = 1, delete token, return 200: `{ "verified": true }`  
**Errors:**
- 400: "Invalid or expired verification link. Request a new one."
- Token expiry: 24 hours. Token is single-use (nulled after use).

---

### POST /api/v1/auth/login

**Auth:** None  
**Rate limit:** 5 attempts per IP per 15 minutes; 10 per account per 30 minutes

**Request body:**
```json
{ "email": "mlro@example.com", "password": "Secure12!@" }
```

**On success:**
1. Verify email/password (bcrypt.checkpw)
2. Verify email_verified = 1 (if not: "Please verify your email before logging in. [Resend verification email]")
3. Fixed 200ms minimum response time (timing attack mitigation)
4. Create access token (JWT, 15 min expiry, payload: user_id, org_id, role, jti)
5. Create refresh token (JWT, 7 days, HttpOnly SameSite=Strict cookie)
6. Update last_login_at
7. Return: `{ "access_token": "...", "token_type": "bearer", "expires_in": 900, "user": { "id": 1, "email": "...", "name": "...", "role": "owner" }, "org": { "id": 1, "name": "...", "plan": "founding_pilot" } }`

**Errors:**
- 401: "Incorrect email or password." (same message for both — do not reveal which is wrong)
- 403: "Please verify your email before logging in." (with resend link)
- 429: "Too many failed attempts. Try again in 15 minutes or reset your password."

---

### POST /api/v1/auth/refresh

**Auth:** HttpOnly refresh cookie  

**On success:** New access token + rolling refresh cookie refresh (7 days from now)  
**Errors:** 401 if cookie missing, expired, or invalid

---

### POST /api/v1/auth/logout

**Auth:** Access JWT  

**On success:** Delete refresh cookie, invalidate jti in token blocklist (in-memory or DB)  
Return: 204 No Content

---

### POST /api/v1/auth/forgot-password

**Auth:** None  
**Rate limit:** 3 per IP per 10 minutes

**Request body:** `{ "email": "mlro@example.com" }`

**Response always:** 200 `{ "message": "If this email is registered, you will receive a reset link within 5 minutes." }`  
*Same response for registered and unregistered emails — prevent email enumeration.*

**If email registered:** Generate reset token (32-byte hex, 1 hour expiry), send password reset email.

---

### POST /api/v1/auth/reset-password

**Auth:** None

**Request body:**
```json
{ "token": "abc123...", "new_password": "NewSecure12!@" }
```

**Validation:** Token exists, not expired, not used. Password meets strength requirements.  
**On success:** Update password_hash, null the reset token, return 200.  
**Errors:** 400 if token invalid/expired, 400 if password too weak.

---

### POST /api/v1/auth/resend-verification

**Auth:** None  
**Rate limit:** 3 per email per hour

**Request body:** `{ "email": "mlro@example.com" }`  
**Response:** Always 200 (same message). Only sends email if user exists and is unverified.

---

### GET /api/v1/org

**Auth:** Access JWT (any role)  
**Returns:** Org profile + plan limits + current usage

---

### POST /api/v1/org/invite

**Auth:** Admin or Owner  
**Rate limit:** 20 invites per org per day

**Request body:**
```json
{ "email": "analyst@example.com", "role": "compliance_user" }
```

**Validation:**
- Email not already a member
- Org has not exceeded max_users limit
- Role is valid enum value
- Inviter is admin or owner

**On success:**
1. Create membership record with invite_token (48-byte hex, expires 72 hours)
2. Send invite email
3. Return 201: `{ "membership_id": N, "invite_sent": true }`

---

### POST /api/v1/auth/accept-invite

**Auth:** None (invite token is auth)

**Request body:**
```json
{
  "token": "invite_token_here",
  "password": "Secure12!@",
  "first_name": "Sara",
  "last_name": "Al-Mansoori",
  "terms_accepted": true,
  "not_legal_advice_ack": true
}
```

**On success:**
1. Create User record
2. Accept membership (set invite_accepted_at, clear invite_token)
3. Store legal acks
4. Send verification email (or auto-verify if invite email matches)
5. Return 201 with login credentials ready

---

## 3. Role Permissions Table

| Permission | Owner | Admin | Compliance User | Reviewer | Auditor |
|-----------|-------|-------|-----------------|----------|---------|
| View alerts | Yes | Yes | Yes | Yes | Yes |
| View evidence records | Yes | Yes | Yes | Yes | Yes |
| View briefs | Yes | Yes | Yes | Yes | Yes |
| View sources | Yes | Yes | Yes | Yes | Yes |
| Export evidence records | Yes | Yes | Yes | Yes | No |
| Export briefs | Yes | Yes | Yes | Yes | No |
| Approve/reject alerts | Yes | Yes | No | Yes | No |
| Approve briefs | Yes | Yes | No | Yes | No |
| Configure sources | Yes | Yes | No | No | No |
| Add custom sources | Yes | Yes | No | No | No |
| Pause/resume sources | Yes | Yes | No | No | No |
| Invite team members | Yes | Yes | No | No | No |
| Change member roles | Yes | Yes | No | No | No |
| Remove members | Yes | Yes | No | No | No |
| View team list | Yes | Yes | Yes | Yes | Yes |
| View org profile | Yes | Yes | Yes | Yes | Yes |
| Edit org profile | Yes | Yes | No | No | No |
| Access billing | Yes | No | No | No | No |
| Delete org data | Yes | No | No | No | No |

---

## 4. Email Flows

### Registration Verification Email

**Trigger:** POST /api/v1/auth/register  
**To:** Registered email  
**Subject:** "Verify your StatuteProof account"  
**Body:**
```
You're almost set up. Click below to verify your email and complete registration.

[Verify email address]  → /verify-email?token=[token]

This link expires in 24 hours and can only be used once.

If you did not sign up for StatuteProof, you can safely ignore this email.

StatuteProof — Official-source regulatory monitoring for UAE compliance teams.
For monitoring information only. Not legal advice.
```

### Password Reset Email

**Trigger:** POST /api/v1/auth/forgot-password (when email found)  
**Subject:** "Reset your StatuteProof password"  
**Body:**
```
We received a request to reset the password for your StatuteProof account.

[Reset password]  → /reset-password?token=[token]

This link expires in 1 hour and can only be used once.

If you did not request a password reset, your account is secure and you can ignore this email.

StatuteProof
For monitoring information only. Not legal advice.
```

### Team Invite Email

**Trigger:** POST /api/v1/org/invite  
**Subject:** "[InviterName] invited you to join [OrgName] on StatuteProof"  
**Body:**
```
[InviterName] has invited you to join [OrgName]'s StatuteProof account as a [Role].

StatuteProof is an official-source regulatory monitoring tool for UAE compliance teams. 
It detects changes on UAE regulatory sources and delivers human-reviewed compliance briefs.

[Accept invitation]  → /accept-invite?token=[invite_token]

This invitation expires in 72 hours.

StatuteProof
For monitoring information only. Not legal advice.
```

---

## 5. Validation Rules

### Password

- Minimum 12 characters
- At least 1 uppercase letter
- At least 1 lowercase letter
- At least 1 digit
- At least 1 special character (!@#$%^&*()_+-=[]{}|;:',.<>?)
- Maximum 200 characters

**Error messages:**
- "Password must be at least 12 characters"
- "Password must include at least one uppercase letter"
- "Password must include at least one number"
- "Password must include at least one special character"

### Email

- Standard RFC 5322 format validation
- Disposable email check (recommended, not required for MVP)
- Maximum 254 characters
- Stored lowercase

### Company Name

- Minimum 2 characters
- Maximum 200 characters
- No HTML allowed (strip/escape)

### Role Values

Valid enum: owner, admin, compliance_user, reviewer, auditor  
Error: "Invalid role. Permitted values: admin, compliance_user, reviewer, auditor" (owner not settable via invite — only first user gets owner)

---

## 6. Error Messages (UI Copy)

| Scenario | Error message |
|----------|--------------|
| Email already registered | "An account with this email address already exists. [Log in] or [Reset password]." |
| Password too weak | "Password does not meet requirements. [See requirements]" |
| Terms not accepted | "You must accept the Terms of Service to create an account." |
| Not-legal-advice not accepted | "You must acknowledge that StatuteProof reports are not legal advice to continue." |
| Email verification token expired | "This verification link has expired. [Request a new one]" |
| Reset token expired | "This password reset link has expired. [Request a new one]" |
| Wrong email/password | "Incorrect email or password." |
| Account locked (rate limit) | "Too many failed attempts. Please try again in 15 minutes or [reset your password]." |
| Email not verified | "Please verify your email address before logging in. [Resend verification email]" |
| Invite token expired | "This invitation has expired. Contact your team administrator for a new invite." |
| Invite token invalid | "This invitation link is invalid or has already been used." |
| Max users reached | "Your organization has reached its user limit. Upgrade your plan to add more team members." |

---

## 7. Session Management

### Access Token (JWT)

- Algorithm: HS256
- Secret: JWT_SECRET from environment variable (min 32 chars, random)
- Expiry: 15 minutes
- Payload: `{ "sub": user_id, "org_id": org_id, "role": role, "jti": uuid, "iat": ..., "exp": ... }`
- Storage: Memory (not localStorage — XSS risk)

### Refresh Token (JWT)

- Algorithm: HS256
- Separate secret: REFRESH_SECRET from environment variable
- Expiry: 7 days, rolling (reissued on each refresh)
- Storage: HttpOnly, Secure, SameSite=Strict cookie
- Name: `sp_refresh` (short, not obvious)
- Path: `/api/v1/auth` (restrict cookie scope)

### Token Revocation

- On logout: jti stored in in-memory blocklist (or DB table for multi-server deployments)
- On password reset: all existing refresh tokens invalidated (store user_token_version, increment on reset)
- Session view in Settings: show active sessions (last IP, last active time, device hint from user-agent)
- Revoke all: endpoint to invalidate all refresh tokens for a user

---

## 8. Magic Link (Future Feature — Not MVP)

Magic link login is specified here for future implementation:

1. User enters email on login page, clicks "Send login link"
2. Server generates 48-byte random token, stores with email + expiry (15 min)
3. Email sent with link: /magic-login?token=[token]
4. User clicks link → token verified, deleted, user logged in, JWT issued
5. Same session management as password login

Security considerations for future implementation:
- 15 minute expiry (shorter than verification links)
- Single use only
- IP check (warn if different IP from request to click)
- Rate limit: 3 per email per 15 min

---

## 9. Implementation Notes

### Current State

The existing auth in `product/regradar/app/auth.py` and `product/regradar/app/api/v1/router.py` uses:
- `API_USERNAME` and `API_PASSWORD_HASH` from `.env` (single user)
- JWT creation in `product/regradar/app/infrastructure/security/auth.py`

### Migration Path

1. Create new DB tables (users, organizations, memberships, subscription_plans, user_legal_acknowledgements) as a migration alongside existing schema
2. Implement new auth endpoints at `/api/v1/auth/register`, `/api/v1/auth/verify-email` etc.
3. Update existing endpoints to read user_id + org_id from JWT payload (not just username from env)
4. Add role-checking middleware using the roles table
5. Legacy single-user login can remain as fallback during transition if needed (remove once all pilot users are migrated)

### File Locations

New files to create:
- `product/regradar/app/auth_service.py` — registration, verification, password reset logic
- `product/regradar/app/org_service.py` — org creation, membership, invite logic
- `product/regradar/app/email_service.py` — transactional email (Resend or similar)
- `product/regradar/app/models/user.py` — User model
- `product/regradar/app/models/organization.py` — Organization, Membership models
- `product/regradar/app/middleware/auth_middleware.py` — JWT validation + role extraction for all protected routes
- DB migration: `product/regradar/app/db_migrations/001_add_auth_tables.py`

---

*Not legal advice. Internal implementation specification.*
