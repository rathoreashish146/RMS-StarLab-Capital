#   raise PreventUpdate
#             if role and user.role != role:
#                 raise PreventUpdate
#             return fn(*args, **kwargs)
#         return wrapper
#     return decorator

# def role_name(role):
#     return {"GM":"General Manager","OM":"Office Manager","EMP":"Employee"}[role]

# def df(query):
#     with SessionLocal() as s:
#         return pd.read_sql(query, s.bind)

# # ---------- Layouts ----------
# def navbar():
#     user = current_user()
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
#     return html.Nav(items, style={"marginBottom":"10px"}) if user else html.Nav([])

# def login_layout():
#     return html.Div([
#         html.H2("Resource Management System — Login"),
#         dcc.Input(id="login-username", placeholder="Username"),
#         dcc.Input(id="login-password", type="password", placeholder="Password"),
#         html.Button("Login", id="login-btn"),
#         html.Div(id="login-msg", style={"color":"crimson","marginTop":"8px"}),
#         html.Hr(),
#         html.Div("Default demo users: admin/admin, om_east/om_east, alice/alice")
#     ], style={"maxWidth":"480px"})

# def dashboard_layout():
#     user = current_user()
#     if not user: return login_layout()
#     scope = "Company-wide" if user.role == Role.GM else f"Office: {user.office.name if user.office else 'N/A'}"
#     return html.Div([
#         navbar(),
#         html.H3(f"Dashboard — {role_name(user.role.value)} ({scope})"),
#         html.Div(id="dashboard-cards"),
#     ])

# def assets_layout():
#     user = current_user()
#     if not user: return login_layout()
#     return html.Div([
#         navbar(),
#         html.H3("Assets"),
#         dcc.Upload(id='upload-bill', children=html.Div(['Drag/Drop or ', html.A('Select Bill (image/pdf)')]),
#                    multiple=False),
#         dcc.Input(id="asset-name", placeholder="Asset name"),
#         dcc.Input(id="asset-price", placeholder="Price", type="number"),
#         dcc.Input(id="asset-qty", placeholder="Quantity", type="number", value=1),
#         html.Button("Add Asset", id="add-asset-btn"),
#         html.Div(id="asset-add-msg"),
#         html.Hr(),
#         html.H4("Assets Table"),
#         html.Div(id="assets-table")
#     ])

# def requests_layout():
#     user = current_user()
#     if not user: return login_layout()
#     return html.Div([
#         navbar(),
#         html.H3("Requests"),
#         html.Div(id="request-form"),
#         html.Hr(),
#         html.H4("Open Requests"),
#         html.Div(id="requests-table")
#     ])

# def reports_layout():
#     user = current_user()
#     if not user: return login_layout()
#     return html.Div([
#         navbar(),
#         html.H3("Reports"),
#         html.Div(id="reports-content")
#     ])

# def admin_layout():
#     user = current_user()
#     if not user: return login_layout()
#     if user.role != Role.GM:
#         return html.Div([navbar(), html.Div("Admins only.")])
#     return html.Div([
#         navbar(),
#         html.H3("Admin Panel"),
#         html.H4("Create Office"),
#         dcc.Input(id="new-office-name", placeholder="Office name"),
#         html.Button("Add Office", id="btn-add-office"),
#         html.Div(id="msg-add-office", style={"marginTop":"6px"}),
#         html.Hr(),
#         html.H4("Create User"),
#         dcc.Dropdown(id="user-role", options=[{"label":"General Manager","value":"GM"},
#                                               {"label":"Office Manager","value":"OM"},
#                                               {"label":"Employee","value":"EMP"}], placeholder="Role"),
#         dcc.Input(id="user-username", placeholder="Username"),
#         dcc.Input(id="user-password", placeholder="Password"),
#         dcc.Dropdown(id="user-office", placeholder="Office (optional)"),
#         html.Button("Create User", id="btn-add-user"),
#         html.Div(id="msg-add-user", style={"marginTop":"6px"}),
#         html.Hr(),
#         html.H4("Employees"),
#         dcc.Input(id="emp-name", placeholder="Employee name"),
#         dcc.Dropdown(id="emp-office", placeholder="Office"),
#         html.Button("Add Employee", id="btn-add-emp"),
#         html.Div(id="msg-add-emp", style={"marginTop":"6px"}),
#         html.Hr(),
#         html.Div(id="admin-tables")
#     ])

# app.layout = html.Div([
#     dcc.Location(id="url"),
#     html.Div(id="page-content")
# ])

# # ---------- Routes ----------
# @app.callback(Output("page-content","children"), Input("url","pathname"))
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
#     return html.Div([navbar(), html.H3("Not Found")])

# # ---------- Login ----------
# @app.callback(Output("login-msg","children"), Input("login-btn","n_clicks"),
#               State("login-username","value"), State("login-password","value"),
#               prevent_initial_call=True)
# def do_login(n, username, password):
#     with SessionLocal() as s:
#         u = s.query(User).filter(User.username == (username or "")).first()
#         if not u or not check_password_hash(u.password_hash, password or ""):
#             return "Invalid credentials"
#         session["user_id"] = u.id
#         return dcc.Location(href="/", id="redir")  # client side redirect

# # ---------- Dashboard KPIs ----------
# @app.callback(Output("dashboard-cards","children"), Input("url","pathname"))
# def load_kpis(_):
#     user = current_user()
#     if not user: raise PreventUpdate
#     with SessionLocal() as s:
#         # totals
#         if user.role == Role.GM:
#             total_assets_cost = sum(a.price * a.quantity for a in s.query(Asset).all())
#             by_office = s.query(Office).all()
#         else:
#             # office scoped
#             assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(
#                     [e.id for e in s.query(Employee).filter(Employee.office_id==user.office_id)]
#                 )))
#             ).all()
#             total_assets_cost = sum(a.price * a.quantity for a in assets)
#             by_office = [user.office]

#         cards = [
#             html.Div([html.H4("Total Asset Cost"), html.H3(f"${total_assets_cost:,.2f}")],
#                      style={"padding":"10px","border":"1px solid #eee","borderRadius":"10px","display":"inline-block","marginRight":"10px"}),
#         ]

#         # pending returns & approvals
#         if user.role in (Role.GM, Role.OM):
#             if user.role == Role.GM:
#                 pending = s.query(Request).filter(Request.status==RequestStatus.PENDING).count()
#                 returns = s.query(Request).filter(Request.status==RequestStatus.RETURN_PENDING).count()
#             else:
#                 pending = s.query(Request).filter(Request.status==RequestStatus.PENDING, Request.office_id==user.office_id).count()
#                 returns = s.query(Request).filter(Request.status==RequestStatus.RETURN_PENDING, Request.office_id==user.office_id).count()
#             cards.append(html.Div([html.H4("Pending Requests"), html.H3(str(pending))],
#                      style={"padding":"10px","border":"1px solid #eee","borderRadius":"10px","display":"inline-block","marginRight":"10px"}))
#             cards.append(html.Div([html.H4("Pending Returns"), html.H3(str(returns))],
#                      style={"padding":"10px","border":"1px solid #eee","borderRadius":"10px","display":"inline-block"}))
#         return html.Div(cards)

# # ---------- Assets CRUD ----------
# @app.callback(
#     Output("asset-add-msg","children"),
#     Output("assets-table","children"),
#     Input("add-asset-btn","n_clicks"),
#     State("asset-name","value"), State("asset-price","value"), State("asset-qty","value"),
#     State("upload-bill","contents"), State("upload-bill","filename"),
#     prevent_initial_call=True
# )
# def add_asset(n, name, price, qty, contents, filename):
#     user = current_user()
#     if not user: raise PreventUpdate
#     saved_path = None
#     if contents and filename:
#         import base64
#         content_type, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         saved_path = os.path.join(UPLOAD_FOLDER, f"{datetime.datetime.utcnow().timestamp()}_{filename}")
#         with open(saved_path, "wb") as f:
#             f.write(decoded)
#     with SessionLocal() as s:
#         a = Asset(name=name or "Unnamed", price=float(price or 0), quantity=int(qty or 1), bill_path=saved_path)
#         s.add(a); s.commit()
#     return "Asset added.", render_assets_table()

# @app.callback(Output("assets-table","children"), Input("url","pathname"))
# def render_assets_table(_=None):
#     user = current_user()
#     if not user: raise PreventUpdate
#     with SessionLocal() as s:
#         assets = s.query(Asset).all()
#         rows = [{
#             "id": a.id, "name": a.name, "price": a.price, "qty": a.quantity,
#             "bill": os.path.basename(a.bill_path) if a.bill_path else "",
#             "allocation": a.allocation_type.value,
#             "allocation_id": a.allocation_id
#         } for a in assets]
#     table = dash_table.DataTable(
#         data=rows,
#         columns=[{"name":k,"id":k} for k in ["id","name","price","qty","bill","allocation","allocation_id"]],
#         page_size=10,
#         style_table={"overflowX":"auto"}
#     )
#     return table

# # Serve uploaded files
# @server.route("/uploads/<path:path>")
# def serve_file(path):
#     return send_from_directory(UPLOAD_FOLDER, path, as_attachment=True)

# # ---------- Requests ----------
# @app.callback(Output("request-form","children"), Input("url","pathname"))
# def req_form(_):
#     user = current_user()
#     if not user: raise PreventUpdate
#     with SessionLocal() as s:
#         employees = s.query(Employee).all() if user.role!=Role.EMP else s.query(Employee).filter(Employee.office_id==user.office_id).all()
#     options = [{"label":e.name, "value":e.id} for e in employees]
#     return html.Div([
#         html.H4("Create Request"),
#         dcc.Dropdown(id="req-employee", options=options, placeholder="Employee"),
#         dcc.Input(id="req-asset-name", placeholder="Asset name"),
#         dcc.Input(id="req-qty", type="number", value=1),
#         html.Button("Submit Request", id="req-submit"),
#         html.Div(id="req-msg", style={"marginTop":"6px"})
#     ])

# @app.callback(Output("req-msg","children"),
#               Output("requests-table","children"),
#               Input("req-submit","n_clicks"),
#               State("req-employee","value"), State("req-asset-name","value"), State("req-qty","value"),
#               prevent_initial_call=True)
# def create_request(n, emp_id, asset_name, qty):
#     user = current_user()
#     if not user: raise PreventUpdate
#     with SessionLocal() as s:
#         emp = s.get(Employee, emp_id)
#         if not emp:
#             return "Select an employee.", render_requests_table()
#         r = Request(employee_id=emp.id, office_id=emp.office_id, asset_name=asset_name or "Unnamed", quantity=int(qty or 1))
#         s.add(r); s.commit()
#     return "Request submitted.", render_requests_table()

# @app.callback(Output("requests-table","children"), Input("url","pathname"))
# def render_requests_table(_=None):
#     user = current_user()
#     if not user: raise PreventUpdate
#     with SessionLocal() as s:
#         q = s.query(Request)
#         if user.role == Role.OM:
#             q = q.filter(Request.office_id == user.office_id)
#         rows = q.order_by(Request.created_at.desc()).all()
#         data = [{
#             "id": r.id, "employee_id": r.employee_id, "office_id": r.office_id, "asset": r.asset_name,
#             "qty": r.quantity, "status": r.status.value, "remark": r.remark or "", "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
#         } for r in rows]
#     cols = [{"name":n,"id":n} for n in ["id","employee_id","office_id","asset","qty","status","remark","created_at"]]
#     return html.Div([
#         dash_table.DataTable(data=data, columns=cols, id="req-table", row_selectable="single", page_size=10),
#         html.Div([
#             dcc.Textarea(id="mgr-remark", placeholder="Remark…", style={"width":"100%","height":"60px"}),
#             html.Button("Approve", id="btn-approve"),
#             html.Button("Reject", id="btn-reject"),
#             html.Button("Mark Return Pending", id="btn-return-pending"),
#             html.Button("Mark Returned", id="btn-returned"),
#             html.Div(id="req-action-msg", style={"marginTop":"6px"})
#         ])
#     ])

# def _update_request_status(req_id, status, remark):
#     with SessionLocal() as s:
#         r = s.get(Request, req_id)
#         if not r:
#             return "Select a request first."
#         r.status = status
#         if remark:
#             r.remark = remark
#         s.commit()
#     return f"Status set to {status.value}."

# for btn_id, status in [
#     ("btn-approve", RequestStatus.APPROVED),
#     ("btn-reject", RequestStatus.REJECTED),
#     ("btn-return-pending", RequestStatus.RETURN_PENDING),
#     ("btn-returned", RequestStatus.RETURNED),
# ]:
#     @app.callback(Output("req-action-msg","children"),
#                   Input(btn_id,"n_clicks"),
#                   State("req-table","selected_rows"),
#                   State("req-table","data"),
#                   State("mgr-remark","value"),
#                   prevent_initial_call=True)
#     def _handler(n, selected, data, remark, _status=status):
#         user = current_user()
#         if not user: raise PreventUpdate
#         if not selected:
#             return "Select a request in the table."
#         req_id = data[selected[0]]["id"]
#         return _update_request_status(req_id, _status, remark)

# # ---------- Reports ----------
# @app.callback(Output("reports-content","children"), Input("url","pathname"))
# def render_reports(_):
#     user = current_user()
#     if not user: raise PreventUpdate
#     with SessionLocal() as s:
#         # totals by employee & office
#         # asset cost is approximated: sum(price*qty) grouped by allocation
#         assets = s.query(Asset).all()
#         emp_ids = {a.allocation_id for a in assets if a.allocation_type==AllocationType.EMPLOYEE}
#         off_ids = {a.allocation_id for a in assets if a.allocation_type==AllocationType.OFFICE}

#         emp_cost = {}
#         for a in assets:
#             if a.allocation_type==AllocationType.EMPLOYEE:
#                 emp_cost[a.allocation_id] = emp_cost.get(a.allocation_id, 0) + a.price*a.quantity
#         off_cost = {}
#         for a in assets:
#             if a.allocation_type==AllocationType.OFFICE:
#                 off_cost[a.allocation_id] = off_cost.get(a.allocation_id, 0) + a.price*a.quantity

#         employees = {e.id:e for e in s.query(Employee).all()}
#         offices = {o.id:o for o in s.query(Office).all()}

#         emp_rows = [{"employee": employees[eid].name, "office": offices[employees[eid].office_id].name, "total_cost": round(cost,2)} for eid, cost in emp_cost.items()]
#         off_rows = [{"office": offices[oid].name, "total_cost": round(cost,2)} for oid, cost in off_cost.items()]

#     return html.Div([
#         html.H4("Asset Cost by Employee"),
#         dash_table.DataTable(data=emp_rows, columns=[{"name":k,"id":k} for k in ["employee","office","total_cost"]], page_size=10),
#         html.Br(),
#         html.H4("Asset Cost by Office"),
#         dash_table.DataTable(data=off_rows, columns=[{"name":k,"id":k} for k in ["office","total_cost"]], page_size=10),
#     ])

# # ---------- Admin ----------
# @app.callback(
#     Output("msg-add-office","children"),
#     Output("user-office","options"),
#     Output("emp-office","options"),
#     Input("btn-add-office","n_clicks"),
#     State("new-office-name","value"),
#     prevent_initial_call=True
# )
# def add_office(n, name):
#     with SessionLocal() as s:
#         if not (name or "").strip():
#             offices = s.query(Office).all()
#             opts = [{"label":o.name, "value":o.id} for o in offices]
#             return "Enter a name.", opts, opts
#         s.add(Office(name=name.strip()))
#         s.commit()
#         offices = s.query(Office).all()
#         opts = [{"label":o.name, "value":o.id} for o in offices]
#     return "Office added.", opts, opts

# @app.callback(
#     Output("msg-add-user","children"),
#     Input("btn-add-user","n_clicks"),
#     State("user-role","value"), State("user-username","value"), State("user-password","value"), State("user-office","value"),
#     prevent_initial_call=True
# )
# def add_user(n, role, username, password, office_id):
#     if not role or not username or not password:
#         return "Fill all required fields."
#     with SessionLocal() as s:
#         if s.query(User).filter(User.username==username).first():
#             return "Username already exists."
#         u = User(username=username, password_hash=generate_password_hash(password), role=Role(role), office_id=office_id)
#         s.add(u); s.commit()
#     return "User created."

# @app.callback(
#     Output("msg-add-emp","children"),
#     Input("btn-add-emp","n_clicks"),
#     State("emp-name","value"), State("emp-office","value"),
#     prevent_initial_call=True
# )
# def add_employee(n, name, office_id):
#     if not name or not office_id:
#         return "Provide name and office."
#     with SessionLocal() as s:
#         s.add(Employee(name=name, office_id=int(office_id))); s.commit()
#     return "Employee added."

# @app.callback(Output("admin-tables","children"), Input("url","pathname"))
# def admin_tables(_):
#     user = current_user()
#     if not user or user.role!=Role.GM: raise PreventUpdate
#     with SessionLocal() as s:
#         users = s.query(User).all()
#         offices = s.query(Office).all()
#         employees = s.query(Employee).all()
#     urows = [{"id":u.id, "username":u.username, "role":u.role.value, "office": (u.office.name if u.office else "")} for u in users]
#     orows = [{"id":o.id, "name":o.name} for o in offices]
#     erows = [{"id":e.id, "name":e.name, "office":e.office.name} for e in employees]
#     return html.Div([
#         html.H4("Users"), dash_table.DataTable(data=urows, columns=[{"name":k,"id":k} for k in ["id","username","role","office"]], page_size=10),
#         html.Br(),
#         html.H4("Offices"), dash_table.DataTable(data=orows, columns=[{"name":"id","id":"id"},{"name":"name","id":"name"}], page_size=10),
#         html.Br(),
#         html.H4("Employees"), dash_table.DataTable(data=erows, columns=[{"name":k,"id":k} for k in ["id","name","office"]], page_size=10),
#     ])

# if __name__ == "__main__":
#     app.run(debug=True)

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
    Office, User, Employee, Asset, Request, Remark
)

UPLOAD_FOLDER = os.environ.get("RMS_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize DB (create if missing) and seed demo data
if not os.path.exists("rms.db"):
    init_db(seed=True)
else:
    init_db(seed=False)

# Create Dash app (Flask server under the hood)
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
server.secret_key = os.environ.get("RMS_SECRET", "dev-secret-key")

# ---------- Helpers ----------
def current_user():
    if "user_id" not in session:
        return None
    with SessionLocal() as s:
        return s.get(User, session["user_id"])

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
    return html.Nav(items, style={"marginBottom": "10px"}) if user else html.Nav([])

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
    scope = "Company-wide" if user.role == Role.GM else f"Office: {user.office.name if user.office else 'N/A'}"
    return html.Div([
        navbar(),
        html.H3(f"Dashboard — {role_name(user.role.value)} ({scope})"),
        html.Div(id="dashboard-cards"),
    ])

def assets_layout():
    user = current_user()
    if not user:
        return login_layout()
    return html.Div([
        navbar(),
        html.H3("Assets"),
        dcc.Upload(id='upload-bill', children=html.Div(['Drag/Drop or ', html.A('Select Bill (image/pdf)')]),
                   multiple=False),
        dcc.Input(id="asset-name", placeholder="Asset name"),
        dcc.Input(id="asset-price", placeholder="Price", type="number"),
        dcc.Input(id="asset-qty", placeholder="Quantity", type="number", value=1),
        html.Button("Add Asset", id="add-asset-btn"),
        html.Div(id="asset-add-msg"),
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
        html.Hr(),
        html.H4("Open Requests"),
        html.Div(id="requests-table")
    ])

def reports_layout():
    user = current_user()
    if not user:
        return login_layout()
    return html.Div([
        navbar(),
        html.H3("Reports"),
        html.Div(id="reports-content")
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
        html.H4("Create Office"),
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
    return html.Div([navbar(), html.H3("Not Found")])

# ---------- Login ----------
@app.callback(Output("login-msg", "children"), Input("login-btn", "n_clicks"),
              State("login-username", "value"), State("login-password", "value"),
              prevent_initial_call=True)
def do_login(n, username, password):
    with SessionLocal() as s:
        u = s.query(User).filter(User.username == (username or "")).first()
        if not u or not check_password_hash(u.password_hash, password or ""):
            return "Invalid credentials"
        session["user_id"] = u.id
        return dcc.Location(href="/", id="redir")

# ---------- Dashboard ----------
@app.callback(Output("dashboard-cards", "children"), Input("url", "pathname"))
def load_kpis(_):
    user = current_user()
    if not user:
        raise PreventUpdate
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
    Input("add-asset-btn", "n_clicks"),
    State("asset-name", "value"), State("asset-price", "value"), State("asset-qty", "value"),
    State("upload-bill", "contents"), State("upload-bill", "filename"),
    prevent_initial_call=True
)
def add_asset(n, name, price, qty, contents, filename):
    user = current_user()
    if not user:
        raise PreventUpdate
    saved_path = None
    if contents and filename:
        import base64
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        saved_path = os.path.join(UPLOAD_FOLDER, f"{datetime.datetime.utcnow().timestamp()}_{filename}")
        with open(saved_path, "wb") as f:
            f.write(decoded)
    with SessionLocal() as s:
        a = Asset(name=name or "Unnamed", price=float(price or 0), quantity=int(qty or 1), bill_path=saved_path)
        s.add(a)
        s.commit()
    return "Asset added.", render_assets_table()

@app.callback(Output("assets-table", "children"), Input("url", "pathname"))
def render_assets_table(_=None):
    user = current_user()
    if not user:
        raise PreventUpdate
    with SessionLocal() as s:
        assets = s.query(Asset).all()
        rows = [{
            "id": a.id, "name": a.name, "price": a.price, "qty": a.quantity,
            "bill": os.path.basename(a.bill_path) if a.bill_path else "",
            "allocation": a.allocation_type.value,
            "allocation_id": a.allocation_id
        } for a in assets]
    return dash_table.DataTable(data=rows,
                                columns=[{"name": k, "id": k} for k in ["id", "name", "price", "qty", "bill", "allocation", "allocation_id"]],
                                page_size=10, style_table={"overflowX": "auto"})

@server.route("/uploads/<path:path>")
def serve_file(path):
    return send_from_directory(UPLOAD_FOLDER, path, as_attachment=True)

# ---------- Requests ----------
@app.callback(Output("req-msg", "children"),
              Output("requests-table", "children", allow_duplicate=True),
              Input("req-submit", "n_clicks"),
              State("req-employee", "value"), State("req-asset-name", "value"), State("req-qty", "value"),
              prevent_initial_call=True)
def create_request(n, emp_id, asset_name, qty):
    user = current_user()
    if not user:
        raise PreventUpdate
    with SessionLocal() as s:
        emp = s.get(Employee, emp_id)
        if not emp:
            return "Select an employee.", render_requests_table()
        r = Request(employee_id=emp.id, office_id=emp.office_id,
                    asset_name=asset_name or "Unnamed", quantity=int(qty or 1))
        s.add(r)
        s.commit()
    return "Request submitted.", render_requests_table()

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
    if not user or not selected:
        return "Select a request first."
    req_id = data[selected[0]]["id"]
    with SessionLocal() as s:
        r = s.get(Request, req_id)
        if not r:
            return "Request not found."
        r.status = status
        if remark:
            r.remark = remark
        s.commit()
    return f"Status updated to {status.value}."

# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)

