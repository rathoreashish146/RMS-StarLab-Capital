from sqlalchemy.orm import joinedload
from sqlalchemy import text
import os, io, datetime
from functools import wraps

import dash
from dash import Dash, html, dcc, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
import pandas as pd
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session, send_from_directory

from db import (
    init_db, SessionLocal, Role, AllocationType, RequestStatus,
    Office, User, Employee, Asset, Request, Remark,
)

# --- Try to add phone column if missing (safe on SQLite) ---
try:
    from db import engine as _engine  # type: ignore
    with _engine.connect() as conn:  # type: ignore
        cols = conn.execute(text("PRAGMA table_info(employees)")).fetchall()
        names = {c[1] for c in cols}
        if "phone" not in names:
            conn.execute(text("ALTER TABLE employees ADD COLUMN phone VARCHAR"))
except Exception:
    pass

UPLOAD_FOLDER = os.environ.get("RMS_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize DB
if not os.path.exists("rms.db"):
    init_db(seed=True)
else:
    init_db(seed=False)

# Dash app (CDN assets to avoid renderer path issues on Render)
app = Dash(__name__, suppress_callback_exceptions=True, serve_locally=False)
server = app.server
server.secret_key = os.environ.get("RMS_SECRET", "dev-secret-key")

# ---------- Helpers ----------
def current_user():
    if "user_id" not in session:
        return None
    with SessionLocal() as s:
        u = s.query(User).options(joinedload(User.office)).get(session["user_id"])
        if not u:
            return None
        _ = u.office.name if u.office else None
        return u

def _employee_for_user(user, s):
    if not user or not user.office_id:
        return None
    employees = s.query(Employee).filter(Employee.office_id == user.office_id).all()
    if not employees:
        return None
    uname = (user.username or "").strip().lower()
    match = next((e for e in employees if (e.name or "").strip().lower() == uname), None)
    return match or employees[0]

def login_required(role: Role | None = None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            user = current_user()
            if not user:
                raise PreventUpdate
            if role and user.role != role:
                raise PreventUpdate
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def role_name(role):
    return {"GM": "General Manager", "OM": "Office Manager", "EMP": "Employee"}[role]

# ---------- Layouts ----------
def navbar():
    user = current_user()
    if not user:
        return html.Nav([])
    if user.role == Role.EMP:
        items = [
            dcc.Link("My Assets", href="/assets"),
            html.Span(" | "),
            dcc.Link("Requests", href="/requests"),
            html.Span(" | "),
            dcc.Link("My Profile", href="/profile"),
            html.Span(" | "),
            dcc.Link("Logout", href="/logout"),
        ]
        return html.Nav(items, style={"marginBottom": "10px"})
    items = [
        dcc.Link("Dashboard", href="/"),
        html.Span(" | "),
        dcc.Link("Assets", href="/assets"),
        html.Span(" | "),
        dcc.Link("Requests", href="/requests"),
        html.Span(" | "),
        dcc.Link("Reports", href="/reports"),
        html.Span(" | "),
        dcc.Link("Admin", href="/admin"),
        html.Span(" | "),
        dcc.Link("Logout", href="/logout")
    ]
    return html.Nav(items, style={"marginBottom": "10px"})

def login_layout():
    return html.Div([
        html.H2("Resource Management System — Login"),
        dcc.Input(id="login-username", placeholder="Username"),
        dcc.Input(id="login-password", type="password", placeholder="Password"),
        html.Button("Login", id="login-btn"),
        html.Div(id="login-msg", style={"color": "crimson", "marginTop": "8px"}),
        html.Hr(),
        html.Div("Default demo users: admin/admin, om_east/om_east, alice/alice")
    ], style={"maxWidth": "480px"})

def dashboard_layout():
    user = current_user()
    if not user:
        return login_layout()
    if user.role == Role.EMP:
        return assets_layout()
    scope = "Company-wide" if user.role == Role.GM else f"Office: {user.office.name if user.office else 'N/A'}"
    return html.Div([
        navbar(),
        html.H3(f"Dashboard — {role_name(user.role.value)} ({scope})"),
        html.Div(id="dashboard-cards"),
    ])

def _uploader_component():
    return dcc.Upload(
        id='upload-bill',
        children=html.Button("Upload Bill / Drag & Drop"),
        multiple=False,
        style={
            "border": "2px dashed #bbb",
            "borderRadius": "10px",
            "padding": "12px",
            "display": "inline-block",
            "cursor": "pointer",
            "marginBottom": "8px"
        }
    )

def assets_layout():
    user = current_user()
    if not user:
        return login_layout()
    if user.role == Role.EMP:
        return html.Div([
            navbar(),
            html.H3("My Assets"),
            _uploader_component(),
            dcc.Input(id="asset-name", placeholder="Asset name *"),
            dcc.Input(id="asset-price", placeholder="Price *", type="number"),
            dcc.Input(id="asset-qty", placeholder="Quantity *", type="number", value=1),
            html.Button("Add to My Profile", id="add-asset-btn"),
            html.Div(id="asset-add-msg", style={"color":"crimson", "marginTop":"6px"}),
            dcc.ConfirmDialog(id="asset-dialog"),
            html.Hr(),
            html.H4("My Assets Table"),
            html.Div(id="assets-table")
        ])
    return html.Div([
        navbar(),
        html.H3("Assets"),
        _uploader_component(),
        dcc.Input(id="asset-name", placeholder="Asset name *"),
        dcc.Input(id="asset-price", placeholder="Price *", type="number"),
        dcc.Input(id="asset-qty", placeholder="Quantity *", type="number", value=1),
        html.Button("Add Asset", id="add-asset-btn"),
        html.Div(id="asset-add-msg", style={"color":"crimson", "marginTop":"6px"}),
        dcc.ConfirmDialog(id="asset-dialog"),
        html.Hr(),
        html.H4("Assets Table"),
        html.Div(id="assets-table")
    ])

def requests_layout():
    user = current_user()
    if not user:
        return login_layout()
    return html.Div([
        navbar(),
        html.H3("Requests"),
        html.Div(id="request-form"),
        dcc.ConfirmDialog(id="req-dialog"),     # <-- popup for requests
        html.Hr(),
        html.H4("Open Requests"),
        html.Div(id="requests-table")
    ])

def reports_layout():
    user = current_user()
    if not user:
        return login_layout()
    if user.role == Role.EMP:
        return html.Div([navbar(), html.Div("Reports are not available for Employees.")])
    return html.Div([navbar(), html.H3("Reports"), html.Div(id="reports-content")])

def profile_layout():
    user = current_user()
    if not user:
        return login_layout()
    return html.Div([
        navbar(),
        html.H3("My Profile"),
        html.Div(id="profile-form"),
        dcc.ConfirmDialog(id="profile-dialog"),
        html.Div(id="profile-msg", style={"color":"crimson", "marginTop":"6px"}),
    ])

def admin_layout():
    user = current_user()
    if not user:
        return login_layout()
    if user.role != Role.GM:
        return html.Div([navbar(), html.Div("Admins only.")])
    return html.Div([
        navbar(),
        html.H3("Admin Panel"),
        dcc.Input(id="new-office-name", placeholder="Office name"),
        html.Button("Add Office", id="btn-add-office"),
        html.Div(id="msg-add-office", style={"marginTop": "6px"}),
        html.Hr(),
        html.H4("Create User"),
        dcc.Dropdown(id="user-role", options=[
            {"label": "General Manager", "value": "GM"},
            {"label": "Office Manager", "value": "OM"},
            {"label": "Employee", "value": "EMP"}], placeholder="Role"),
        dcc.Input(id="user-username", placeholder="Username"),
        dcc.Input(id="user-password", placeholder="Password"),
        dcc.Dropdown(id="user-office", placeholder="Office (optional)"),
        html.Button("Create User", id="btn-add-user"),
        html.Div(id="msg-add-user", style={"marginTop": "6px"}),
        html.Hr(),
        html.H4("Employees"),
        dcc.Input(id="emp-name", placeholder="Employee name"),
        dcc.Dropdown(id="emp-office", placeholder="Office"),
        html.Button("Add Employee", id="btn-add-emp"),
        html.Div(id="msg-add-emp", style={"marginTop": "6px"}),
        html.Hr(),
        html.Div(id="admin-tables")
    ])

app.layout = html.Div([
    dcc.Location(id="url"),
    html.Div(id="page-content")
])

# ---------- Routes ----------
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def route(path):
    user = current_user()
    if path == "/logout":
        session.clear()
        return login_layout()
    if not user:
        return login_layout()
    if path == "/" or path is None:
        return dashboard_layout()
    if path == "/assets":
        return assets_layout()
    if path == "/requests":
        return requests_layout()
    if path == "/reports":
        return reports_layout()
    if path == "/admin":
        return admin_layout()
    if path == "/profile":
        return profile_layout()
    return html.Div([navbar(), html.H3("Not Found")])

# ---------- Login ----------
@app.callback(Output("login-msg", "children"), Input("login-btn", "n_clicks"),
              State("login-username", "value"), State("login-password", "value"),
              prevent_initial_call=True)
def do_login(n, username, password):
    uname = (username or "").strip()
    pwd = (password or "")
    with SessionLocal() as s:
        u = s.query(User).filter(User.username == uname).first()
        if not u and s.query(User).count() == 0:
            s.close()
            init_db(seed=True)
            with SessionLocal() as s2:
                u = s2.query(User).filter(User.username == uname).first()
        if not u or not check_password_hash(u.password_hash, pwd):
            return "Invalid credentials"
        session["user_id"] = u.id
        return dcc.Location(href="/", id="redir")

# ---------- Dashboard (GM/OM only) ----------
@app.callback(Output("dashboard-cards", "children"), Input("url", "pathname"))
def load_kpis(_):
    user = current_user()
    if not user:
        raise PreventUpdate
    if user.role == Role.EMP:
        return html.Div()
    with SessionLocal() as s:
        if user.role == Role.GM:
            total_assets_cost = sum(a.price * a.quantity for a in s.query(Asset).all())
        else:
            assets = s.query(Asset).filter(
                ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
                ((Asset.allocation_type == AllocationType.EMPLOYEE) &
                 (Asset.allocation_id.in_([e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)])))
            ).all()
            total_assets_cost = sum(a.price * a.quantity for a in assets)
        cards = [
            html.Div([html.H4("Total Asset Cost"), html.H3(f"${total_assets_cost:,.2f}")],
                     style={"padding": "10px", "border": "1px solid #eee",
                            "borderRadius": "10px", "display": "inline-block", "marginRight": "10px"})
        ]
        return html.Div(cards)

# ---------- Assets CRUD ----------
@app.callback(
    Output("asset-add-msg", "children"),
    Output("assets-table", "children", allow_duplicate=True),
    Output("asset-dialog", "message"),
    Output("asset-dialog", "displayed"),
    Output("asset-name", "value"),
    Output("asset-price", "value"),
    Output("asset-qty", "value"),
    Output("upload-bill", "contents"),
    Input("add-asset-btn", "n_clicks"),
    State("asset-name", "value"), State("asset-price", "value"), State("asset-qty", "value"),
    State("upload-bill", "contents"), State("upload-bill", "filename"),
    prevent_initial_call=True
)
def add_asset(n, name, price, qty, contents, filename):
    user = current_user()
    if not user:
        raise PreventUpdate

    name = (name or "").strip()
    try:
        price_val = float(price)
    except Exception:
        price_val = 0.0
    try:
        qty_val = int(qty or 0)
    except Exception:
        qty_val = 0

    if not name:
        return ("Asset name is required.", render_assets_table(), "", False, name, price, qty, contents)
    if price_val <= 0:
        return ("Price must be greater than 0.", render_assets_table(), "", False, name, price, qty, contents)
    if qty_val < 1:
        return ("Quantity must be at least 1.", render_assets_table(), "", False, name, price, qty, contents)

    saved_path = None
    if contents and filename:
        import base64
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
        saved_path = os.path.join(UPLOAD_FOLDER, fname)
        with open(saved_path, "wb") as f:
            f.write(decoded)

    with SessionLocal() as s:
        if user.role == Role.EMP:
            emp = _employee_for_user(user, s)
            if not emp:
                return ("No employee profile found for you.", render_assets_table(), "", False, name, price, qty, contents)
            a = Asset(
                name=name,
                price=price_val,
                quantity=qty_val,
                bill_path=saved_path,
                allocation_type=AllocationType.EMPLOYEE,
                allocation_id=emp.id
            )
            s.add(a); s.commit()
            return ("", render_assets_table(), "Asset added to your profile.", True, "", "", 1, None)

        a = Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path)
        s.add(a); s.commit()
    return ("", render_assets_table(), "Asset added.", True, "", "", 1, None)

def _bill_link(a):
    if not a.bill_path:
        return ""
    base = os.path.basename(a.bill_path)
    # markdown link for DataTable
    return f"[{base}](/uploads/{base})"

@app.callback(Output("assets-table", "children"), Input("url", "pathname"))
def render_assets_table(_=None):
    user = current_user()
    if not user:
        raise PreventUpdate
    with SessionLocal() as s:
        if user.role == Role.EMP:
            emp = _employee_for_user(user, s)
            assets = [] if not emp else s.query(Asset).filter(
                Asset.allocation_type == AllocationType.EMPLOYEE,
                Asset.allocation_id == emp.id
            ).all()
            rows = []
            for i, a in enumerate(assets, start=1):
                rows.append({
                    "asset_no": i,
                    "name": a.name, "price": a.price, "qty": a.quantity,
                    "bill": _bill_link(a),
                })
            cols = [
                {"name":"asset_no","id":"asset_no"},
                {"name":"name","id":"name"},
                {"name":"price","id":"price"},
                {"name":"qty","id":"qty"},
                {"name":"bill","id":"bill","presentation":"markdown"},  # clickable
            ]
            return dash_table.DataTable(data=rows, columns=cols, page_size=10, style_table={"overflowX":"auto"})
        else:
            assets = s.query(Asset).all()
            rows = [{
                "id": a.id, "name": a.name, "price": a.price, "qty": a.quantity,
                "bill": _bill_link(a),
                "allocation": a.allocation_type.value,
                "allocation_id": a.allocation_id
            } for a in assets]
            cols = [
                {"name":"id","id":"id"},
                {"name":"name","id":"name"},
                {"name":"price","id":"price"},
                {"name":"qty","id":"qty"},
                {"name":"bill","id":"bill","presentation":"markdown"},  # clickable
                {"name":"allocation","id":"allocation"},
                {"name":"allocation_id","id":"allocation_id"},
            ]
            return dash_table.DataTable(data=rows, columns=cols, page_size=10, style_table={"overflowX":"auto"})

@server.route("/uploads/<path:path>")
def serve_file(path):
    return send_from_directory(UPLOAD_FOLDER, path, as_attachment=True)

# ---------- Requests ----------
@app.callback(Output("request-form", "children"), Input("url", "pathname"))
def req_form(_):
    user = current_user()
    if not user:
        raise PreventUpdate
    with SessionLocal() as s:
        if user.role == Role.EMP:
            emp = _employee_for_user(user, s)
            options = [{"label": emp.name, "value": emp.id}] if emp else []
            return html.Div([
                html.H4("Create Request"),
                dcc.Dropdown(id="req-employee", options=options,
                             value=(emp.id if emp else None),
                             disabled=True,
                             placeholder="Employee"),
                dcc.Input(id="req-asset-name", placeholder="Asset name"),
                dcc.Input(id="req-qty", type="number", value=1),
                html.Button("Submit Request", id="req-submit", type="button", n_clicks=0),
                html.Div(id="req-msg", style={"marginTop": "6px", "color":"crimson"})
            ])
        else:
            employees = s.query(Employee).all() if user.role == Role.GM else \
                        s.query(Employee).filter(Employee.office_id == user.office_id).all()
            options = [{"label": e.name, "value": e.id} for e in employees]
            return html.Div([
                html.H4("Create Request"),
                dcc.Dropdown(id="req-employee", options=options, placeholder="Employee"),
                dcc.Input(id="req-asset-name", placeholder="Asset name"),
                dcc.Input(id="req-qty", type="number", value=1),
                html.Button("Submit Request", id="req-submit", type="button", n_clicks=0),
                html.Div(id="req-msg", style={"marginTop": "6px", "color":"crimson"})
            ])

@app.callback(
    Output("req-msg", "children"),
    Output("requests-table", "children", allow_duplicate=True),
    Output("req-dialog","message"),
    Output("req-dialog","displayed"),
    Output("req-asset-name","value"),
    Output("req-qty","value"),
    Input("req-submit", "n_clicks"),
    State("req-employee", "value"),
    State("req-asset-name", "value"),
    State("req-qty", "value"),
    prevent_initial_call=True
)
def create_request(n, emp_id, asset_name, qty):
    user = current_user()
    if not user:
        raise PreventUpdate
    if not n or n < 1:
        raise PreventUpdate

    asset_name = (asset_name or "").strip()
    try:
        qty = int(qty or 0)
    except Exception:
        qty = 0
    if not asset_name:
        return "Please enter an asset name.", render_requests_table(), "", False, asset_name, qty
    if qty < 1:
        return "Quantity must be at least 1.", render_requests_table(), "", False, asset_name, qty

    with SessionLocal() as s:
        if user.role == Role.EMP and not emp_id:
            emp = _employee_for_user(user, s)
            emp_id = emp.id if emp else None
        if not emp_id:
            return "Select an employee.", render_requests_table(), "", False, asset_name, qty

        emp = s.get(Employee, emp_id)
        if not emp:
            return "Invalid employee.", render_requests_table(), "", False, asset_name, qty
        if user.role == Role.OM and emp.office_id != user.office_id:
            return "You can only submit requests for your office.", render_requests_table(), "", False, asset_name, qty

        r = Request(
            employee_id=emp.id,
            office_id=emp.office_id,
            asset_name=asset_name,
            quantity=qty
        )
        s.add(r)
        s.commit()

    # success -> popup + clear fields
    return "", render_requests_table(), "Request submitted.", True, "", 1

@app.callback(Output("requests-table", "children"), Input("url", "pathname"))
def render_requests_table(_=None):
    user = current_user()
    if not user:
        raise PreventUpdate
    with SessionLocal() as s:
        q = s.query(Request)
        if user.role == Role.OM:
            q = q.filter(Request.office_id == user.office_id)
        elif user.role == Role.EMP:
            emp = _employee_for_user(user, s)
            q = q.filter(Request.employee_id == emp.id) if emp else q.filter(Request.id == -1)
        rows = q.order_by(Request.created_at.desc()).all()
        data = [{
            "id": r.id, "employee_id": r.employee_id, "office_id": r.office_id, "asset": r.asset_name,
            "qty": r.quantity, "status": r.status.value, "remark": r.remark or "", "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
        } for r in rows]
    cols = [{"name": n, "id": n} for n in ["id", "employee_id", "office_id", "asset", "qty", "status", "remark", "created_at"]]

    user = current_user()
    controls = html.Div([
        dcc.Textarea(id="mgr-remark", placeholder="Remark…", style={"width": "100%", "height": "60px"}),
        html.Button("Approve", id="btn-approve"),
        html.Button("Reject", id="btn-reject"),
        html.Button("Mark Return Pending", id="btn-return-pending"),
        html.Button("Mark Returned", id="btn-returned"),
        html.Div(id="req-action-msg", style={"marginTop": "6px"})
    ]) if user and user.role in (Role.GM, Role.OM) else html.Div()

    return html.Div([
        dash_table.DataTable(data=data, columns=cols, id="req-table", row_selectable="single", page_size=10),
        controls
    ])

@app.callback(Output("req-action-msg", "children", allow_duplicate=True),
              Input("btn-approve", "n_clicks"),
              State("req-table", "selected_rows"), State("req-table", "data"),
              State("mgr-remark", "value"), prevent_initial_call=True)
def approve_req(n, selected, data, remark):
    return handle_request_update(selected, data, remark, RequestStatus.APPROVED)

@app.callback(Output("req-action-msg", "children", allow_duplicate=True),
              Input("btn-reject", "n_clicks"),
              State("req-table", "selected_rows"), State("req-table", "data"),
              State("mgr-remark", "value"), prevent_initial_call=True)
def reject_req(n, selected, data, remark):
    return handle_request_update(selected, data, remark, RequestStatus.REJECTED)

@app.callback(Output("req-action-msg", "children", allow_duplicate=True),
              Input("btn-return-pending", "n_clicks"),
              State("req-table", "selected_rows"), State("req-table", "data"),
              State("mgr-remark", "value"), prevent_initial_call=True)
def pending_req(n, selected, data, remark):
    return handle_request_update(selected, data, remark, RequestStatus.RETURN_PENDING)

@app.callback(Output("req-action-msg", "children", allow_duplicate=True),
              Input("btn-returned", "n_clicks"),
              State("req-table", "selected_rows"), State("req-table", "data"),
              State("mgr-remark", "value"), prevent_initial_call=True)
def returned_req(n, selected, data, remark):
    return handle_request_update(selected, data, remark, RequestStatus.RETURNED)

def handle_request_update(selected, data, remark, status):
    user = current_user()
    if not user:
        return "Not allowed."
    if user.role not in (Role.GM, Role.OM):
        return "Not allowed."
    if not selected:
        return "Select a request first."
    req_id = data[selected[0]]["id"]
    with SessionLocal() as s:
        r = s.get(Request, req_id)
        if not r:
            return "Request not found."
        if user.role == Role.OM and r.office_id != user.office_id:
            return "You can only update requests in your office."
        r.status = status
        if remark:
            r.remark = remark
        s.commit()
    return f"Status updated to {status.value}."

# ---------- Profile ----------
@app.callback(Output("profile-form", "children"), Input("url", "pathname"))
def load_profile(_):
    user = current_user()
    if not user:
        raise PreventUpdate
    with SessionLocal() as s:
        emp = _employee_for_user(user, s) if user.role == Role.EMP else None
        office = emp.office if emp else (user.office if user.office_id else None)
        return html.Div([
            html.Div([
                html.Div(f"Employee ID: {emp.id if emp else '—'}"),
                html.Div(f"Office ID: {office.id if office else '—'}"),
                html.Div(f"Office Name: {office.name if office else '—'}"),
            ], style={"marginBottom":"8px"}),
            dcc.Input(id="profile-emp-name", placeholder="Employee name", value=(emp.name if emp else "")),
            dcc.Input(id="profile-phone", placeholder="Phone number", value=getattr(emp, "phone", "") if emp else ""),
            html.Button("Save Profile", id="btn-save-profile", n_clicks=0, type="button"),
        ])

@app.callback(
    Output("profile-dialog","message"),
    Output("profile-dialog","displayed"),
    Output("profile-msg","children"),
    Input("btn-save-profile","n_clicks"),
    State("profile-emp-name","value"),
    State("profile-phone","value"),
    prevent_initial_call=True
)
def save_profile(n, name, phone):
    user = current_user()
    if not user:
        raise PreventUpdate
    if not n or n < 1:
        raise PreventUpdate
    name = (name or "").strip()
    phone = (phone or "").strip()
    if not name:
        return "", False, "Name is required."
    with SessionLocal() as s:
        emp = _employee_for_user(user, s)
        if not emp:
            return "", False, "No employee record."
        emp.name = name
        try:
            setattr(emp, "phone", phone)
        except Exception:
            pass
        s.commit()
    return "Profile updated.", True, ""

# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)


# from sqlalchemy.orm import joinedload
# from sqlalchemy import text
# import os, io, datetime
# from functools import wraps

# import dash
# from dash import Dash, html, dcc, Input, Output, State, dash_table
# from dash.exceptions import PreventUpdate
# import pandas as pd
# from werkzeug.security import check_password_hash, generate_password_hash
# from flask import session, send_from_directory

# from db import (
#     init_db, SessionLocal, Role, AllocationType, RequestStatus,
#     Office, User, Employee, Asset, Request, Remark,
# )

# # --- Try to add phone column if missing (safe on SQLite) ---
# try:
#     from db import engine as _engine  # type: ignore
#     with _engine.connect() as conn:  # type: ignore
#         cols = conn.execute(text("PRAGMA table_info(employees)")).fetchall()
#         names = {c[1] for c in cols}
#         if "phone" not in names:
#             conn.execute(text("ALTER TABLE employees ADD COLUMN phone VARCHAR"))
# except Exception:
#     pass

# UPLOAD_FOLDER = os.environ.get("RMS_UPLOAD_DIR", "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Initialize DB
# if not os.path.exists("rms.db"):
#     init_db(seed=True)
# else:
#     init_db(seed=False)

# # Dash app (CDN assets to avoid renderer path issues on Render)
# app = Dash(__name__, suppress_callback_exceptions=True, serve_locally=False)
# server = app.server
# server.secret_key = os.environ.get("RMS_SECRET", "dev-secret-key")

# # ---------- Helpers ----------
# def current_user():
#     if "user_id" not in session:
#         return None
#     with SessionLocal() as s:
#         u = s.query(User).options(joinedload(User.office)).get(session["user_id"])
#         if not u:
#             return None
#         _ = u.office.name if u.office else None
#         return u

# def _employee_for_user(user, s):
#     if not user or not user.office_id:
#         return None
#     employees = s.query(Employee).filter(Employee.office_id == user.office_id).all()
#     if not employees:
#         return None
#     uname = (user.username or "").strip().lower()
#     match = next((e for e in employees if (e.name or "").strip().lower() == uname), None)
#     return match or employees[0]

# def login_required(role: Role | None = None):
#     def decorator(fn):
#         @wraps(fn)
#         def wrapper(*args, **kwargs):
#             user = current_user()
#             if not user:
#                 raise PreventUpdate
#             if role and user.role != role:
#                 raise PreventUpdate
#             return fn(*args, **kwargs)
#         return wrapper
#     return decorator

# def role_name(role):
#     return {"GM": "General Manager", "OM": "Office Manager", "EMP": "Employee"}[role]

# # ---------- Layouts ----------
# def navbar():
#     user = current_user()
#     if not user:
#         return html.Nav([])
#     if user.role == Role.EMP:
#         items = [
#             dcc.Link("My Assets", href="/assets"),
#             html.Span(" | "),
#             dcc.Link("Requests", href="/requests"),
#             html.Span(" | "),
#             dcc.Link("My Profile", href="/profile"),
#             html.Span(" | "),
#             dcc.Link("Logout", href="/logout"),
#         ]
#         return html.Nav(items, style={"marginBottom": "10px"})
#     items = [
#         dcc.Link("Dashboard", href="/"),
#         html.Span(" | "),
#         dcc.Link("Assets", href="/assets"),
#         html.Span(" | "),
#         dcc.Link("Requests", href="/requests"),
#         html.Span(" | "),
#         dcc.Link("Reports", href="/reports"),
#         html.Span(" | "),
#         dcc.Link("Admin", href="/admin"),
#         html.Span(" | "),
#         dcc.Link("Logout", href="/logout")
#     ]
#     return html.Nav(items, style={"marginBottom": "10px"})

# def login_layout():
#     return html.Div([
#         html.H2("Resource Management System — Login"),
#         dcc.Input(id="login-username", placeholder="Username"),
#         dcc.Input(id="login-password", type="password", placeholder="Password"),
#         html.Button("Login", id="login-btn"),
#         html.Div(id="login-msg", style={"color": "crimson", "marginTop": "8px"}),
#         html.Hr(),
#         html.Div("Default demo users: admin/admin, om_east/om_east, alice/alice")
#     ], style={"maxWidth": "480px"})

# def dashboard_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role == Role.EMP:
#         return assets_layout()
#     scope = "Company-wide" if user.role == Role.GM else f"Office: {user.office.name if user.office else 'N/A'}"
#     return html.Div([
#         navbar(),
#         html.H3(f"Dashboard — {role_name(user.role.value)} ({scope})"),
#         html.Div(id="dashboard-cards"),
#     ])

# def _uploader_component():
#     return dcc.Upload(
#         id='upload-bill',
#         children=html.Button("Upload Bill / Drag & Drop"),
#         multiple=False,
#         style={
#             "border": "2px dashed #bbb",
#             "borderRadius": "10px",
#             "padding": "12px",
#             "display": "inline-block",
#             "cursor": "pointer",
#             "marginBottom": "8px"
#         }
#     )

# def assets_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role == Role.EMP:
#         return html.Div([
#             navbar(),
#             html.H3("My Assets"),
#             _uploader_component(),
#             dcc.Input(id="asset-name", placeholder="Asset name *"),
#             dcc.Input(id="asset-price", placeholder="Price *", type="number"),
#             dcc.Input(id="asset-qty", placeholder="Quantity *", type="number", value=1),
#             html.Button("Add to My Profile", id="add-asset-btn"),
#             html.Div(id="asset-add-msg", style={"color":"crimson", "marginTop":"6px"}),
#             dcc.ConfirmDialog(id="asset-dialog"),
#             html.Hr(),
#             html.H4("My Assets Table"),
#             html.Div(id="assets-table")
#         ])
#     return html.Div([
#         navbar(),
#         html.H3("Assets"),
#         _uploader_component(),
#         dcc.Input(id="asset-name", placeholder="Asset name *"),
#         dcc.Input(id="asset-price", placeholder="Price *", type="number"),
#         dcc.Input(id="asset-qty", placeholder="Quantity *", type="number", value=1),
#         html.Button("Add Asset", id="add-asset-btn"),
#         html.Div(id="asset-add-msg", style={"color":"crimson", "marginTop":"6px"}),
#         dcc.ConfirmDialog(id="asset-dialog"),
#         html.Hr(),
#         html.H4("Assets Table"),
#         html.Div(id="assets-table")
#     ])

# def requests_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.H3("Requests"),
#         html.Div(id="request-form"),
#         dcc.ConfirmDialog(id="req-dialog"),     # popup for requests
#         html.Hr(),
#         html.H4("Open Requests"),
#         html.Div(id="requests-table")
#     ])

# def reports_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role == Role.EMP:
#         return html.Div([navbar(), html.Div("Reports are not available for Employees.")])
#     return html.Div([navbar(), html.H3("Reports"), html.Div(id="reports-content")])

# def profile_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.H3("My Profile"),
#         html.Div(id="profile-form"),
#         dcc.ConfirmDialog(id="profile-dialog"),
#         html.Div(id="profile-msg", style={"color":"crimson", "marginTop":"6px"}),
#     ])

# def admin_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role != Role.GM:
#         return html.Div([navbar(), html.Div("Admins only.")])
#     return html.Div([
#         navbar(),
#         html.H3("Admin Panel"),
#         dcc.Input(id="new-office-name", placeholder="Office name"),
#         html.Button("Add Office", id="btn-add-office"),
#         html.Div(id="msg-add-office", style={"marginTop": "6px"}),
#         html.Hr(),
#         html.H4("Create User"),
#         dcc.Dropdown(id="user-role", options=[
#             {"label": "General Manager", "value": "GM"},
#             {"label": "Office Manager", "value": "OM"},
#             {"label": "Employee", "value": "EMP"}], placeholder="Role"),
#         dcc.Input(id="user-username", placeholder="Username"),
#         dcc.Input(id="user-password", placeholder="Password"),
#         dcc.Dropdown(id="user-office", placeholder="Office (optional)"),
#         html.Button("Create User", id="btn-add-user"),
#         html.Div(id="msg-add-user", style={"marginTop": "6px"}),
#         html.Hr(),
#         html.H4("Employees"),
#         dcc.Input(id="emp-name", placeholder="Employee name"),
#         dcc.Dropdown(id="emp-office", placeholder="Office"),
#         html.Button("Add Employee", id="btn-add-emp"),
#         html.Div(id="msg-add-emp", style={"marginTop": "6px"}),
#         html.Hr(),
#         html.Div(id="admin-tables")
#     ])

# app.layout = html.Div([
#     dcc.Location(id="url"),
#     html.Div(id="page-content")
# ])

# # ---------- Routes ----------
# @app.callback(Output("page-content", "children"), Input("url", "pathname"))
# def route(path):
#     user = current_user()
#     if path == "/logout":
#         session.clear()
#         return login_layout()
#     if not user:
#         return login_layout()
#     if path == "/" or path is None:
#         return dashboard_layout()
#     if path == "/assets":
#         return assets_layout()
#     if path == "/requests":
#         return requests_layout()
#     if path == "/reports":
#         return reports_layout()
#     if path == "/admin":
#         return admin_layout()
#     if path == "/profile":
#         return profile_layout()
#     return html.Div([navbar(), html.H3("Not Found")])

# # ---------- Login ----------
# @app.callback(Output("login-msg", "children"), Input("login-btn", "n_clicks"),
#               State("login-username", "value"), State("login-password", "value"),
#               prevent_initial_call=True)
# def do_login(n, username, password):
#     uname = (username or "").strip()
#     pwd = (password or "")
#     with SessionLocal() as s:
#         u = s.query(User).filter(User.username == uname).first()
#         if not u and s.query(User).count() == 0:
#             s.close()
#             init_db(seed=True)
#             with SessionLocal() as s2:
#                 u = s2.query(User).filter(User.username == uname).first()
#         if not u or not check_password_hash(u.password_hash, pwd):
#             return "Invalid credentials"
#         session["user_id"] = u.id
#         return dcc.Location(href="/", id="redir")

# # ---------- Dashboard (GM/OM only) ----------
# @app.callback(Output("dashboard-cards", "children"), Input("url", "pathname"))
# def load_kpis(_):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     if user.role == Role.EMP:
#         return html.Div()
#     with SessionLocal() as s:
#         if user.role == Role.GM:
#             total_assets_cost = sum(a.price * a.quantity for a in s.query(Asset).all())
#         else:
#             assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) &
#                  (Asset.allocation_id.in_([e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)])))
#             ).all()
#             total_assets_cost = sum(a.price * a.quantity for a in assets)
#         cards = [
#             html.Div([html.H4("Total Asset Cost"), html.H3(f"${total_assets_cost:,.2f}")],
#                      style={"padding": "10px", "border": "1px solid #eee",
#                             "borderRadius": "10px", "display": "inline-block", "marginRight": "10px"})
#         ]
#         return html.Div(cards)

# # ---------- Assets CRUD ----------
# @app.callback(
#     Output("asset-add-msg", "children"),
#     Output("assets-table", "children", allow_duplicate=True),
#     Output("asset-dialog", "message"),
#     Output("asset-dialog", "displayed"),
#     Output("asset-name", "value"),
#     Output("asset-price", "value"),
#     Output("asset-qty", "value"),
#     Output("upload-bill", "contents"),
#     Input("add-asset-btn", "n_clicks"),
#     State("asset-name", "value"), State("asset-price", "value"), State("asset-qty", "value"),
#     State("upload-bill", "contents"), State("upload-bill", "filename"),
#     prevent_initial_call=True
# )
# def add_asset(n, name, price, qty, contents, filename):
#     user = current_user()
#     if not user:
#         raise PreventUpdate

#     name = (name or "").strip()
#     try:
#         price_val = float(price)
#     except Exception:
#         price_val = 0.0
#     try:
#         qty_val = int(qty or 0)
#     except Exception:
#         qty_val = 0

#     if not name:
#         return ("Asset name is required.", render_assets_table(), "", False, name, price, qty, contents)
#     if price_val <= 0:
#         return ("Price must be greater than 0.", render_assets_table(), "", False, name, price, qty, contents)
#     if qty_val < 1:
#         return ("Quantity must be at least 1.", render_assets_table(), "", False, name, price, qty, contents)

#     saved_path = None
#     if contents and filename:
#         import base64
#         _, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
#         saved_path = os.path.join(UPLOAD_FOLDER, fname)
#         with open(saved_path, "wb") as f:
#             f.write(decoded)

#     with SessionLocal() as s:
#         if user.role == Role.EMP:
#             emp = _employee_for_user(user, s)
#             if not emp:
#                 return ("No employee profile found for you.", render_assets_table(), "", False, name, price, qty, contents)
#             a = Asset(
#                 name=name,
#                 price=price_val,
#                 quantity=qty_val,
#                 bill_path=saved_path,
#                 allocation_type=AllocationType.EMPLOYEE,
#                 allocation_id=emp.id
#             )
#             s.add(a); s.commit()
#             return ("", render_assets_table(), "Asset added to your profile.", True, "", "", 1, None)

#         a = Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path)
#         s.add(a); s.commit()
#     return ("", render_assets_table(), "Asset added.", True, "", "", 1, None)

# def _bill_link(a):
#     """Return an HTML anchor that triggers a file download."""
#     if not a.bill_path:
#         return ""
#     base = os.path.basename(a.bill_path)
#     # Use a plain HTML <a> so it downloads; DataTable will render it via dangerously_allow_html=True
#     return f'<a href="/uploads/{base}" download="{base}" target="_blank">{base}</a>'

# @app.callback(Output("assets-table", "children"), Input("url", "pathname"))
# def render_assets_table(_=None):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         if user.role == Role.EMP:
#             emp = _employee_for_user(user, s)
#             assets = [] if not emp else s.query(Asset).filter(
#                 Asset.allocation_type == AllocationType.EMPLOYEE,
#                 Asset.allocation_id == emp.id
#             ).all()
#             rows = []
#             for i, a in enumerate(assets, start=1):
#                 rows.append({
#                     "asset_no": i,
#                     "name": a.name, "price": a.price, "qty": a.quantity,
#                     "bill": _bill_link(a),
#                 })
#             cols = [
#                 {"name":"asset_no","id":"asset_no"},
#                 {"name":"name","id":"name"},
#                 {"name":"price","id":"price"},
#                 {"name":"qty","id":"qty"},
#                 {"name":"bill","id":"bill"},  # html link
#             ]
#             return dash_table.DataTable(
#                 data=rows,
#                 columns=cols,
#                 page_size=10,
#                 style_table={"overflowX":"auto"},
#                 dangerously_allow_html=True  # <-- render <a> as link
#             )
#         else:
#             assets = s.query(Asset).all()
#             rows = [{
#                 "id": a.id, "name": a.name, "price": a.price, "qty": a.quantity,
#                 "bill": _bill_link(a),
#                 "allocation": a.allocation_type.value,
#                 "allocation_id": a.allocation_id
#             } for a in assets]
#             cols = [
#                 {"name":"id","id":"id"},
#                 {"name":"name","id":"name"},
#                 {"name":"price","id":"price"},
#                 {"name":"qty","id":"qty"},
#                 {"name":"bill","id":"bill"},  # html link
#                 {"name":"allocation","id":"allocation"},
#                 {"name":"allocation_id","id":"allocation_id"},
#             ]
#             return dash_table.DataTable(
#                 data=rows,
#                 columns=cols,
#                 page_size=10,
#                 style_table={"overflowX":"auto"},
#                 dangerously_allow_html=True  # <-- render <a> as link
#             )

# @server.route("/uploads/<path:path>")
# def serve_file(path):
#     # This header forces download instead of trying to preview
#     return send_from_directory(UPLOAD_FOLDER, path, as_attachment=True)

# # ---------- Requests ----------
# @app.callback(Output("request-form", "children"), Input("url", "pathname"))
# def req_form(_):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         if user.role == Role.EMP:
#             emp = _employee_for_user(user, s)
#             options = [{"label": emp.name, "value": emp.id}] if emp else []
#             return html.Div([
#                 html.H4("Create Request"),
#                 dcc.Dropdown(id="req-employee", options=options,
#                              value=(emp.id if emp else None),
#                              disabled=True,
#                              placeholder="Employee"),
#                 dcc.Input(id="req-asset-name", placeholder="Asset name"),
#                 dcc.Input(id="req-qty", type="number", value=1),
#                 html.Button("Submit Request", id="req-submit", type="button", n_clicks=0),
#                 html.Div(id="req-msg", style={"marginTop": "6px", "color":"crimson"})
#             ])
#         else:
#             employees = s.query(Employee).all() if user.role == Role.GM else \
#                         s.query(Employee).filter(Employee.office_id == user.office_id).all()
#             options = [{"label": e.name, "value": e.id} for e in employees]
#             return html.Div([
#                 html.H4("Create Request"),
#                 dcc.Dropdown(id="req-employee", options=options, placeholder="Employee"),
#                 dcc.Input(id="req-asset-name", placeholder="Asset name"),
#                 dcc.Input(id="req-qty", type="number", value=1),
#                 html.Button("Submit Request", id="req-submit", type="button", n_clicks=0),
#                 html.Div(id="req-msg", style={"marginTop": "6px", "color":"crimson"})
#             ])

# @app.callback(
#     Output("req-msg", "children"),
#     Output("requests-table", "children", allow_duplicate=True),
#     Output("req-dialog","message"),
#     Output("req-dialog","displayed"),
#     Output("req-asset-name","value"),
#     Output("req-qty","value"),
#     Input("req-submit", "n_clicks"),
#     State("req-employee", "value"),
#     State("req-asset-name", "value"),
#     State("req-qty", "value"),
#     prevent_initial_call=True
# )
# def create_request(n, emp_id, asset_name, qty):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     if not n or n < 1:
#         raise PreventUpdate

#     asset_name = (asset_name or "").strip()
#     try:
#         qty = int(qty or 0)
#     except Exception:
#         qty = 0
#     if not asset_name:
#         return "Please enter an asset name.", render_requests_table(), "", False, asset_name, qty
#     if qty < 1:
#         return "Quantity must be at least 1.", render_requests_table(), "", False, asset_name, qty

#     with SessionLocal() as s:
#         if user.role == Role.EMP and not emp_id:
#             emp = _employee_for_user(user, s)
#             emp_id = emp.id if emp else None
#         if not emp_id:
#             return "Select an employee.", render_requests_table(), "", False, asset_name, qty

#         emp = s.get(Employee, emp_id)
#         if not emp:
#             return "Invalid employee.", render_requests_table(), "", False, asset_name, qty
#         if user.role == Role.OM and emp.office_id != user.office_id:
#             return "You can only submit requests for your office.", render_requests_table(), "", False, asset_name, qty

#         r = Request(
#             employee_id=emp.id,
#             office_id=emp.office_id,
#             asset_name=asset_name,
#             quantity=qty
#         )
#         s.add(r)
#         s.commit()

#     # success -> popup + clear fields
#     return "", render_requests_table(), "Request submitted.", True, "", 1

# @app.callback(Output("requests-table", "children"), Input("url", "pathname"))
# def render_requests_table(_=None):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         q = s.query(Request)
#         if user.role == Role.OM:
#             q = q.filter(Request.office_id == user.office_id)
#         elif user.role == Role.EMP:
#             emp = _employee_for_user(user, s)
#             q = q.filter(Request.employee_id == emp.id) if emp else q.filter(Request.id == -1)
#         rows = q.order_by(Request.created_at.desc()).all()
#         data = [{
#             "id": r.id, "employee_id": r.employee_id, "office_id": r.office_id, "asset": r.asset_name,
#             "qty": r.quantity, "status": r.status.value, "remark": r.remark or "", "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
#         } for r in rows]
#     cols = [{"name": n, "id": n} for n in ["id", "employee_id", "office_id", "asset", "qty", "status", "remark", "created_at"]]

#     user = current_user()
#     controls = html.Div([
#         dcc.Textarea(id="mgr-remark", placeholder="Remark…", style={"width": "100%", "height": "60px"}),
#         html.Button("Approve", id="btn-approve"),
#         html.Button("Reject", id="btn-reject"),
#         html.Button("Mark Return Pending", id="btn-return-pending"),
#         html.Button("Mark Returned", id="btn-returned"),
#         html.Div(id="req-action-msg", style={"marginTop": "6px"})
#     ]) if user and user.role in (Role.GM, Role.OM) else html.Div()

#     return html.Div([
#         dash_table.DataTable(data=data, columns=cols, id="req-table", row_selectable="single", page_size=10),
#         controls
#     ])

# @app.callback(Output("req-action-msg", "children", allow_duplicate=True),
#               Input("btn-approve", "n_clicks"),
#               State("req-table", "selected_rows"), State("req-table", "data"),
#               State("mgr-remark", "value"), prevent_initial_call=True)
# def approve_req(n, selected, data, remark):
#     return handle_request_update(selected, data, remark, RequestStatus.APPROVED)

# @app.callback(Output("req-action-msg", "children", allow_duplicate=True),
#               Input("btn-reject", "n_clicks"),
#               State("req-table", "selected_rows"), State("req-table", "data"),
#               State("mgr-remark", "value"), prevent_initial_call=True)
# def reject_req(n, selected, data, remark):
#     return handle_request_update(selected, data, remark, RequestStatus.REJECTED)

# @app.callback(Output("req-action-msg", "children", allow_duplicate=True),
#               Input("btn-return-pending", "n_clicks"),
#               State("req-table", "selected_rows"), State("req-table", "data"),
#               State("mgr-remark", "value"), prevent_initial_call=True)
# def pending_req(n, selected, data, remark):
#     return handle_request_update(selected, data, remark, RequestStatus.RETURN_PENDING)

# @app.callback(Output("req-action-msg", "children", allow_duplicate=True),
#               Input("btn-returned", "n_clicks"),
#               State("req-table", "selected_rows"), State("req-table", "data"),
#               State("mgr-remark", "value"), prevent_initial_call=True)
# def returned_req(n, selected, data, remark):
#     return handle_request_update(selected, data, remark, RequestStatus.RETURNED)

# def handle_request_update(selected, data, remark, status):
#     user = current_user()
#     if not user:
#         return "Not allowed."
#     if user.role not in (Role.GM, Role.OM):
#         return "Not allowed."
#     if not selected:
#         return "Select a request first."
#     req_id = data[selected[0]]["id"]
#     with SessionLocal() as s:
#         r = s.get(Request, req_id)
#         if not r:
#             return "Request not found."
#         if user.role == Role.OM and r.office_id != user.office_id:
#             return "You can only update requests in your office."
#         r.status = status
#         if remark:
#             r.remark = remark
#         s.commit()
#     return f"Status updated to {status.value}."

# # ---------- Profile ----------
# @app.callback(Output("profile-form", "children"), Input("url", "pathname"))
# def load_profile(_):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         emp = _employee_for_user(user, s) if user.role == Role.EMP else None
#         office = emp.office if emp else (user.office if user.office_id else None)
#         return html.Div([
#             html.Div([
#                 html.Div(f"Employee ID: {emp.id if emp else '—'}"),
#                 html.Div(f"Office ID: {office.id if office else '—'}"),
#                 html.Div(f"Office Name: {office.name if office else '—'}"),
#             ], style={"marginBottom":"8px"}),
#             dcc.Input(id="profile-emp-name", placeholder="Employee name", value=(emp.name if emp else "")),
#             dcc.Input(id="profile-phone", placeholder="Phone number", value=getattr(emp, "phone", "") if emp else ""),
#             html.Button("Save Profile", id="btn-save-profile", n_clicks=0, type="button"),
#         ])

# @app.callback(
#     Output("profile-dialog","message"),
#     Output("profile-dialog","displayed"),
#     Output("profile-msg","children"),
#     Input("btn-save-profile","n_clicks"),
#     State("profile-emp-name","value"),
#     State("profile-phone","value"),
#     prevent_initial_call=True
# )
# def save_profile(n, name, phone):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     if not n or n < 1:
#         raise PreventUpdate
#     name = (name or "").strip()
#     phone = (phone or "").strip()
#     if not name:
#         return "", False, "Name is required."
#     with SessionLocal() as s:
#         emp = _employee_for_user(user, s)
#         if not emp:
#             return "", False, "No employee record."
#         emp.name = name
#         try:
#             setattr(emp, "phone", phone)
#         except Exception:
#             pass
#         s.commit()
#     return "Profile updated.", True, ""

# # ---------- Run ----------
# if __name__ == "__main__":
#     app.run(debug=True)
