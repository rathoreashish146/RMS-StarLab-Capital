# from sqlalchemy.orm import joinedload
# from sqlalchemy import text
# import os, datetime
# from functools import wraps

# import dash
# from dash import Dash, html, dcc, Input, Output, State, dash_table
# from dash.exceptions import PreventUpdate
# from werkzeug.security import check_password_hash, generate_password_hash
# from flask import session, send_from_directory

# from db import (
#     init_db, SessionLocal, Role, AllocationType, RequestStatus,
#     Office, User, Employee, Asset, Request, Remark, engine
# )

# # --- tiny migrations (idempotent) ---
# def _safe_add_column(table, coldef):
#     try:
#         with engine.begin() as conn:
#             cols = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
#             names = {c[1] for c in cols}
#             cname = coldef.split()[0]
#             if cname not in names:
#                 conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {coldef}"))
#     except Exception:
#         pass

# _safe_add_column("employees", "phone VARCHAR")
# _safe_add_column("employees", "username VARCHAR")

# UPLOAD_FOLDER = os.environ.get("RMS_UPLOAD_DIR", "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Initialize DB
# if not os.path.exists("rms.db"):
#     init_db(seed=True)
# else:
#     init_db(seed=False)

# # Dash
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
#     # strict username link first
#     emp = s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.username == user.username
#     ).first()
#     if emp:
#         return emp
#     # legacy fallback: name == username
#     emp = s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.name.ilike((user.username or "").strip())
#     ).first()
#     return emp

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
#         return html.Nav([
#             dcc.Link("My Assets", href="/assets"), html.Span(" | "),
#             dcc.Link("Requests", href="/requests"), html.Span(" | "),
#             dcc.Link("My Profile", href="/profile"), html.Span(" | "),
#             dcc.Link("Logout", href="/logout"),
#         ], style={"marginBottom": "10px"})
#     return html.Nav([
#         dcc.Link("Dashboard", href="/"), html.Span(" | "),
#         dcc.Link("Assets", href="/assets"), html.Span(" | "),
#         dcc.Link("Requests", href="/requests"), html.Span(" | "),
#         dcc.Link("Employees", href="/employees"), html.Span(" | "),
#         dcc.Link("Reports", href="/reports"), html.Span(" | "),
#         dcc.Link("Logout", href="/logout"),
#     ], style={"marginBottom": "10px"})

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
#     return html.Div([navbar(), html.H3(f"Dashboard — {role_name(user.role.value)} ({scope})"), html.Div(id="dashboard-cards")])

# def _uploader_component():
#     return dcc.Upload(
#         id='upload-bill',
#         children=html.Button("Upload Bill / Drag & Drop"),
#         multiple=False,
#         style={"border": "2px dashed #bbb","borderRadius": "10px","padding": "12px","display": "inline-block","cursor": "pointer","marginBottom": "8px"}
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
#         dcc.ConfirmDialog(id="req-dialog"),
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
#     return html.Div([
#         navbar(),
#         html.H3("Reports"),
#         html.Div(id="reports-content"),
#         dcc.ConfirmDialog(id="reports-dialog"),
#         html.Div(id="reports-msg", style={"color":"crimson", "marginTop":"6px"}),
#     ])

# def employees_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role != Role.OM:
#         return html.Div([navbar(), html.Div("Only Office Managers can manage employees.")])
#     return html.Div([
#         navbar(),
#         html.H3("Manage Employees"),
#         dcc.Input(id="emp-new-name", placeholder="Employee name *", style={"width":"300px"}),
#         dcc.Input(id="emp-new-phone", placeholder="Phone", style={"width":"300px"}),
#         dcc.Input(id="emp-new-username", placeholder="Username *", style={"width":"300px"}),
#         dcc.Input(id="emp-new-password", placeholder="Password *"),
#         html.Button("Add Employee", id="emp-add-btn"),
#         dcc.ConfirmDialog(id="emp-dialog"),
#         html.Div(id="emp-add-msg", style={"color":"crimson", "marginTop":"6px"}),
#         html.Hr(),
#         html.H4("Employees in My Office"),
#         html.Div(id="emp-table")
#     ])

# def profile_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([navbar(), html.H3("My Profile"), html.Div(id="profile-form"),
#                      dcc.ConfirmDialog(id="profile-dialog"),
#                      html.Div(id="profile-msg", style={"color":"crimson", "marginTop":"6px"})])

# app.layout = html.Div([dcc.Location(id="url"), html.Div(id="page-content")])

# # ---------- Routes ----------
# @app.callback(Output("page-content", "children"), Input("url", "pathname"))
# def route(path):
#     user = current_user()
#     if path == "/logout":
#         session.clear()
#         return login_layout()
#     if not user:
#         return login_layout()
#     if path in ("/", None):
#         return dashboard_layout()
#     if path == "/assets":
#         return assets_layout()
#     if path == "/requests":
#         return requests_layout()
#     if path == "/reports":
#         return reports_layout()
#     if path == "/employees":
#         return employees_layout()
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

# # ---------- Dashboard ----------
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
#             emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#             assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#             ).all()
#             total_assets_cost = sum(a.price * a.quantity for a in assets)
#         return html.Div([
#             html.Div([html.H4("Total Asset Cost"), html.H3(f"${total_assets_cost:,.2f}")],
#                      style={"padding":"10px","border":"1px solid #eee","borderRadius":"10px","display":"inline-block"})
#         ])

# # ---------- Assets ----------
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
#     try: price_val = float(price)
#     except Exception: price_val = 0.0
#     try: qty_val = int(qty or 0)
#     except Exception: qty_val = 0
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
#         with open(saved_path, "wb") as f: f.write(decoded)

#     with SessionLocal() as s:
#         if user.role == Role.EMP:
#             emp = _employee_for_user(user, s)
#             if not emp:
#                 return ("No employee profile found for you.", render_assets_table(), "", False, name, price, qty, contents)
#             s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
#                         allocation_type=AllocationType.EMPLOYEE, allocation_id=emp.id))
#             s.commit()
#             return ("", render_assets_table(), "Asset added to your profile.", True, "", "", 1, None)
#         s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path))
#         s.commit()
#     return ("", render_assets_table(), "Asset added.", True, "", "", 1, None)

# def _bill_link(a):
#     """Return a markdown link; DataTable renders it and the Flask route forces download."""
#     if not a.bill_path:
#         return ""
#     base = os.path.basename(a.bill_path)
#     return f"[{base}](/uploads/{base})"

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
#             rows = [{"asset_no": i, "name": a.name, "price": a.price, "qty": a.quantity, "bill": _bill_link(a)}
#                     for i, a in enumerate(assets, start=1)]
#             cols = [
#                 {"name":"asset_no","id":"asset_no"},
#                 {"name":"name","id":"name"},
#                 {"name":"price","id":"price"},
#                 {"name":"qty","id":"qty"},
#                 {"name":"bill","id":"bill","presentation":"markdown"},
#             ]
#             return dash_table.DataTable(data=rows, columns=cols, page_size=10, style_table={"overflowX":"auto"})
#         assets = s.query(Asset).all()
#         rows = [{"id":a.id,"name":a.name,"price":a.price,"qty":a.quantity,"bill":_bill_link(a),
#                  "allocation":a.allocation_type.value,"allocation_id":a.allocation_id} for a in assets]
#         cols = [
#             {"name":"id","id":"id"},
#             {"name":"name","id":"name"},
#             {"name":"price","id":"price"},
#             {"name":"qty","id":"qty"},
#             {"name":"bill","id":"bill","presentation":"markdown"},
#             {"name":"allocation","id":"allocation"},
#             {"name":"allocation_id","id":"allocation_id"},
#         ]
#         return dash_table.DataTable(data=rows, columns=cols, page_size=10, style_table={"overflowX":"auto"})

# @server.route("/uploads/<path:path>")
# def serve_file(path):
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
#                 dcc.Dropdown(id="req-employee", options=options, value=(emp.id if emp else None), disabled=True),
#                 dcc.Input(id="req-asset-name", placeholder="Asset name"),
#                 dcc.Input(id="req-qty", type="number", value=1),
#                 html.Button("Submit Request", id="req-submit", type="button", n_clicks=0),
#                 html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#             ])
#         employees = s.query(Employee).filter(Employee.office_id == user.office_id).all() \
#             if user.role == Role.OM else s.query(Employee).all()
#         options = [{"label": e.name, "value": e.id} for e in employees]
#         return html.Div([
#             html.H4("Create Request"),
#             dcc.Dropdown(id="req-employee", options=options, placeholder="Employee"),
#             dcc.Input(id="req-asset-name", placeholder="Asset name"),
#             dcc.Input(id="req-qty", type="number", value=1),
#             html.Button("Submit Request", id="req-submit", type="button", n_clicks=0),
#             html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#         ])

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
#     try: qty = int(qty or 0)
#     except Exception: qty = 0
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
#         s.add(Request(employee_id=emp.id, office_id=emp.office_id, asset_name=asset_name, quantity=qty))
#         s.commit()
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
#             q = q.filter(Request.employee_id == (emp.id if emp else -1))
#         rows = q.order_by(Request.created_at.desc()).all()
#         data = [{"id":r.id,"employee_id":r.employee_id,"office_id":r.office_id,"asset":r.asset_name,
#                  "qty":r.quantity,"status":r.status.value,"remark":r.remark or "",
#                  "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")} for r in rows]
#     cols = [{"name": n, "id": n} for n in ["id","employee_id","office_id","asset","qty","status","remark","created_at"]]

#     controls = html.Div([
#         dcc.Textarea(id="mgr-remark", placeholder="Remark…", style={"width":"100%","height":"60px"}),
#         html.Button("Approve", id="btn-approve"),
#         html.Button("Reject", id="btn-reject"),
#         html.Button("Mark Return Pending", id="btn-return-pending"),
#         html.Button("Mark Returned", id="btn-returned"),
#         html.Div(id="req-action-msg", style={"marginTop":"6px"})
#     ]) if user.role in (Role.GM, Role.OM) else html.Div()

#     return html.Div([dash_table.DataTable(data=data, columns=cols, id="req-table", row_selectable="single", page_size=10), controls])

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
#         if remark: r.remark = remark
#         s.commit()
#     return f"Status updated to {status.value}."

# # ---------- Employees (OM) ----------
# @app.callback(Output("emp-table", "children"), Input("url", "pathname"))
# def list_employees(_):
#     user = current_user()
#     if not user or user.role != Role.OM:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         emps = s.query(Employee).filter(Employee.office_id == user.office_id).order_by(Employee.id).all()
#         data = [{"id": e.id, "name": e.name, "phone": getattr(e, "phone", ""), "office_id": e.office_id} for e in emps]
#     cols = [{"name": n, "id": n} for n in ["id", "name", "phone", "office_id"]]
#     return dash_table.DataTable(data=data, columns=cols, page_size=10)

# @app.callback(
#     Output("emp-add-msg","children"),
#     Output("emp-dialog","message"),
#     Output("emp-dialog","displayed"),
#     Output("emp-new-name","value"),
#     Output("emp-new-phone","value"),
#     Output("emp-new-username","value"),
#     Output("emp-new-password","value"),
#     Input("emp-add-btn","n_clicks"),
#     State("emp-new-name","value"),
#     State("emp-new-phone","value"),
#     State("emp-new-username","value"),
#     State("emp-new-password","value"),
#     prevent_initial_call=True
# )
# def add_employee(n, name, phone, uname, pwd):
#     user = current_user()
#     if not user or user.role != Role.OM:
#         raise PreventUpdate
#     name = (name or "").strip()
#     uname = (uname or "").strip()
#     pwd = (pwd or "")
#     if not name or not uname or not pwd:
#         return ("Name, username and password are required.", "", False, name, phone, uname, pwd)
#     with SessionLocal() as s:
#         if s.query(User).filter(User.username == uname).first():
#             return ("Username already exists.", "", False, name, phone, uname, pwd)
#         emp = Employee(name=name, office_id=user.office_id, username=uname)
#         try: emp.phone = (phone or "").strip()
#         except Exception: pass
#         s.add(emp); s.flush()
#         s.add(User(username=uname, password_hash=generate_password_hash(pwd),
#                    role=Role.EMP, office_id=user.office_id))
#         s.commit()
#     return ("", "Employee created and login set.", True, "", "", "", "")

# # ---------- Reports ----------
# @app.callback(Output("reports-content","children"), Input("url","pathname"))
# def render_reports(_):
#     user = current_user()
#     if not user or user.role == Role.EMP:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         if user.role == Role.OM:
#             emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#             office_assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#             ).all()
#             office_count = len(office_assets)
#             office_cost = sum(a.price * a.quantity for a in office_assets)
#             emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#         else:
#             office_assets = s.query(Asset).all()
#             office_count = len(office_assets)
#             office_cost = sum(a.price * a.quantity for a in office_assets)
#             emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee)]
#     return html.Div([
#         html.Div([html.B("Assets allocated to my office: "), f"{office_count}"]),
#         html.Div([html.B("Total asset cost for my office: "), f"${office_cost:,.2f}"]),
#         html.Hr(),
#         html.Div([html.B("Per-Employee Analytics")]),
#         dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee"),
#         html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
#         html.Hr(),
#         html.Div([html.B("Add Remark for Employee")]),
#         dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee"),
#         dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", style={"width":"100%","height":"80px"}),
#         html.Button("Add Remark", id="rep-add-remark"),
#         html.Div(id="rep-remark-msg", style={"marginTop":"6px","color":"crimson"})
#     ])

# @app.callback(Output("rep-emp-kpis","children"), Input("rep-emp","value"), prevent_initial_call=True)
# def per_employee_kpis(emp_id):
#     user = current_user()
#     if not user or not emp_id:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         assets = s.query(Asset).filter(Asset.allocation_type == AllocationType.EMPLOYEE,
#                                        Asset.allocation_id == emp_id).all()
#         count = len(assets)
#         pending = sum(1 for a in assets if not a.returned)
#         cost = sum(a.price * a.quantity for a in assets)
#     return html.Ul([
#         html.Li(f"Resources this employee has: {count}"),
#         html.Li(f"Pending resources (not returned): {pending}"),
#         html.Li(f"Total asset cost for this employee: ${cost:,.2f}")
#     ])

# @app.callback(Output("rep-remark-msg","children"),
#               Input("rep-add-remark","n_clicks"),
#               State("rep-emp-remark","value"),
#               State("rep-remark-text","value"),
#               prevent_initial_call=True)
# def add_remark(n, emp_id, textv):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     if not emp_id or not (textv or "").strip():
#         return "Select an employee and enter a remark."
#     with SessionLocal() as s:
#         s.add(Remark(author_user_id=user.id, target_type="EMPLOYEE", target_id=int(emp_id), content=(textv or "").strip()))
#         s.commit()
#     return "Remark added."

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

# @app.callback(Output("profile-dialog","message"),
#               Output("profile-dialog","displayed"),
#               Output("profile-msg","children"),
#               Input("btn-save-profile","n_clicks"),
#               State("profile-emp-name","value"),
#               State("profile-phone","value"),
#               prevent_initial_call=True)
# def save_profile(n, name, phone):
#     user = current_user()
#     if not user:
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
#         try: emp.phone = phone
#         except Exception: pass
#         s.commit()
#     return "Profile updated.", True, ""

# # ---------- Run ----------
# if __name__ == "__main__":
#     app.run(debug=True)




from sqlalchemy.orm import joinedload
from sqlalchemy import text
import os, datetime
from functools import wraps

import dash
from dash import Dash, html, dcc, Input, Output, State, dash_table
from dash.exceptions import PreventUpdate
from werkzeug.security import check_password_hash, generate_password_hash
from flask import session, send_from_directory

from db import (
    init_db, SessionLocal, Role, AllocationType, RequestStatus,
    Office, User, Employee, Asset, Request, Remark, engine
)

# ---------- tiny migrations (idempotent) ----------
def _safe_add_column(table, coldef):
    try:
        with engine.begin() as conn:
            cols = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            names = {c[1] for c in cols}
            cname = coldef.split()[0]
            if cname not in names:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {coldef}"))
    except Exception:
        pass

_safe_add_column("employees", "phone VARCHAR")
_safe_add_column("employees", "username VARCHAR")

UPLOAD_FOLDER = os.environ.get("RMS_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize DB
if not os.path.exists("rms.db"):
    init_db(seed=True)
else:
    init_db(seed=False)

# Dash
app = Dash(__name__, suppress_callback_exceptions=True, serve_locally=False)
server = app.server
server.secret_key = os.environ.get("RMS_SECRET", "dev-secret-key")

# ---------- Helpers ----------
def current_user():
    """SA 2.x safe version (use Session.get instead of Query.get)."""
    uid = session.get("user_id")
    if not uid:
        return None
    with SessionLocal() as s:
        u = s.get(User, uid)
        if not u:
            return None
        # warm relation while session is open
        if u.office_id:
            _ = s.get(Office, u.office_id)
        return u

def _employee_for_user(user, s):
    if not user or not user.office_id:
        return None
    # strict username link
    emp = s.query(Employee).filter(
        Employee.office_id == user.office_id,
        Employee.username == user.username
    ).first()
    if emp:
        return emp
    # legacy fallback: employee.name == username
    return s.query(Employee).filter(
        Employee.office_id == user.office_id,
        Employee.name.ilike((user.username or "").strip())
    ).first()

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
        return html.Nav([
            dcc.Link("My Assets", href="/assets"), html.Span(" | "),
            dcc.Link("Requests", href="/requests"), html.Span(" | "),
            dcc.Link("My Profile", href="/profile"), html.Span(" | "),
            dcc.Link("Logout", href="/logout"),
        ], style={"marginBottom": "10px"})
    return html.Nav([
        dcc.Link("Dashboard", href="/"), html.Span(" | "),
        dcc.Link("Assets", href="/assets"), html.Span(" | "),
        dcc.Link("Requests", href="/requests"), html.Span(" | "),
        dcc.Link("Employees", href="/employees"), html.Span(" | "),
        dcc.Link("Reports", href="/reports"), html.Span(" | "),
        dcc.Link("Logout", href="/logout"),
    ], style={"marginBottom": "10px"})

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
    return html.Div([navbar(), html.H3(f"Dashboard — {role_name(user.role.value)} ({scope})"),
                     html.Div(id="dashboard-cards")])

def _uploader_component():
    return dcc.Upload(
        id='upload-bill',
        children=html.Button("Upload Bill / Drag & Drop"),
        multiple=False,
        style={"border": "2px dashed #bbb","borderRadius": "10px","padding": "12px",
               "display": "inline-block","cursor": "pointer","marginBottom": "8px"}
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
        dcc.ConfirmDialog(id="req-dialog"),
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
    return html.Div([
        navbar(),
        html.H3("Reports"),
        html.Div(id="reports-content"),
        dcc.ConfirmDialog(id="reports-dialog"),
        html.Div(id="reports-msg", style={"color":"crimson", "marginTop":"6px"}),
    ])

def employees_layout():
    user = current_user()
    if not user:
        return login_layout()
    if user.role != Role.OM:
        return html.Div([navbar(), html.Div("Only Office Managers can manage employees.")])
    return html.Div([
        navbar(),
        html.H3("Manage Employees"),
        dcc.Input(id="emp-new-name", placeholder="Employee name *", style={"width":"300px"}),
        dcc.Input(id="emp-new-phone", placeholder="Phone", style={"width":"300px"}),
        dcc.Input(id="emp-new-username", placeholder="Username *", style={"width":"300px"}),
        dcc.Input(id="emp-new-password", placeholder="Password *"),
        html.Button("Add Employee", id="emp-add-btn"),
        dcc.ConfirmDialog(id="emp-dialog"),
        html.Div(id="emp-add-msg", style={"color":"crimson", "marginTop":"6px"}),
        html.Hr(),
        html.H4("Employees in My Office"),
        html.Div(id="emp-table")
    ])

def profile_layout():
    user = current_user()
    if not user:
        return login_layout()
    return html.Div([navbar(), html.H3("My Profile"), html.Div(id="profile-form"),
                     dcc.ConfirmDialog(id="profile-dialog"),
                     html.Div(id="profile-msg", style={"color":"crimson", "marginTop":"6px"})])

app.layout = html.Div([dcc.Location(id="url"), html.Div(id="page-content")])

# ---------- Routes ----------
@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def route(path):
    user = current_user()
    if path == "/logout":
        session.clear()
        return login_layout()
    if not user:
        return login_layout()
    if path in ("/", None):
        return dashboard_layout()
    if path == "/assets":
        return assets_layout()
    if path == "/requests":
        return requests_layout()
    if path == "/reports":
        return reports_layout()
    if path == "/employees":
        return employees_layout()
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

# ---------- Dashboard KPIs ----------
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
            emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
            assets = s.query(Asset).filter(
                ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
                ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
            ).all()
            total_assets_cost = sum(a.price * a.quantity for a in assets)
        return html.Div([
            html.Div([html.H4("Total Asset Cost"), html.H3(f"${total_assets_cost:,.2f}")],
                     style={"padding":"10px","border":"1px solid #eee","borderRadius":"10px","display":"inline-block"})
        ])

# ---------- Assets ----------
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
    try: price_val = float(price)
    except Exception: price_val = 0.0
    try: qty_val = int(qty or 0)
    except Exception: qty_val = 0
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
        with open(saved_path, "wb") as f: f.write(decoded)

    with SessionLocal() as s:
        if user.role == Role.EMP:
            emp = _employee_for_user(user, s)
            if not emp:
                return ("No employee profile found for you.", render_assets_table(), "", False, name, price, qty, contents)
            s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
                        allocation_type=AllocationType.EMPLOYEE, allocation_id=emp.id))
            s.commit()
            return ("", render_assets_table(), "Asset added to your profile.", True, "", "", 1, None)
        s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path))
        s.commit()
    return ("", render_assets_table(), "Asset added.", True, "", "", 1, None)

def _bill_link(a):
    if not a.bill_path:
        return ""
    base = os.path.basename(a.bill_path)
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
            rows = [{"asset_no": i, "name": a.name, "price": a.price, "qty": a.quantity, "bill": _bill_link(a)}
                    for i, a in enumerate(assets, start=1)]
            cols = [
                {"name":"asset_no","id":"asset_no"},
                {"name":"name","id":"name"},
                {"name":"price","id":"price"},
                {"name":"qty","id":"qty"},
                {"name":"bill","id":"bill","presentation":"markdown"},
            ]
            return dash_table.DataTable(data=rows, columns=cols, page_size=10, style_table={"overflowX":"auto"})
        assets = s.query(Asset).all()
        rows = [{"id":a.id,"name":a.name,"price":a.price,"qty":a.quantity,"bill":_bill_link(a),
                 "allocation":a.allocation_type.value,"allocation_id":a.allocation_id} for a in assets]
        cols = [
            {"name":"id","id":"id"},
            {"name":"name","id":"name"},
            {"name":"price","id":"price"},
            {"name":"qty","id":"qty"},
            {"name":"bill","id":"bill","presentation":"markdown"},
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
                dcc.Dropdown(id="req-employee", options=options, value=(emp.id if emp else None), disabled=True),
                dcc.Input(id="req-asset-name", placeholder="Asset name"),
                dcc.Input(id="req-qty", type="number", value=1),
                html.Button("Submit Request", id="req-submit", type="button", n_clicks=0),
                html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
            ])
        employees = s.query(Employee).filter(Employee.office_id == user.office_id).all() \
            if user.role == Role.OM else s.query(Employee).all()
        options = [{"label": e.name, "value": e.id} for e in employees]
        return html.Div([
            html.H4("Create Request"),
            dcc.Dropdown(id="req-employee", options=options, placeholder="Employee"),
            dcc.Input(id="req-asset-name", placeholder="Asset name"),
            dcc.Input(id="req-qty", type="number", value=1),
            html.Button("Submit Request", id="req-submit", type="button", n_clicks=0),
            html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
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
    try: qty = int(qty or 0)
    except Exception: qty = 0
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
        s.add(Request(employee_id=emp.id, office_id=emp.office_id, asset_name=asset_name, quantity=qty))
        s.commit()
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
            q = q.filter(Request.employee_id == (emp.id if emp else -1))
        rows = q.order_by(Request.created_at.desc()).all()
        data = [{"id":r.id,"employee_id":r.employee_id,"office_id":r.office_id,"asset":r.asset_name,
                 "qty":r.quantity,"status":r.status.value,"remark":r.remark or "",
                 "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")} for r in rows]
    cols = [{"name": n, "id": n} for n in ["id","employee_id","office_id","asset","qty","status","remark","created_at"]]

    user = current_user()
    controls = html.Div([
        dcc.Textarea(id="mgr-remark", placeholder="Remark…", style={"width":"100%","height":"60px"}),
        html.Button("Approve", id="btn-approve"),
        html.Button("Reject", id="btn-reject"),
        html.Button("Mark Return Pending", id="btn-return-pending"),
        html.Button("Mark Returned", id="btn-returned"),
        html.Div(id="req-action-msg", style={"marginTop":"6px"})
    ]) if user and user.role in (Role.GM, Role.OM) else html.Div()

    return html.Div([dash_table.DataTable(data=data, columns=cols, id="req-table", row_selectable="single", page_size=10),
                     controls])

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
        if remark: r.remark = remark
        s.commit()
    return f"Status updated to {status.value}."

# ---------- Employees (OM) ----------
@app.callback(Output("emp-table", "children"), Input("url", "pathname"))
def list_employees(_):
    user = current_user()
    if not user or user.role != Role.OM:
        raise PreventUpdate
    with SessionLocal() as s:
        emps = s.query(Employee).filter(Employee.office_id == user.office_id).order_by(Employee.id).all()
        data = [{"id": e.id, "name": e.name, "phone": getattr(e, "phone", ""), "office_id": e.office_id} for e in emps]
    cols = [{"name": n, "id": n} for n in ["id", "name", "phone", "office_id"]]
    return dash_table.DataTable(data=data, columns=cols, page_size=10)

@app.callback(
    Output("emp-add-msg","children"),
    Output("emp-dialog","message"),
    Output("emp-dialog","displayed"),
    Output("emp-new-name","value"),
    Output("emp-new-phone","value"),
    Output("emp-new-username","value"),
    Output("emp-new-password","value"),
    Input("emp-add-btn","n_clicks"),
    State("emp-new-name","value"),
    State("emp-new-phone","value"),
    State("emp-new-username","value"),
    State("emp-new-password","value"),
    prevent_initial_call=True
)
def add_employee(n, name, phone, uname, pwd):
    user = current_user()
    if not user or user.role != Role.OM:
        raise PreventUpdate
    name = (name or "").strip()
    uname = (uname or "").strip()
    pwd = (pwd or "")
    if not name or not uname or not pwd:
        return ("Name, username and password are required.", "", False, name, phone, uname, pwd)
    with SessionLocal() as s:
        if s.query(User).filter(User.username == uname).first():
            return ("Username already exists.", "", False, name, phone, uname, pwd)
        emp = Employee(name=name, office_id=user.office_id, username=uname)
        try: emp.phone = (phone or "").strip()
        except Exception: pass
        s.add(emp); s.flush()
        s.add(User(username=uname, password_hash=generate_password_hash(pwd),
                   role=Role.EMP, office_id=user.office_id))
        s.commit()
    return ("", "Employee created and login set.", True, "", "", "", "")

# ---------- Reports (GM + OM) ----------
@app.callback(Output("reports-content","children"), Input("url","pathname"))
def render_reports(_):
    user = current_user()
    if not user or user.role == Role.EMP:
        raise PreventUpdate

    with SessionLocal() as s:
        # Company totals for GM; Office totals for OM (also shown below again)
        if user.role == Role.GM:
            all_assets = s.query(Asset).all()
            company_count = len(all_assets)
            company_cost = sum(a.price * a.quantity for a in all_assets)
            company_pending = sum(1 for a in all_assets if not a.returned)

            offices = s.query(Office).order_by(Office.name).all()
            office_options = [{"label": o.name, "value": o.id} for o in offices]
            emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).order_by(Employee.name)]
            top = html.Div([
                html.Div([html.B("Company assets: "), f"{company_count}"]),
                html.Div([html.B("Company total cost: "), f"${company_cost:,.2f}"]),
                html.Div([html.B("Company pending returns: "), f"{company_pending}"]),
                html.Hr(),
                html.Div([html.B("Per-Office Analytics")]),
                dcc.Dropdown(id="rep-office", options=office_options, placeholder="Select office"),
                html.Div(id="rep-office-kpis", style={"marginTop":"8px"}),
                html.Hr(),
                html.Div([html.B("Per-Employee Analytics")]),
                dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee"),
                html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
                html.Div(id="rep-emp-assets", style={"marginTop":"8px"}),
                html.Hr(),
                html.Div([html.B("Add Remark for Employee")]),
                dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee"),
                dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", style={"width":"100%","height":"80px"}),
                html.Button("Add Remark", id="rep-add-remark"),
                html.Div(id="rep-remark-msg", style={"marginTop":"6px","color":"crimson"})
            ])
            return top

        # OM view
        emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
        office_assets = s.query(Asset).filter(
            ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
            ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
        ).all()
        office_count = len(office_assets)
        office_cost = sum(a.price * a.quantity for a in office_assets)
        office_pending = sum(1 for a in office_assets if not a.returned)
        emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).filter(Employee.office_id == user.office_id)]

    return html.Div([
        html.Div([html.B("Assets allocated to my office: "), f"{office_count}"]),
        html.Div([html.B("Total asset cost for my office: "), f"${office_cost:,.2f}"]),
        html.Div([html.B("Pending returns in my office: "), f"{office_pending}"]),
        html.Hr(),
        html.Div([html.B("Per-Employee Analytics")]),
        dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee"),
        html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
        html.Div(id="rep-emp-assets", style={"marginTop":"8px"}),
        html.Hr(),
        html.Div([html.B("Add Remark for Employee")]),
        dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee"),
        dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", style={"width":"100%","height":"80px"}),
        html.Button("Add Remark", id="rep-add-remark"),
        html.Div(id="rep-remark-msg", style={"marginTop":"6px","color":"crimson"})
    ])

# Office selector -> KPIs + employees summary (GM only)
@app.callback(Output("rep-office-kpis","children"),
              Input("rep-office","value"),
              prevent_initial_call=True)
def per_office_kpis(office_id):
    user = current_user()
    if not user or user.role != Role.GM or not office_id:
        raise PreventUpdate
    with SessionLocal() as s:
        emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == office_id)]
        assets = s.query(Asset).filter(
            ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == office_id)) |
            ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
        ).all()
        count = len(assets)
        pending = sum(1 for a in assets if not a.returned)
        cost = sum(a.price * a.quantity for a in assets)

        # employees summary for this office
        emps = s.query(Employee).filter(Employee.office_id == office_id).all()
        rows = []
        for e in emps:
            ea = [a for a in assets if a.allocation_type == AllocationType.EMPLOYEE and a.allocation_id == e.id]
            rows.append({"employee_id": e.id, "employee": e.name,
                         "assets": len(ea),
                         "pending": sum(1 for a in ea if not a.returned),
                         "cost": sum(a.price * a.quantity for a in ea)})
        table = dash_table.DataTable(
            data=rows,
            columns=[{"name":"employee_id","id":"employee_id"},
                     {"name":"employee","id":"employee"},
                     {"name":"assets","id":"assets"},
                     {"name":"pending","id":"pending"},
                     {"name":"cost","id":"cost"}],
            page_size=10
        )
    return html.Div([
        html.Ul([
            html.Li(f"Assets in this office: {count}"),
            html.Li(f"Pending returns in this office: {pending}"),
            html.Li(f"Total asset cost in this office: ${cost:,.2f}")
        ]),
        html.Div(style={"height":"8px"}),
        html.Div(table)
    ])

# Employee selector -> KPIs
@app.callback(Output("rep-emp-kpis","children"),
              Input("rep-emp","value"),
              prevent_initial_call=True)
def per_employee_kpis(emp_id):
    user = current_user()
    if not user or not emp_id:
        raise PreventUpdate
    with SessionLocal() as s:
        assets = s.query(Asset).filter(Asset.allocation_type == AllocationType.EMPLOYEE,
                                       Asset.allocation_id == emp_id).all()
        count = len(assets)
        pending = sum(1 for a in assets if not a.returned)
        cost = sum(a.price * a.quantity for a in assets)
    return html.Ul([
        html.Li(f"Resources this employee has: {count}"),
        html.Li(f"Pending returns (not returned): {pending}"),
        html.Li(f"Total asset cost for this employee: ${cost:,.2f}")
    ])

# Employee selector -> Assets table
@app.callback(Output("rep-emp-assets","children"),
              Input("rep-emp","value"),
              prevent_initial_call=True)
def per_employee_assets_table(emp_id):
    user = current_user()
    if not user or not emp_id:
        raise PreventUpdate
    with SessionLocal() as s:
        assets = s.query(Asset).filter(Asset.allocation_type == AllocationType.EMPLOYEE,
                                       Asset.allocation_id == emp_id).all()
        rows = [{"id": a.id, "name": a.name, "price": a.price, "qty": a.quantity,
                 "returned": bool(a.returned), "bill": _bill_link(a)} for a in assets]
    cols = [{"name":"id","id":"id"},
            {"name":"name","id":"name"},
            {"name":"price","id":"price"},
            {"name":"qty","id":"qty"},
            {"name":"returned","id":"returned"},
            {"name":"bill","id":"bill","presentation":"markdown"}]
    return dash_table.DataTable(data=rows, columns=cols, page_size=10, style_table={"overflowX":"auto"})

# Remarks (GM & OM)
@app.callback(Output("rep-remark-msg","children"),
              Input("rep-add-remark","n_clicks"),
              State("rep-emp-remark","value"),
              State("rep-remark-text","value"),
              prevent_initial_call=True)
def add_remark(n, emp_id, textv):
    user = current_user()
    if not user:
        raise PreventUpdate
    if not emp_id or not (textv or "").strip():
        return "Select an employee and enter a remark."
    with SessionLocal() as s:
        s.add(Remark(author_user_id=user.id, target_type="EMPLOYEE",
                     target_id=int(emp_id), content=(textv or "").strip()))
        s.commit()
    return "Remark added."

# ---------- Profile ----------
@app.callback(Output("profile-form", "children"), Input("url", "pathname"))
def load_profile(_):
    user = current_user()
    if not user:
        raise PreventUpdate
    with SessionLocal() as s:
        emp = _employee_for_user(user, s) if user.role == Role.EMP else None
        office = emp.office if emp else (s.get(Office, user.office_id) if user.office_id else None)

        # recent remarks for employee
        remarks_block = html.Div()
        if emp:
            rws = s.query(Remark).filter(
                Remark.target_type == "EMPLOYEE", Remark.target_id == emp.id
            ).order_by(Remark.created_at.desc()).limit(10).all()
            remarks_block = html.Div([
                html.H4("Manager Remarks"),
                html.Ul([html.Li(f"{r.content} — {r.created_at.strftime('%Y-%m-%d %H:%M')}") for r in rws])
            ], style={"marginTop":"10px"})

        return html.Div([
            html.Div([
                html.Div(f"Employee ID: {emp.id if emp else '—'}"),
                html.Div(f"Office ID: {office.id if office else '—'}"),
                html.Div(f"Office Name: {office.name if office else '—'}"),
            ], style={"marginBottom":"8px"}),
            dcc.Input(id="profile-emp-name", placeholder="Employee name", value=(emp.name if emp else "")),
            dcc.Input(id="profile-phone", placeholder="Phone number", value=getattr(emp, "phone", "") if emp else ""),
            html.Button("Save Profile", id="btn-save-profile", n_clicks=0, type="button"),
            remarks_block
        ])

@app.callback(Output("profile-dialog","message"),
              Output("profile-dialog","displayed"),
              Output("profile-msg","children"),
              Input("btn-save-profile","n_clicks"),
              State("profile-emp-name","value"),
              State("profile-phone","value"),
              prevent_initial_call=True)
def save_profile(n, name, phone):
    user = current_user()
    if not user:
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
        try: emp.phone = phone
        except Exception: pass
        s.commit()
    return "Profile updated.", True, ""

# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)
