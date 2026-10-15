# Multi-Tenant Event & Ticket Reservation System (EventHub)

A full-stack, enterprise-grade web application where multiple event organizers can create and manage events, configure tiered ticket categories, and sell tickets to attendees with real-time concurrency protection, guaranteed 10-minute holds, and zero double-booking.

---

## 🚀 Key Features

- **Multi-Tenant Architecture**: Supports three distinct user roles:
  - **Admin**: Platform oversight, user/role management, event moderation, transaction audit logs, and global analytics.
  - **Organizer**: Event creation, ticket tier configuration, sales cutoff controls, and live Chart.js revenue & conversion dashboards.
  - **Attendee**: Public discovery, interactive ticket selection, 10-minute reservation holds, simulated checkout, and booking receipts.
- **Ticket Reservation Engine**:
  - Employs **PostgreSQL `SELECT FOR UPDATE`** row-level locking with deterministic ID ordering to eliminate deadlocks.
  - Enforces the strict inventory invariant at database and ORM levels:
    $$\text{total\_quantity} = \text{available\_quantity} + \text{held\_quantity} + \text{sold\_quantity}$$
- **10-Minute Reservation Hold**:
  - Server-synchronized countdown timer with automatic state transition.
  - Background expiration cleanup worker idempotently releases expired holds back to the available inventory.
- **Asynchronous Mock Payment Gateway**:
  - Endpoint `POST /api/payments/mock` with idempotency key protection against duplicate callbacks.
  - Deterministic simulation outcomes (`SUCCESS` / `FAILED`) for reliable automated testing.
- **Redis Caching**:
  - High-performance caching for published events and details with automatic invalidation.
  - Robust error handling: automatically falls back to direct database queries if Redis is offline.
- **Analytics Dashboard**:
  - Visualized with **Chart.js**: 14-day revenue & sales trend line chart, sales by ticket category doughnut chart, and real-time conversion rates.
  - Conversion rate business formula:
    $$\text{Conversion Rate} = \frac{\text{Confirmed Reservations}}{\text{Total Reservations Created}} \times 100$$
- **Production-Ready Deployment**:
  - Pre-configured `render.yaml` blueprint, `Procfile`, and Gunicorn WSGI startup.

---

## 🛠 Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons, Chart.js
- **Backend**: Python 3.14+, Flask (Application Factory & Blueprints), Flask-Login, Flask-WTF (CSRF Protection)
- **Database**: PostgreSQL (with psycopg v3 binary), SQLAlchemy ORM 2.0+, Flask-Migrate / Alembic
- **Caching**: Redis
- **Background Tasks**: Celery with Redis broker (plus fallback in-process scheduler thread for dev environments)
- **Testing**: pytest (21 comprehensive tests including concurrency simulation)
- **API Testing**: Postman Collection (20 test requests)
- **Deployment**: Gunicorn, Render Blueprint (`render.yaml`)

---

## 📦 Project Structure

```
event-ticket-system/
├── app/
│   ├── __init__.py           # Flask Application Factory & Error Handlers
│   ├── models.py             # 9 Relational Entities & Check Constraints
│   ├── extensions.py         # SQLAlchemy, Migrate, LoginManager, CSRF, Redis Wrapper
│   ├── celery_utils.py       # Celery configuration with Flask Task context
│   ├── auth/                 # Authentication Blueprint & RBAC decorators
│   ├── events/               # Event Management & Ticket Tiers Blueprint
│   ├── reservations/         # 10-Minute Hold Reservation Blueprint
│   ├── payments/             # Mock Payment Gateway & Checkout Blueprint
│   ├── analytics/            # Organizer & Admin Chart.js Analytics Blueprint
│   ├── admin/                # Platform Governance & Moderation Blueprint
│   ├── services/             # Core Business Logic (Reservation, Payment, Cache, Analytics)
│   ├── tasks/                # Celery Background Tasks (Auto-cleanup & Payments)
│   ├── templates/            # Jinja2 HTML5 Templates (Bootstrap 5)
│   └── static/               # CSS styles & client-side JavaScript
├── tests/                    # 21 Automated pytest tests (concurrency, auth, payments...)
├── docs/                     # System architecture, ER diagram, database schema, API docs
├── postman/                  # 20-Request Postman Collection
├── config.py                 # Development, Testing, and Production Config
├── run.py                    # Application Runner & Management CLI
├── render.yaml               # Render Infrastructure as Code Blueprint
├── Procfile                  # Production Process Definitions
├── requirements.txt          # Pinned Python Dependencies
└── .env.example              # Environment Variable Template
```

---

## ⚙️ Local Setup Instructions

### 1. Clone & Initialize Environment
```bash
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Default configuration supports PostgreSQL:
```ini
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/event_ticket_db
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
RESERVATION_HOLD_SECONDS=600
```
*(If local PostgreSQL/Redis servers are not running on your workstation, the application automatically falls back to local SQLite and direct DB querying without breaking).*

### 3. Initialize & Seed Database
```bash
# Seed initial demo organizers, events, and ticket categories
flask seed-data

# Or create a custom administrator account:
flask create-admin --email=admin@eventhub.com --password=AdminPass123! --name="Platform Admin"
```

### 4. Run the Application
```bash
python run.py
```
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your browser.

---

## 🏃 Background Processing & Celery

To run the background worker for production or local environments with Redis:
```bash
# Start Celery Worker
celery -A run.celery worker --loglevel=info

# Start Celery Periodic Beat Scheduler
celery -A run.celery beat --loglevel=info
```
*(Note: In local development without Celery, an automatic background thread monitor starts on server launch to release expired holds).*

---

## 🧪 Running Automated Tests

Run the complete 21-test pytest suite:
```bash
.\.venv\Scripts\python.exe -m pytest -v
```

### Verified Test Results:
```text
tests/test_analytics.py::test_organizer_analytics_and_conversion_rate PASSED
tests/test_analytics.py::test_organizer_cannot_access_other_organizers_analytics PASSED
tests/test_analytics.py::test_admin_platform_analytics PASSED
tests/test_auth.py::test_user_registration_success PASSED
tests/test_auth.py::test_admin_registration_rejected PASSED
tests/test_auth.py::test_duplicate_registration_rejected PASSED
tests/test_auth.py::test_login_success_and_me PASSED
tests/test_auth.py::test_login_invalid_password PASSED
tests/test_auth.py::test_unauthenticated_protected_route PASSED
tests/test_concurrency.py::test_concurrent_reservation_prevent_double_booking PASSED
tests/test_events.py::test_organizer_create_event_success PASSED
tests/test_events.py::test_sales_cutoff_validation PASSED
tests/test_events.py::test_organizer_cannot_modify_other_organizers_event PASSED
tests/test_events.py::test_public_events_listing PASSED
tests/test_payments.py::test_payment_success_moves_held_to_sold PASSED
tests/test_payments.py::test_payment_failure_releases_inventory PASSED
tests/test_payments.py::test_duplicate_callback_idempotency PASSED
tests/test_reservations.py::test_create_reservation_and_inventory_hold PASSED
tests/test_reservations.py::test_insufficient_inventory_returns_409 PASSED
tests/test_reservations.py::test_cancel_reservation_releases_inventory PASSED
tests/test_reservations.py::test_expired_reservation_cleanup_idempotent PASSED

======================= 21 passed in 15.40s =======================
```

---

## 🔑 Demo Login Accounts

| Role | Email | Password | Dashboard Features |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@eventhub.com` | `AdminPass123!` | User moderation, event toggles, transaction logs, global analytics |
| **Organizer** | `organizer@techconf.org` | `OrganizerPass123!` | Create/edit events, ticket categories, Chart.js analytics |
| **Attendee** | `attendee@example.com` | `AttendeePass123!` | Event browsing, 10-minute hold reservation, checkout simulation |

---

## 📮 Postman Collection
Import `postman/event_ticket_booking.postman_collection.json` into Postman to run all 20 API requests with automated test assertions.
