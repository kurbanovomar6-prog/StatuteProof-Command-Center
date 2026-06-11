# Sprint Auth B2 — Full Name Persistence

## 1. Verdict

Full name persistence is implemented.

New registrations can send `full_name`, and the backend stores it on the `users` table. Existing users remain compatible because the column is nullable and added through an idempotent migration. Public auth user responses now include `full_name` and still exclude `password_hash`.

## 2. Files changed

- `app/db.py`
- `app/auth.py`
- `app/api.py`
- `web/src/components/auth/RegisterPage.jsx`
- `web/src/components/app/AppSidebar.jsx`
- `web/src/components/app/AppTopbar.jsx`
- `reports/sprint_auth_b2_full_name_persistence.md`

## 3. Database migration

Added nullable column:

```sql
full_name TEXT
```

The `users` table `CREATE TABLE IF NOT EXISTS` statement now includes `full_name`.

`ensure_auth_tables()` also performs an idempotent migration:

```sql
ALTER TABLE users ADD COLUMN full_name TEXT
```

The migration checks `PRAGMA table_info(users)` first, so it does not fail if the column already exists.

## 4. Backend auth changes

`create_user()` now accepts:

- `full_name=None`
- `company_name=None`
- `industry=None`

`full_name` is sanitized as optional text:

- stripped;
- capped at 160 characters;
- empty values stored as `NULL`.

Auth lookups now select `full_name`:

- `get_user_by_email()`
- `get_user_by_id()`
- `validate_session()`

`make_public_user()` now returns `full_name` and still never returns `password_hash` or session tokens.

## 5. Frontend register changes

`RegisterPage.jsx` already had a full name input from the landing-account flow cleanup. It now sends:

```js
full_name: form.name
```

The register endpoint also accepts fallback aliases:

- `full_name`
- `fullName`
- `name`

Full name is optional and registration remains short.

## 6. UI display changes

The app shell now prefers full name where appropriate:

- `AppSidebar.jsx`
- `AppTopbar.jsx`

Display fallback order:

```text
currentUser.full_name → currentUser.company_name → currentUser.email
```

Company and email remain available as fallbacks.

## 7. Validation result

Commands run:

```bash
python3 -m compileall app run.py -q
cd web && npm run build
git diff --check
```

Results:

- Backend compile: PASS
- Frontend build: PASS
- Diff whitespace check: PASS

Smoke test run:

```bash
python3 - <<'PY'
from app.db import ensure_auth_tables
from app.auth import create_user, get_user_by_email

ensure_auth_tables()

email = "fullname_smoke@example.com"
user = get_user_by_email(email)
if not user:
    user = create_user(
        email=email,
        password="testpass123",
        full_name="Full Name Smoke",
        company_name="Smoke Co",
        industry="Fintech",
    )

user = get_user_by_email(email)
assert user.get("full_name") == "Full Name Smoke", user
print("Full name smoke OK")
PY
```

Result:

- PASS: `Full name smoke OK`

## 8. Remaining limitations

- Full name is stored on `users`, not `user_profiles`.
- No profile editing UI for full name was added in this sprint.
- No delivery behavior changed.
- No Telegram behavior changed.
- Existing users remain compatible, but their `full_name` is `NULL` until updated through a future account settings flow.
