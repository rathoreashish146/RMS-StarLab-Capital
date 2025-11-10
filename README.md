# RMS (Resource Management System)

A role-based resource tracking web app built with **Dash + Flask**, **SQLAlchemy**, and **PostgreSQL**. It supports asset lifecycle management, request approvals, office/employee scoping, file uploads (bills/receipts), analytics, and remarks.

> This documentation is generated from the uploaded source for maintainers and contributors. It covers architecture, data model, roles/permissions, page behaviors, and operational guidance.

---

## 1) Quick Start

### 1.1. Requirements
- Python 3.10+
- PostgreSQL 13+ (or a managed instance)
- Packages pinned in `requirements.txt` (Dash, Flask, SQLAlchemy, pandas, gunicorn, psycopg2-binary)

### 1.2. Environment
Set the following environment variables as needed:

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy connection string | see `db.py` (Postgres URL)
| `RMS_SECRET` | Flask session secret key | `dev-secret-key` (development only)
| `RMS_UPLOAD_DIR` | Directory for uploaded bills | `uploads/`

> **Note:** In development you can keep defaults; in production, **always** set a strong `RMS_SECRET` and a managed PostgreSQL URL.

### 1.3. Install & Run (Dev)
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py  # starts Dash/Flask dev server
```
The app seeds the DB automatically on first run (see §6.4). Visit `http://localhost:8050/`.

### 1.4. Production (Gunicorn Example)
```bash
export RMS_SECRET='change-me'
export DATABASE_URL='postgresql://user:pass@host:5432/dbname'
export RMS_UPLOAD_DIR='/var/lib/rms/uploads'
# optional: pre-create upload dir with correct perms
mkdir -p "$RMS_UPLOAD_DIR" && chmod 750 "$RMS_UPLOAD_DIR"
# start
gunicorn -w 3 -b 0.0.0.0:8050 app:server
```

---

## 2) High-Level Architecture

```
+------------------------------+
|          Browser UI          |
|  Dash pages & components     |
+---------------+--------------+
                |
                v (HTTP)
+---------------+--------------+
|      Flask (Dash server)     |
|  - Auth via session cookie   |
|  - Dash callbacks (routes)   |
+---------------+--------------+
                |
                v (SQLAlchemy ORM)
+---------------+--------------+
|        PostgreSQL Database   |
|  offices, users, employees,  |
|  assets, requests, remarks   |
+------------------------------+
```

### Key Modules
- **`app.py`** — UI, routing, authentication, role-based logic, Dash callbacks, uploads.
- **`db.py`** — ORM models, enums, engine/session setup, seeding utilities.
- **`requirements.txt`** — runtime dependencies.

---

## 3) Roles & Permissions

### 3.1. Roles
- **GM (General Manager)**: Global admin scope — all offices, admin panel access, create OMs, reset OM passwords, company-wide reports.
- **OM (Office Manager)**: Office-scoped manager — manage employees for their office, approve/reject requests within office, view office assets & reports.
- **EMP (Employee)**: Self-scope — view own assets, raise requests, update own profile, view manager remarks.

### 3.2. Allocation Rules
- **GM** can create assets as **UNALLOCATED**, **OFFICE**, or **EMPLOYEE**.
- **OM** can create assets as **OFFICE** (auto to own office) or **EMPLOYEE** (limited to employees in own office). Cannot create **UNALLOCATED**.
- **EMP** can only add assets allocated to **self**.

### 3.3. Request Workflow
Statuses: `PENDING → APPROVED → RETURN_PENDING → RETURNED` or `REJECTED`.

Manager actions (GM/OM): **Approve**, **Reject**, **Return Pending**, **Returned** with hard guards, optional remarks, and automatic asset creation/return marking where applicable.

---

## 4) User Interface & Navigation

### 4.1. Pages
- **Login** — username/password; seeds DB if empty; on success sets `session["user_id"]`.
- **Dashboard** — role-specific KPIs (GM/OM), quick-start guides, metrics.
- **Assets** — create assets (with optional bill upload), table view filtered by role scope.
- **Requests** — submit new requests (EMP pre-selected), table with manager actions.
- **Reports** — analytics (GM: company + per-office + per-employee; OM: office + per-employee) and add **Remarks** to employees.
- **Employees** (OM only) — add employees (creates corresponding `User` with EMP role) and live table refresh.
- **Admin** (GM only) — create offices, create OMs, reset OM passwords.
- **Profile** — employee profile (name, phone) + **Manager Remarks** feed.

### 4.2. Visual Style
Pastel blue / glassmorphism theme, keyboard-friendly forms, accessible focus styles, status badges, and rich toasts.

---

## 5) Data Model

### 5.1. Enums
- `Role`: `GM`, `OM`, `EMP`
- `AllocationType`: `EMPLOYEE`, `OFFICE`, `UNALLOCATED`
- `RequestStatus`: `PENDING`, `APPROVED`, `REJECTED`, `RETURN_PENDING`, `RETURNED`

### 5.2. Tables

**`offices`**
- `id` (PK)
- `name` (unique, required)

**`users`**
- `id` (PK)
- `username` (unique, required)
- `password_hash` (required, Werkzeug PBKDF2)
- `role` (Enum[Role], required)
- `office_id` (FK→offices.id, nullable for GM)

**`employees`**
- `id` (PK)
- `name` (required)
- `office_id` (FK→offices.id)
- `phone` (nullable)
- `username` (unique nullable; links to `users.username` when present)

**`assets`**
- `id` (PK)
- `name` (required)
- `price` (float, default 0)
- `quantity` (int, default 1)
- `bill_path` (string, uploaded file path)
- `allocation_type` (Enum[AllocationType], default `UNALLOCATED`)
- `allocation_id` (int; employee_id or office_id depending on type)
- `returned` (bool, default False)

**`requests`**
- `id` (PK)
- `employee_id` (FK→employees.id)
- `office_id` (FK→offices.id)
- `asset_name` (required)
- `quantity` (default 1)
- `price` (float, optional)
- `bill_path` (string, optional)
- `status` (Enum[RequestStatus], default `PENDING`)
- `approver_user_id` (FK→users.id, nullable)
- `remark` (Text, nullable)
- `created_at` (UTC time)

**`remarks`**
- `id` (PK)
- `author_user_id` (FK→users.id)
- `target_type` (string: `EMPLOYEE` | `OFFICE` | `REQUEST` | `ASSET`)
- `target_id` (int)
- `content` (Text)
- `created_at` (UTC time)

### 5.3. Relationships (Conceptual)
- `Office` 1—N `Employee`, 1—N `User`
- `User` (role-scoped by `office_id` except GM)
- `Request` belongs to `Employee` + `Office`
- `Asset` allocation determined by `allocation_type` + `allocation_id`

---

## 6) Application Behavior

### 6.1. Authentication
- Login form checks `users.username` and `password_hash`.
- On first login attempt with empty DB, the app seeds data (see **6.4**).
- Session cookie stores `user_id`; `current_user()` fetches full `User` record per request.

### 6.2. Authorization
- `login_required(role=None)` decorator guards admin dropdown loaders and sensitive callbacks.
- Page router (`/`, `/assets`, `/requests`, `/reports`, `/employees`, `/admin`, `/profile`) renders login page for anonymous users, and role-specific pages otherwise.

### 6.3. Uploads
- Bills are uploaded through Dash `dcc.Upload`, saved into `RMS_UPLOAD_DIR` with a timestamped filename.
- Files are served via `GET /uploads/<path>` using `send_from_directory` (download as attachment).

### 6.4. Seeding
On a new database:
- Creates two offices (example names).
- Creates one **GM** user and two **OM** users.
- Creates multiple **EMP** users/employees per office with default passwords (`<username>@51020`).
> **Change these defaults in production** and/or remove the seeding path after initial provisioning.

### 6.5. Assets Page Workflow
- Validates name/price/quantity.
- Applies allocation rules by role.
- Optionally associates a `bill_path`.
- On success: success toast, input reset, and table refresh.
- Table columns: `id`, `name`, `price`, `qty`, `bill` (markdown link), `allocation`, `allocation_id`.

### 6.6. Requests Page Workflow
- EMP: `employee` is auto-selected/disabled.
- Managers: choose any (GM) or same-office (OM) employee.
- Submit validates `asset_name` and `qty` (≥1), optional price and file.
- Manager Actions with guards:
  - **Approve**: creates a matching `Asset` if one doesn’t exist; sets status `APPROVED`.
  - **Return Pending**: only valid from `APPROVED`.
  - **Returned**: marks matching asset `returned=True`.
  - **Reject**: deletes matched asset (if created by approval) and sets `REJECTED`.

### 6.7. Reports
- **GM**: company KPIs + per-office/employee dropdowns; add **Remarks** to employees.
- **OM**: office KPIs + per-employee analytics; add **Remarks**.

### 6.8. Employees (OM)
- Creates `Employee` + paired `User` (EMP role) with chosen password.
- Immediately refreshes the employees table after creation.

### 6.9. Profile (EMP)
- Displays role, employee id, and office.
- Edit **Full Name** and **Phone**; saves without modal.
- Shows **Manager Remarks** timeline addressed to the employee.

---

## 7) Security & Compliance

- **Passwords**: hashed using Werkzeug’s secure hash (PBKDF2). Never store plaintext. Enforce strong passwords in production.
- **Session secret**: set `RMS_SECRET` to a strong random string in production.
- **File uploads**: stored on disk with server-side generated names; consider restricting file types and scanning in production.
- **RBAC**: server-side checks in callbacks and query filters enforce scope.
- **Least privilege**: UI hides links by role, *and* server validates access.
- **Database URL**: treat as secret; use env-injected configuration and secret storage (e.g., AWS Parameter Store/Secrets Manager).

---

## 8) Deployment Notes

- **Gunicorn** behind a reverse proxy (Nginx/ALB) is recommended.
- **Static uploads**: persist `RMS_UPLOAD_DIR` (bind mount or durable volume).
- **Database migrations**: project uses “tiny migrations” for a few columns via `_safe_add_column(...)` at runtime. For production-grade changes, adopt Alembic migrations and CI gating.
- **Observability**: add access logs, request IDs, and SQL echo-off in prod; consider Sentry/OTel.
- **Scaling**: Dash/Flask are single-process per worker; scale horizontally with multiple workers and sticky sessions if needed.

---

## 9) Testing Strategy (Suggested)

- **Unit tests**: model validation, role guards, helpers (e.g., `_find_matching_asset`).
- **Callback tests**: use Dash testing (`dash[testing]`) to simulate UI interactions.
- **Integration tests**: seed a temporary DB, hit callback endpoints, verify table data and permissions.
- **Security tests**: direct-callback calls with wrong roles; file upload constraints; session tampering.

---

## 10) Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| Login always fails | Seed users missing | Ensure first login triggers seeding or run a manual seed.
| OM can’t see employees | Wrong `office_id` on `User` or `Employee` | Verify mappings; reseed or correct records.
| Upload links 404 | `RMS_UPLOAD_DIR` path or permissions | Create the directory and ensure the process can read it.
| Requests not updating | No row selected or guard prevents transition | Select a row and check status rules in manager panel.
| Company KPIs empty | Empty DB | Add assets/requests or seed.

---

## 11) Extensibility Roadmap

- Replace ad-hoc “tiny migrations” with Alembic.
- Add soft-deletes and audit trails (who changed what, when).
- Add pagination & filters to all tables.
- Add S3-backed upload storage and signed URLs.
- Add MFA and password reset flows.
- Add email/Slack notifications on approvals.
- Add CSV/Excel export from reports.

---

## 12) Reference Logins (from seed data)

> **For development only** — change/remove in production.
- GM: `faisal` / `faisal@51020`
- OMs: `mahtab` / `mahtab@51020`; `mahtab_ai` / `mahtab@51020`
- EMPs: `<username>` / `<username>@51020` (see seed lists)

---

## 13) Code Map (Selected Functions)

- **Auth & Session**: `current_user()`, `do_login()`
- **Routing**: `route(path)` → returns layout per path/role
- **Layouts**: `dashboard_layout()`, `assets_layout()`, `requests_layout()`, `reports_layout()`, `employees_layout()`, `admin_layout()`, `profile_layout()`
- **Assets**: `add_asset(...)`, `render_assets_table(...)`, `update_alloc_options(...)`
- **Requests**: `req_form(...)`, `create_request(...)`, `render_requests_table(...)`, `handle_request_action(...)`
- **Reports**: `render_reports(...)`, `per_office_kpis(...)`, `per_employee_kpis(...)`, `add_remark(...)`
- **Employees**: `_render_emp_table_for_om(...)`, `list_employees(...)`, `add_employee(...)`
- **Admin**: `load_admin_dropdowns(...)`, `add_office(...)`, `create_om(...)`, `reset_om_password(...)`
- **Profile**: `load_profile(...)`, `save_profile(...)`

---

## 14) Glossary
- **Asset**: Any resource (e.g., laptop, desk) optionally with an attached bill.
- **Request**: A request by an employee for an asset; managers update lifecycle.
- **Remark**: Manager-authored note attached to employees (or other targets in future).
- **Allocation**: Where an asset is assigned (office vs. specific employee).

---

## 15) License & Ownership
Internal STARlab Capital application. Consult your legal team for licensing and redistribution policies.

