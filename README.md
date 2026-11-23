# SecurityGuys
SecurityGuys is a mock medical patient portal with two versions, an insecure and a secure version.

The `backend/` directory stores an intentionally non-compliant with GDPR/CCPA/CPRA codebase. Every violation is deliberate and annotated in `backend/models.py` with the article or section it breaks. Do not deploy or enter real personal data. This version runs on port 8000.

The `secure_backend/` directory stores a compliant version.

## OS Requirements
Any OS that runs Python 3.10+ which includes macOS, Windows 10/11, or Linux.

## Programming Languages
- Python 3.10+ (both backends)
- HTML/CSS/JavaScript (frontend, no build step)

## Required Software and Dependencies
- Python 3.10 or newer
- Git to clone the repo
- Python packages (installed in step 4 below):
  - FastAPI: web framework
  - Uvicorn: ASGI server
  - SQLAlchemy/aiosqlite: ORM and async SQLite driver
  - FastCRUD: auto-generated CRUD endpoints (insecure version)
  - Pydantic: request validation
  - argon2-cffi: Argon2id password hashing (secure version)
  - cryptography: Fernet field encryption (secure version)
  - PyJWT: signed session tokens (secure version)

SQLite is used as the database (included with Python.)

## Installation
1. Clone the repo and enter it:
   ```bash
   git clone https://github.com/teaBag024/SecurityGuys
   cd SecurityGuys
   ```
2. In the root directory of the project, create a venv:
   ```bash
   python3 -m venv .venv
   ```
3. Activate it:
   - macOS/Linux: `source .venv/bin/activate`
   - Windows: `.venv\Scripts\activate`
4. Install dependencies (this installs everything for both versions):
   ```bash
   pip install -r secure_backend/requirements.txt
   ```

## Running the Insecure Version
The server must be started from inside `backend/` (the database path is relative to it):
```bash
cd backend
uvicorn main:app --reload
```

- The API runs at http://127.0.0.1:8000
- API docs are at http://127.0.0.1:8000/docs
- On first run, an SQLite database is created at `backend/app.db`. To reset all data, delete this file. If you ran an older version of the project, delete `backend/app.db` first, as the tables changed and the old file will cause errors.

### Insecure endpoints
(Method - Description)
GET /health - health check
POST /signup - create user with everything stored in plaintext and printed to console
POST/GET/PATCH/DELETE /users, /users/{id} - user CRUD with no auth
POST/GET/PATCH/DELETE /appointments, /appointments/{id} - appointments CRUD with no auth
POST/GET/PATCH/DELETE /prescriptions, /prescriptions/{id} - prescriptions CRUD with no auth

## Running the Secure Version
In a second terminal with venv activated:
```bash
cd secure_backend
uvicorn main:app --port 8001
# in another terminal:
python seed.py # create the demo accounts below (run once)
```

- Application portal (web page): http://127.0.0.1:8001
- API docs: http://127.0.0.1:8001/docs
- Data is stored in `secure_backend/secure_app.db`, delete to reset.
- On first run, random encryption and signing keys are generated in `secure_backend/.secrets.json` which are gitignored, deleting that file makes the existing database unreadable, so delete both together. You can also provide `FIELD_ENCRYPTION_KEY`, `BLIND_INDEX_KEY` and `JWT_SECRET` as env variables.

### Secure endpoints
(Method - Who is allowed to access - Description)
GET / - anyone - web page
POST /api/signup - anyone - create account with email, first/last name, password, terms consent, optional newsletter
POST /api/login - anyone - returns a session token that expires after 30 minutes
POST /api/logout - logged in - logs out (the web page deletes its token)
GET /api/me - logged in - view your profile
PUT /api/me - logged in - correct your email, name, or newsletter choice
PUT /api/me/privacy - logged in - turn "Do Not Sell or Share" and "Limit Sensitive Info" on or off
DELETE /api/me - logged in - permanently delete your account and all your data
GET /api/doctors - logged in - list doctors
GET /api/doctors/{id}/slots?date= - logged in - free time slots for a doctor on a date
GET /api/appointments - logged in - list your own appointments
POST /api/appointments - logged in - book an appointment
DELETE /api/appointments/{id} - logged in - cancel your own appointment (someone else's appointments returns 404)
GET /api/prescriptions - logged in - list your own prescriptions

### Security controls in the secure version
(Control - Where)
passwords hashed with Argon2id, common passwords rejected - `security.py`, `main.py`
names, email, appointment reasons, and prescriptions encrypted with fernet - `security.py`, `models.py`
email looked up with HMAC index and not plaintext - `security.py`
signed JWT login tokens which expire after 30 minutes - `security.py`, `main.py`
every protected route checks the token and user id comes from the token - `main.py` (`get_current_user`)
users can only see and change their own data - `main.py`
account locked for 15 minutes after 5 wrong passwords - `main.py` (`login`)
same error for wrong password and unknown email - `main.py` (`login`)
unknown fields such as `ssn` or `role` rejected with 422 - `schemas.py`
terms must be accepted, newsletter off by default, time of acceptance saved - `schemas.py`, `models.py`
deleting an account deletes the user's appointments and prescriptions (ON DELETE CASCADE) - `models.py`, `database.py`
nothing personal printed to the server console, errors return no stack traces - `main.py`

## Login Credentials for Testing
### Insecure version
No accounts are pre-seeded. Create one with `/signup` from the `/docs` page or with curl:

```bash
curl -X POST http://127.0.0.1:8000/signup \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Test User",
    "email": "test@example.com",
    "password": "password123",
    "ssn": "123-45-6789",
    "date_of_birth": "1990-01-01",
    "address": "123 Main St",
    "phone": "555-666-7777",
    "medical_history": "None",
    "credit_card_number": "4111111111111111"
  }'
```

### Secure version: example credentials are created by `python seed.py` (you need to start the server once first so the tables exist)

user: patient@example.com
password: DemoPatient#2026
This creates demo patient John Doe with one appointment and one prescription

You can also create a new account with POST `/api/signup` from http://127.0.0.1:8001/docs. To use the protected endpoints in `/docs`, log in with POST `/api/login`, copy the `token`, click **Authorize**, and paste it in.

## Limitations & Incomplete Features (Due to outside of our scope)
- Logout does not invalidate the token, the token stays valid until it expires after 30 minutes.
- There is no audit log, so actions like logins and account deletions are not recorded (no non repudiation).
- The login lockout is stored in memory so it resets when the server restarts.
- Encryption and signing keys are stored in `secure_backend/.secrets.json` on the same machine as the database, a real deployment would use a key management service.
- There are no doctor or admin accounts, prescriptions can only be created by `seed.py`, not through the API.
- The web page only uses the real backend when opened at http://127.0.0.1:8001. If `frontend/newWebpage.html` is opened directly as a file it runs in frontend demo mode.