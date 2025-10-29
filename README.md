# Resource Management System (Dash)

This is a minimal Resource/Asset Management System built with **Dash (Plotly)** + **SQLite**.
It implements the architecture from your PDF:
- Roles: General Manager (GM), Office Manager (OM), Employee (EMP)
- Assets: name, price/value, bill attachment (image/pdf), allocation target (Employee/Office)
- Requests: employees create requests (with quantity); managers approve/reject; return workflow
- Views and reports scoped by role (office vs entire company)
- Admin panel for user/office/employee management

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
python app.py
# open http://127.0.0.1:8050
```

Default credentials (change after first login):
- Admin (GM): **admin / admin**
- Office Manager (East): **om_east / om_east**
- Employee (Alice): **alice / alice**

Uploads (bills) are saved into `uploads/`.

## Notes
- This is an MVP; extend permissions, validations, and UI as needed.
- The database file `rms.db` is created on first run with seed data.
