# # app.py
# from sqlalchemy import text
# import os, datetime, base64
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

# # ---------- tiny migrations (idempotent) ----------
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

# # ---------- Dash ----------
# app = Dash(__name__, suppress_callback_exceptions=True, serve_locally=False)
# server = app.server
# server.secret_key = os.environ.get("RMS_SECRET", "dev-secret-key")

# # 🌈 Glassmorphism + pastel UI (no external CSS needed)
# app.index_string = """
# <!DOCTYPE html>
# <html>
# <head>
#   <meta charset="UTF-8">
#   <title>RMS</title>
#   <link rel="preconnect" href="https://fonts.googleapis.com">
#   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
#   <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
#   {%metas%}
#   {%favicon%}
#   {%css%}
#   <style>
#     :root{
#       --bg1:#eaf2ff; --bg2:#ffffff;
#       --glass:rgba(255,255,255,.55);
#       --text:#101426; --muted:#6b7280;
#       --primary:#6aa1ff; --primary-600:#4f8cff;
#       --danger:#ef4444; --success:#10b981;
#       --border:rgba(51,65,85,.18);
#       --shadow:0 10px 30px rgba(31,38,135,.18);
#       --radius:16px;
#     }
#     html,body{height:100%;}
#     body{
#       margin:0; padding:28px;
#       background:
#         radial-gradient(1200px 600px at 10% 10%, #f7fbff 0%, transparent 55%),
#         radial-gradient(900px 500px at 80% 20%, #f6f0ff 0%, transparent 60%),
#         linear-gradient(180deg, var(--bg1), var(--bg2));
#       font-family:'Inter',system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial;
#       color:var(--text); line-height:1.35;
#     }

#     nav{
#       backdrop-filter:saturate(180%) blur(14px);
#       background:var(--glass);
#       border:1px solid var(--border);
#       border-radius:var(--radius);
#       box-shadow:var(--shadow);
#       padding:12px 14px; margin-bottom:18px;
#     }
#     nav a{ color:var(--text); text-decoration:none; font-weight:600; padding:6px 10px; border-radius:12px; }
#     nav a:hover{ background:rgba(99,102,241,.09); color:#1f2937; }

#     h2,h3,h4{ margin:8px 0 12px 0; }
#     .card{
#       backdrop-filter:saturate(180%) blur(16px);
#       background:var(--glass);
#       border:1px solid var(--border);
#       border-radius:var(--radius);
#       box-shadow:var(--shadow);
#       padding:16px; margin:12px 0;
#     }

#     .btn{ background:linear-gradient(90deg, var(--primary), #9cc1ff);
#           color:white; border:none; padding:9px 14px; border-radius:12px;
#           font-weight:600; cursor:pointer; transition:.15s transform ease, .15s box-shadow ease; }
#     .btn:hover{ transform:translateY(-1px); box-shadow:0 8px 18px rgba(99,102,241,.25); }
#     .btn-outline{ background:transparent; color:var(--primary); border:1px solid var(--primary); }
#     .btn-danger{ background:linear-gradient(90deg, #f87171, #ef4444); color:white; }
#     .btn-success{ background:linear-gradient(90deg, #34d399, #10b981); color:white; }

#     .input, .dash-dropdown, textarea{
#       padding:10px 12px; border:1px solid var(--border); border-radius:12px;
#       background:rgba(255,255,255,.7); outline:none; width:100%; max-width:560px;
#       margin-right:8px; margin-bottom:8px;
#     }
#     .two-col{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }
#     .stack{ display:flex; flex-wrap:wrap; gap:10px; align-items:center; }

#     .kpi{
#       display:inline-block; min-width:210px; padding:16px 18px; margin-right:10px;
#       border:1px solid var(--border); border-radius:18px; box-shadow:var(--shadow);
#       background:rgba(255,255,255,.6);
#     }
#     .kpi .label{ color:#6b7280; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.06em;}
#     .kpi .value{ font-size:22px; font-weight:800; margin-top:4px;}
#     .hr{ height:1px; background:var(--border); margin:16px 0;}
#     .muted{ color:#6b7280; }

#     /* Dash DataTable light glass look */
#     .dash-table-container .dash-spreadsheet-container{
#       backdrop-filter:saturate(180%) blur(10px);
#       background:rgba(255,255,255,.55);
#       border:1px solid var(--border);
#       border-radius:12px; box-shadow:var(--shadow);
#       padding:6px;
#     }
#     .dash-table-container .dash-spreadsheet-container .dash-spreadsheet td,
#     .dash-table-container .dash-spreadsheet-container .dash-spreadsheet th{
#       border-color:rgba(100,116,139,.25) !important;
#     }
#   </style>
# </head>
# <body>
#   {%app_entry%}
#   <footer>{%config%}{%scripts%}{%renderer%}</footer>
# </body>
# </html>
# """

# # ---------- Helpers ----------
# def current_user():
#     """Load user; pre-touch office id only (avoid DetachedInstanceError)."""
#     uid = session.get("user_id")
#     if not uid:
#         return None
#     with SessionLocal() as s:
#         u = s.get(User, uid)
#         if not u:
#             return None
#         # we only rely on u.office_id, not lazy-loading u.office later
#         return u

# def _employee_for_user(user, s):
#     if not user or not user.office_id:
#         return None
#     # First try username link
#     emp = s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.username == user.username
#     ).first()
#     if emp:
#         return emp
#     # Fallback by name == username
#     return s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.name.ilike((user.username or "").strip())
#     ).first()

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
#     items = []
#     if user.role == Role.EMP:
#         items = [
#             dcc.Link("Dashboard", href="/"), html.Span("  "),
#             dcc.Link("My Assets", href="/assets"), html.Span("  "),
#             dcc.Link("Requests", href="/requests"), html.Span("  "),
#             dcc.Link("My Profile", href="/profile"), html.Span("  "),
#         ]
#     else:
#         items = [
#             dcc.Link("Dashboard", href="/"), html.Span("  "),
#             dcc.Link("Assets", href="/assets"), html.Span("  "),
#             dcc.Link("Requests", href="/requests"), html.Span("  "),
#             dcc.Link("Reports", href="/reports"), html.Span("  "),
#         ]
#         if user.role == Role.GM:
#             items.extend([dcc.Link("Admin", href="/admin"), html.Span("  ")])
#         else:
#             items.extend([dcc.Link("Employees", href="/employees"), html.Span("  ")])
#     items.append(dcc.Link("Logout", href="/logout"))
#     return html.Nav(items)

# def login_layout():
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H2("Resource Management System — Login"),
#             dcc.Input(id="login-username", placeholder="Username", className="input"),
#             dcc.Input(id="login-password", type="password", placeholder="Password", className="input"),
#             html.Button("Login", id="login-btn", className="btn"),
#             html.Div(id="login-msg", style={"color": "crimson", "marginTop": "8px"}),
#             html.Div(className="muted", children="Demo users: admin/admin (GM), om_east/om_east (OM), alice/alice (EMP)")
#         ])
#     ])

# def dashboard_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     scope = "Company-wide" if user.role == Role.GM else "Your office"
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(f"Dashboard — {role_name(user.role.value)}"),
#             html.Div(className="muted", children=scope),
#             html.Div(id="dashboard-cards", className="pad-top")
#         ])
#     ])

# def _uploader_component():
#     return dcc.Upload(
#         id='upload-bill',
#         children=html.Button("Upload Bill / Drag & Drop", className="btn btn-outline"),
#         multiple=False
#     )

# def assets_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     header = "My Assets" if user.role == Role.EMP else "Assets"
#     button_label = "Add to My Profile" if user.role == Role.EMP else "Add Asset"
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(header),
#             _uploader_component(),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="asset-name", placeholder="Asset name *", className="input"),
#                 dcc.Input(id="asset-price", placeholder="Price *", type="number", className="input"),
#                 dcc.Input(id="asset-qty", placeholder="Quantity *", type="number", value=1, className="input"),
#             ]),
#             html.Button(button_label, id="add-asset-btn", className="btn"),
#             html.Div(id="asset-add-msg", style={"color":"crimson", "marginTop":"6px"}),
#             dcc.ConfirmDialog(id="asset-dialog"),
#         ]),
#         html.Div(className="card", children=[
#             html.H4(f"{header} Table"),
#             html.Div(id="assets-table")
#         ])
#     ])

# def requests_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Requests"),
#             html.Div(id="request-form"),
#             dcc.ConfirmDialog(id="req-dialog")
#         ]),
#         html.Div(className="card", children=[
#             html.H4("Open Requests"),
#             html.Div(id="requests-table")
#         ])
#     ])

# def reports_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role == Role.EMP:
#         return html.Div([navbar(), html.Div(className="card", children="Reports are not available for Employees.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Reports"),
#             html.Div(id="reports-content"),
#             dcc.ConfirmDialog(id="reports-dialog"),
#             html.Div(id="reports-msg", style={"color":"crimson", "marginTop":"6px"}),
#         ])
#     ])

# def employees_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role != Role.OM:
#         return html.Div([navbar(), html.Div(className="card", children="Only Office Managers can manage employees.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Manage Employees"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="emp-new-name", placeholder="Employee name *", className="input"),
#                 dcc.Input(id="emp-new-phone", placeholder="Phone", className="input"),
#                 dcc.Input(id="emp-new-username", placeholder="Username *", className="input"),
#                 dcc.Input(id="emp-new-password", placeholder="Password *", className="input"),
#             ]),
#             html.Button("Add Employee", id="emp-add-btn", className="btn"),
#             dcc.ConfirmDialog(id="emp-dialog"),
#             html.Div(id="emp-add-msg", style={"color":"crimson", "marginTop":"6px"})
#         ]),
#         html.Div(className="card", children=[
#             html.H4("Employees in My Office"),
#             html.Div(id="emp-table")
#         ])
#     ])

# def admin_layout():
#     user = current_user()
#     if not user or user.role != Role.GM:
#         return html.Div([navbar(), html.Div(className="card", children="Admins only.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Admin — Offices & Managers"),
#             html.H4("Create Office"),
#             dcc.Input(id="new-office-name", placeholder="Office name *", className="input"),
#             html.Button("Add Office", id="btn-add-office", className="btn"),
#             html.Div(id="msg-add-office", className="muted", style={"marginTop":"6px"}),
#             html.Div(className="hr"),
#             html.H4("Create Office Manager"),
#             html.Div(className="two-col", children=[
#                 dcc.Dropdown(id="om-office", placeholder="Select office", className="dash-dropdown"),
#                 dcc.Input(id="om-username", placeholder="Username *", className="input"),
#                 dcc.Input(id="om-password", placeholder="Password *", className="input"),
#             ]),
#             html.Button("Create OM", id="btn-create-om", className="btn"),
#             dcc.ConfirmDialog(id="admin-dialog"),
#             html.Div(id="msg-create-om", className="muted", style={"marginTop":"6px"}),
#             html.Div(className="hr"),
#             html.H4("Reset OM Password"),
#             html.Div(className="two-col", children=[
#                 dcc.Dropdown(id="om-existing", placeholder="Select OM user", className="dash-dropdown"),
#                 dcc.Input(id="om-new-pass", placeholder="New password *", className="input"),
#             ]),
#             html.Button("Reset Password", id="btn-om-reset", className="btn btn-outline"),
#             html.Div(id="msg-om-reset", className="muted", style={"marginTop":"6px"}),
#         ])
#     ])

# def profile_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("My Profile"),
#             html.Div(id="profile-form"),
#             dcc.ConfirmDialog(id="profile-dialog"),
#             html.Div(id="profile-msg", style={"color":"crimson", "marginTop":"6px"}),
#         ])
#     ])

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
#     if path == "/admin":
#         return admin_layout()
#     if path == "/profile":
#         return profile_layout()
#     return html.Div([navbar(), html.Div(className="card", children=html.H3("Not Found"))])

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

# # ---------- Dashboard KPIs ----------
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
#             count = s.query(Asset).count()
#             pending = s.query(Asset).filter(Asset.returned == False).count()  # noqa: E712
#         else:
#             emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#             assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#             ).all()
#             total_assets_cost = sum(a.price * a.quantity for a in assets)
#             count = len(assets)
#             pending = sum(1 for a in assets if not a.returned)
#         return html.Div(className="stack", children=[
#             html.Div(className="kpi", children=[html.Div("Assets", className="label"), html.Div(count, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Pending Returns", className="label"), html.Div(pending, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Total Cost", className="label"), html.Div(f"${total_assets_cost:,.2f}", className="value")]),
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
#             s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
#                         allocation_type=AllocationType.EMPLOYEE, allocation_id=emp.id))
#             s.commit()
#             return ("", render_assets_table(), "Asset added to your profile.", True, "", "", 1, None)
#         elif user.role == Role.OM:
#             # Default OM additions to their Office scope
#             s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
#                         allocation_type=AllocationType.OFFICE, allocation_id=user.office_id))
#             s.commit()
#             return ("", render_assets_table(), "Asset added to your office.", True, "", "", 1, None)
#         else:
#             # GM: unallocated by default
#             s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path))
#             s.commit()
#     return ("", render_assets_table(), "Asset added.", True, "", "", 1, None)

# def _bill_link(a):
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

#         elif user.role == Role.OM:
#             # STRICT office scoping: office-level + employee-level in same office
#             emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#             assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#             ).all()
#         else:
#             # GM sees all
#             assets = s.query(Asset).all()

#         rows = [{"id": a.id, "name": a.name, "price": a.price, "qty": a.quantity,
#                  "bill": _bill_link(a), "allocation": a.allocation_type.value,
#                  "allocation_id": a.allocation_id}
#                 for a in assets]
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
#                 html.B("Create Request"),
#                 dcc.Dropdown(id="req-employee", options=options, value=(emp.id if emp else None), className="dash-dropdown", disabled=True),
#                 html.Div(className="two-col", children=[
#                     dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
#                     dcc.Input(id="req-qty", type="number", value=1, className="input"),
#                 ]),
#                 html.Button("Submit Request", id="req-submit", className="btn"),
#                 html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#             ])
#         employees = s.query(Employee).filter(Employee.office_id == user.office_id).all() \
#             if user.role == Role.OM else s.query(Employee).all()
#         options = [{"label": e.name, "value": e.id} for e in employees]
#         return html.Div([
#             html.B("Create Request"),
#             dcc.Dropdown(id="req-employee", options=options, placeholder="Employee", className="dash-dropdown"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
#                 dcc.Input(id="req-qty", type="number", value=1, className="input"),
#             ]),
#             html.Button("Submit Request", id="req-submit", className="btn"),
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

#     user = current_user()
#     controls = html.Div(className="stack", children=[
#         dcc.Textarea(id="mgr-remark", placeholder="Remark…", className="input", style={"height":"60px", "width":"420px"}),
#         html.Button("Approve", id="btn-approve", className="btn btn-success"),
#         html.Button("Reject", id="btn-reject", className="btn btn-danger"),
#         html.Button("Mark Return Pending", id="btn-return-pending", className="btn btn-outline"),
#         html.Button("Mark Returned", id="btn-returned", className="btn btn-outline"),
#     ]) if user and user.role in (Role.GM, Role.OM) else html.Div()

#     table = dash_table.DataTable(data=data, columns=cols, id="req-table", row_selectable="single", page_size=10, style_table={"overflowX":"auto"})
#     return html.Div([table, html.Div(id="req-action-msg", style={"marginTop":"8px"}), controls])

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
#     return dash_table.DataTable(data=data, columns=cols, page_size=10, style_table={"overflowX":"auto"})

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

# # ---------- GM Admin ----------
# @app.callback(Output("om-office","options"), Output("om-existing","options"), Input("url","pathname"))
# @login_required(Role.GM)
# def load_admin_dropdowns(_):
#     with SessionLocal() as s:
#         offices = s.query(Office).order_by(Office.name).all()
#         oms = s.query(User).filter(User.role == Role.OM).order_by(User.username).all()
#         return (
#             [{"label": o.name, "value": o.id} for o in offices],
#             [{"label": u.username, "value": u.id} for u in oms]
#         )

# @app.callback(Output("msg-add-office","children"),
#               Input("btn-add-office","n_clicks"),
#               State("new-office-name","value"),
#               prevent_initial_call=True)
# @login_required(Role.GM)
# def add_office(n, office_name):
#     name = (office_name or "").strip()
#     if not name:
#         return "Office name is required."
#     with SessionLocal() as s:
#         if s.query(Office).filter(Office.name.ilike(name)).first():
#             return "Office already exists."
#         s.add(Office(name=name))
#         s.commit()
#     return "Office created."

# @app.callback(
#     Output("msg-create-om","children"),
#     Output("admin-dialog","message"),
#     Output("admin-dialog","displayed"),
#     Output("om-username","value"),
#     Output("om-password","value"),
#     State("om-office","value"),
#     State("om-username","value"),
#     State("om-password","value"),
#     Input("btn-create-om","n_clicks"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def create_om(office_id, uname, pwd, n):
#     uname = (uname or "").strip()
#     pwd = (pwd or "")
#     if not office_id or not uname or not pwd:
#         return ("All fields are required.", "", False, uname, pwd)
#     with SessionLocal() as s:
#         if not s.get(Office, office_id):
#             return ("Invalid office.", "", False, uname, pwd)
#         if s.query(User).filter(User.username == uname).first():
#             return ("Username already exists.", "", False, uname, pwd)
#         s.add(User(username=uname, password_hash=generate_password_hash(pwd), role=Role.OM, office_id=office_id))
#         s.commit()
#     return ("OM created.", "Office Manager created successfully.", True, "", "")

# @app.callback(
#     Output("msg-om-reset","children"),
#     State("om-existing","value"),
#     State("om-new-pass","value"),
#     Input("btn-om-reset","n_clicks"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def reset_om_password(om_id, new_pass, n):
#     new_pass = (new_pass or "").strip()
#     if not om_id or not new_pass:
#         return "Select an OM and enter a new password."
#     with SessionLocal() as s:
#         u = s.get(User, om_id)
#         if not u or u.role != Role.OM:
#             return "Invalid OM selected."
#         u.password_hash = generate_password_hash(new_pass)
#         s.commit()
#     return "Password reset."

# # ---------- Reports (GM + OM) ----------
# @app.callback(Output("reports-content","children"), Input("url","pathname"))
# def render_reports(_):
#     user = current_user()
#     if not user or user.role == Role.EMP:
#         raise PreventUpdate

#     with SessionLocal() as s:
#         if user.role == Role.GM:
#             all_assets = s.query(Asset).all()
#             company_count = len(all_assets)
#             company_cost = sum(a.price * a.quantity for a in all_assets)
#             company_pending = sum(1 for a in all_assets if not a.returned)

#             offices = s.query(Office).order_by(Office.name).all()
#             office_options = [{"label": o.name, "value": o.id} for o in offices]
#             emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).order_by(Employee.name)]

#             return html.Div([
#                 html.Div(className="stack", children=[
#                     html.Div(className="kpi", children=[html.Div("Company assets", className="label"), html.Div(company_count, className="value")]),
#                     html.Div(className="kpi", children=[html.Div("Company total cost", className="label"), html.Div(f"${company_cost:,.2f}", className="value")]),
#                     html.Div(className="kpi", children=[html.Div("Company pending returns", className="label"), html.Div(company_pending, className="value")]),
#                 ]),
#                 html.Div(className="hr"),
#                 html.B("Per-Office Analytics"),
#                 dcc.Dropdown(id="rep-office", options=office_options, placeholder="Select office", className="dash-dropdown"),
#                 html.Div(id="rep-office-kpis", style={"marginTop":"8px"}),
#                 html.Div(className="hr"),
#                 html.B("Per-Employee Analytics"),
#                 dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#                 html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
#                 html.Div(className="hr"),
#                 html.B("Add Remark for Employee"),
#                 dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#                 dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input", style={"height":"80px"}),
#                 html.Button("Add Remark", id="rep-add-remark", className="btn"),
#                 html.Div(id="rep-remark-msg", className="muted", style={"marginTop":"6px"})
#             ])

#         # OM scope
#         emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#         office_assets = s.query(Asset).filter(
#             ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#             ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#         ).all()
#         office_count = len(office_assets)
#         office_cost = sum(a.price * a.quantity for a in office_assets)
#         emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).filter(Employee.office_id == user.office_id)]

#         return html.Div([
#             html.Div(className="kpi", children=[html.Div("Assets in my office", className="label"), html.Div(office_count, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Total cost for my office", className="label"), html.Div(f"${office_cost:,.2f}", className="value")]),
#             html.Div(className="hr"),
#             html.B("Per-Employee Analytics"),
#             dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#             html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
#             html.Div(className="hr"),
#             html.B("Add Remark for Employee"),
#             dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#             dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input", style={"height":"80px"}),
#             html.Button("Add Remark", id="rep-add-remark", className="btn"),
#             html.Div(id="rep-remark-msg", className="muted", style={"marginTop":"6px"})
#         ])

# @app.callback(Output("rep-office-kpis","children"), Input("rep-office","value"), prevent_initial_call=True)
# @login_required(Role.GM)
# def per_office_kpis(office_id):
#     if not office_id:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == office_id)]
#         assets = s.query(Asset).filter(
#             ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == office_id)) |
#             ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#         ).all()
#         count = len(assets)
#         pending = sum(1 for a in assets if not a.returned)
#         cost = sum(a.price * a.quantity for a in assets)
#     return html.Ul([
#         html.Li(f"Assets in office: {count}"),
#         html.Li(f"Pending returns: {pending}"),
#         html.Li(f"Total cost: ${cost:,.2f}")
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
#         office = s.get(Office, user.office_id) if user.office_id else None
#         return html.Div([
#             html.Div([
#                 html.Div(f"User: {user.username}"),
#                 html.Div(f"Role: {role_name(user.role.value)}"),
#                 html.Div(f"Employee ID: {emp.id if emp else '—'}"),
#                 html.Div(f"Office ID: {office.id if office else '—'}"),
#                 html.Div(f"Office Name: {office.name if office else '—'}"),
#             ], style={"marginBottom":"8px"}),
#             dcc.Input(id="profile-emp-name", placeholder="Employee name", value=(emp.name if emp else ""), className="input"),
#             dcc.Input(id="profile-phone", placeholder="Phone number", value=getattr(emp, "phone", "") if emp else "", className="input"),
#             html.Button("Save Profile", id="btn-save-profile", n_clicks=0, type="button", className="btn"),
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
# ================================================== above code is base code =================================================================================================================================


# # app.py
# from sqlalchemy import text
# import os, datetime, base64
# from functools import wraps

# import dash
# from dash import Dash, html, dcc, Input, Output, State, dash_table, no_update
# from dash.exceptions import PreventUpdate
# from werkzeug.security import check_password_hash, generate_password_hash
# from flask import session, send_from_directory

# from db import (
#     init_db, SessionLocal, Role, AllocationType, RequestStatus,
#     Office, User, Employee, Asset, Request, Remark, engine
# )

# # ---------- tiny migrations (idempotent) ----------
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

# # existing employee tweaks
# _safe_add_column("employees", "phone VARCHAR")
# _safe_add_column("employees", "username VARCHAR")
# # NEW: enrich requests for price & bill
# _safe_add_column("requests", "price FLOAT")
# _safe_add_column("requests", "bill_path VARCHAR")

# UPLOAD_FOLDER = os.environ.get("RMS_UPLOAD_DIR", "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Initialize DB
# if not os.path.exists("rms.db"):
#     init_db(seed=True)
# else:
#     init_db(seed=False)

# # ---------- Dash ----------
# app = Dash(__name__, suppress_callback_exceptions=True, serve_locally=False)
# server = app.server
# server.secret_key = os.environ.get("RMS_SECRET", "dev-secret-key")

# # Pretty HTML shell + theme (Glassmorphism – light)
# app.index_string = """
# <!DOCTYPE html>
# <html>
# <head>
#   <meta charset="UTF-8">
#   <title>RMS</title>
#   <link rel="preconnect" href="https://fonts.googleapis.com">
#   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
#   <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
#   {%metas%}
#   {%favicon%}
#   {%css%}
#   <style>
#     :root{
#       --bg:#ecf2ff; --card:rgba(255,255,255,.65); --text:#0c1326; --muted:#667085;
#       --primary:#5b8cff; --primary-600:#4b7af0; --danger:#ef4444; --border:rgba(255,255,255,.45);
#       --radius:16px; --shadow:0 20px 40px rgba(94,120,255,.18);
#     }
#     html,body{height:100%;}
#     body{
#       background: radial-gradient(1200px 800px at -10% -10%, #c9d7ff, transparent 50%),
#                   radial-gradient(1200px 800px at 110% 10%, #ffe7f3, transparent 45%),
#                   radial-gradient(1000px 700px at 50% 120%, #e2ffe9, transparent 40%),
#                   #dfe7ff;
#       font-family:'Inter',system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial;
#       color:var(--text); line-height:1.35; padding:24px;
#     }
#     nav{ backdrop-filter: blur(14px); background:var(--card);
#          padding:10px 14px; border:1px solid var(--border);
#          border-radius:var(--radius); box-shadow:var(--shadow); margin-bottom:16px;}
#     nav a{ color:var(--primary); text-decoration:none; font-weight:600; margin-right:12px }
#     nav a:hover{ text-decoration:underline; }
#     h2,h3,h4{ margin:8px 0 12px 0; }
#     .card{ backdrop-filter: blur(16px); background:var(--card); border:1px solid var(--border);
#            border-radius:var(--radius); box-shadow:var(--shadow); padding:18px; margin:10px 0;}
#     .btn{ background:var(--primary); color:white; border:none; padding:9px 15px;
#           border-radius:12px; font-weight:600; cursor:pointer; transition:.15s transform ease, .15s background ease;
#           margin-right:8px; margin-top:6px;}
#     .btn:hover{ background:var(--primary-600); transform:translateY(-1px); }
#     .btn-outline{ background:transparent; color:var(--primary); border:1px solid var(--primary); }
#     .btn-danger{ background:var(--danger); }
#     .input, .dash-dropdown, textarea{ padding:9px 12px; border:1px solid var(--border); border-radius:12px;
#        background:rgba(255,255,255,.8); outline:none; width:100%; max-width:560px; margin-right:8px; margin-bottom:8px;}
#     .two-col{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }
#     .kpi{ display:inline-block; min-width:210px; padding:14px 16px; margin-right:10px;
#           background:linear-gradient(180deg, rgba(255,255,255,.8), rgba(255,255,255,.6));
#           border:1px solid var(--border); border-radius:16px; box-shadow:var(--shadow); }
#     .kpi .label{ color:#6b7280; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.06em;}
#     .kpi .value{ font-size:22px; font-weight:700; margin-top:4px;}
#     .hr{ height:1px; background:linear-gradient(90deg, transparent, var(--border), transparent); margin:16px 0;}
#     .muted{ color:#6b7280; }
#     .stack{ display:flex; flex-wrap:wrap; gap:8px; align-items:center;}
#     .tiny{ font-size:12px; color:#6b7280; }
#   </style>
# </head>
# <body>
#   {%app_entry%}
#   <footer>{%config%}{%scripts%}{%renderer%}</footer>
# </body>
# </html>
# """

# # ---------- Helpers ----------
# def current_user():
#     """Load user and pre-touch office to avoid DetachedInstanceError."""
#     uid = session.get("user_id")
#     if not uid:
#         return None
#     with SessionLocal() as s:
#         u = s.get(User, uid)
#         if not u:
#             return None
#         if u.office_id:
#             _ = s.get(Office, u.office_id)
#         return u

# def _employee_for_user(user, s):
#     if not user or not user.office_id:
#         return None
#     emp = s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.username == user.username
#     ).first()
#     if emp:
#         return emp
#     return s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.name.ilike((user.username or "").strip())
#     ).first()

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

# def _short_name(path):
#     if not path: return ""
#     base = os.path.basename(path)
#     if len(base) <= 18: return base
#     name, ext = os.path.splitext(base)
#     return (name[:8] + "…" + name[-4:] + ext) if len(name) > 12 else base

# # ---------- Layouts ----------
# def navbar():
#     user = current_user()
#     if not user:
#         return html.Nav([])
#     items = []
#     if user.role == Role.EMP:
#         items = [
#             dcc.Link("Dashboard", href="/"),
#             dcc.Link("My Assets", href="/assets"),
#             dcc.Link("Requests", href="/requests"),
#             dcc.Link("My Profile", href="/profile"),
#         ]
#     else:
#         items = [
#             dcc.Link("Dashboard", href="/"),
#             dcc.Link("Assets", href="/assets"),
#             dcc.Link("Requests", href="/requests"),
#             dcc.Link("Reports", href="/reports"),
#         ]
#         if user.role == Role.GM:
#             items.append(dcc.Link("Admin", href="/admin"))
#         else:
#             items.append(dcc.Link("Employees", href="/employees"))
#     items.append(dcc.Link("Logout", href="/logout"))
#     return html.Nav(items)

# def login_layout():
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H2("Resource Management System — Login"),
#             dcc.Input(id="login-username", placeholder="Username", className="input"),
#             dcc.Input(id="login-password", type="password", placeholder="Password", className="input"),
#             html.Button("Login", id="login-btn", className="btn"),
#             html.Div(id="login-msg", style={"color": "crimson", "marginTop": "8px"}),
#             html.Div(className="muted", children="Default demo users: admin/admin, om_east/om_east, alice/alice")
#         ])
#     ])

# def dashboard_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     scope = "Company-wide" if user.role == Role.GM else "Your office"
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(f"Dashboard — {role_name(user.role.value)}"),
#             html.Div(className="muted", children=scope),
#             html.Div(id="dashboard-cards", className="pad-top")
#         ])
#     ])

# def _uploader_component(id_):
#     return dcc.Upload(
#         id=id_,
#         children=html.Button("Upload Bill / Drag & Drop", className="btn btn-outline"),
#         multiple=False
#     )

# def assets_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     header = "My Assets" if user.role == Role.EMP else "Assets"
#     button_label = "Add to My Profile" if user.role == Role.EMP else "Add Asset"
#     allocation_controls = html.Div()
#     if user.role == Role.GM:
#         allocation_controls = html.Div(className="two-col", children=[
#             dcc.RadioItems(
#                 id="asset-alloc-type",
#                 options=[
#                     {"label":"Global / Unallocated","value":"UNALLOCATED"},
#                     {"label":"Allocate to Office","value":"OFFICE"},
#                     {"label":"Allocate to Employee","value":"EMPLOYEE"},
#                 ],
#                 value="UNALLOCATED",
#                 inputStyle={"marginRight":"6px"},
#                 labelStyle={"display":"block","marginBottom":"6px"}
#             ),
#             html.Div(id="asset-alloc-target")
#         ])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(header),
#             _uploader_component("upload-bill"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="asset-name", placeholder="Asset name *", className="input"),
#                 dcc.Input(id="asset-price", placeholder="Price *", type="number", className="input"),
#                 dcc.Input(id="asset-qty", placeholder="Quantity *", type="number", value=1, className="input"),
#             ]),
#             allocation_controls,
#             html.Button(button_label, id="add-asset-btn", className="btn"),
#             html.Div(id="asset-add-msg", style={"color":"crimson", "marginTop":"6px"}),
#             dcc.ConfirmDialog(id="asset-dialog"),
#         ]),
#         html.Div(className="card", children=[
#             html.H4(f"{header} Table"),
#             html.Div(id="assets-table")
#         ])
#     ])

# def requests_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Requests"),
#             html.Div(id="request-form"),
#             dcc.ConfirmDialog(id="req-dialog")
#         ]),
#         html.Div(className="card", children=[
#             html.H4("Open Requests"),
#             html.Div(id="requests-table")
#         ])
#     ])

# def reports_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role == Role.EMP:
#         return html.Div([navbar(), html.Div(className="card", children="Reports are not available for Employees.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Reports"),
#             html.Div(id="reports-content"),
#             dcc.ConfirmDialog(id="reports-dialog"),
#             html.Div(id="reports-msg", style={"color":"crimson", "marginTop":"6px"}),
#         ])
#     ])

# def employees_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role != Role.OM:
#         return html.Div([navbar(), html.Div(className="card", children="Only Office Managers can manage employees.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Manage Employees"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="emp-new-name", placeholder="Employee name *", className="input"),
#                 dcc.Input(id="emp-new-phone", placeholder="Phone", className="input"),
#                 dcc.Input(id="emp-new-username", placeholder="Username *", className="input"),
#                 dcc.Input(id="emp-new-password", placeholder="Password *", className="input"),
#             ]),
#             html.Button("Add Employee", id="emp-add-btn", className="btn"),
#             dcc.ConfirmDialog(id="emp-dialog"),
#             html.Div(id="emp-add-msg", style={"color":"crimson", "marginTop":"6px"})
#         ]),
#         html.Div(className="card", children=[
#             html.H4("Employees in My Office"),
#             html.Div(id="emp-table")
#         ])
#     ])

# def admin_layout():
#     user = current_user()
#     if not user or user.role != Role.GM:
#         return html.Div([navbar(), html.Div(className="card", children="Admins only.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Admin — Offices & Managers"),
#             html.H4("Create Office"),
#             dcc.Input(id="new-office-name", placeholder="Office name *", className="input"),
#             html.Button("Add Office", id="btn-add-office", className="btn"),
#             html.Div(id="msg-add-office", className="muted", style={"marginTop":"6px"}),
#             html.Div(className="hr"),
#             html.H4("Create Office Manager"),
#             html.Div(className="two-col", children=[
#                 dcc.Dropdown(id="om-office", placeholder="Select office", className="dash-dropdown"),
#                 dcc.Input(id="om-username", placeholder="Username *", className="input"),
#                 dcc.Input(id="om-password", placeholder="Password *", className="input"),
#             ]),
#             html.Button("Create OM", id="btn-create-om", className="btn"),
#             dcc.ConfirmDialog(id="admin-dialog"),
#             html.Div(id="msg-create-om", className="muted", style={"marginTop":"6px"}),
#             html.Div(className="hr"),
#             html.H4("Reset OM Password"),
#             html.Div(className="two-col", children=[
#                 dcc.Dropdown(id="om-existing", placeholder="Select OM user", className="dash-dropdown"),
#                 dcc.Input(id="om-new-pass", placeholder="New password *", className="input"),
#             ]),
#             html.Button("Reset Password", id="btn-om-reset", className="btn btn-outline"),
#             html.Div(id="msg-om-reset", className="muted", style={"marginTop":"6px"}),
#         ])
#     ])

# def profile_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("My Profile"),
#             html.Div(id="profile-form"),
#             dcc.ConfirmDialog(id="profile-dialog"),
#             html.Div(id="profile-msg", style={"color":"crimson", "marginTop":"6px"}),
#         ])
#     ])

# app.layout = html.Div([dcc.Location(id="url"), dcc.Store(id="dummy-refresh"), html.Div(id="page-content")])

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
#     if path == "/admin":
#         return admin_layout()
#     if path == "/profile":
#         return profile_layout()
#     return html.Div([navbar(), html.Div(className="card", children=html.H3("Not Found"))])

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

# # ---------- Dashboard KPIs ----------
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
#             count = s.query(Asset).count()
#             pending = s.query(Asset).filter(Asset.returned == False).count()  # noqa: E712
#         else:
#             emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#             assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#             ).all()
#             total_assets_cost = sum(a.price * a.quantity for a in assets)
#             count = len(assets)
#             pending = sum(1 for a in assets if not a.returned)
#         return html.Div(className="stack", children=[
#             html.Div(className="kpi", children=[html.Div("Assets", className="label"), html.Div(count, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Pending Returns", className="label"), html.Div(pending, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Total Cost", className="label"), html.Div(f"${total_assets_cost:,.2f}", className="value")]),
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
#     # GM allocation controls
#     State("asset-alloc-type", "value"),
#     State("asset-alloc-target", "value"),
#     Input("add-asset-btn", "n_clicks"),
#     State("asset-name", "value"), State("asset-price", "value"), State("asset-qty", "value"),
#     State("upload-bill", "contents"), State("upload-bill", "filename"),
#     prevent_initial_call=True
# )
# def add_asset(alloc_type, alloc_target, n, name, price, qty, contents, filename):
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
#             s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
#                         allocation_type=AllocationType.EMPLOYEE, allocation_id=emp.id))
#             s.commit()
#             return ("", render_assets_table(), "Asset added to your profile.", True, "", "", 1, None)
#         # GM allocation logic
#         alloc_type = (alloc_type or "UNALLOCATED") if user.role == Role.GM else "UNALLOCATED"
#         if alloc_type == "OFFICE":
#             if not alloc_target:
#                 return ("Select an office for allocation.", render_assets_table(), "", False, name, price, qty, contents)
#             s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
#                         allocation_type=AllocationType.OFFICE, allocation_id=int(alloc_target)))
#         elif alloc_type == "EMPLOYEE":
#             if not alloc_target:
#                 return ("Select an employee for allocation.", render_assets_table(), "", False, name, price, qty, contents)
#             s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
#                         allocation_type=AllocationType.EMPLOYEE, allocation_id=int(alloc_target)))
#         else:
#             s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path))
#         s.commit()
#     return ("", render_assets_table(), "Asset added.", True, "", "", 1, None)

# @app.callback(Output("asset-alloc-target", "children"), Input("asset-alloc-type", "value"))
# @login_required(Role.GM)
# def show_alloc_target(typ):
#     with SessionLocal() as s:
#         if typ == "OFFICE":
#             offices = s.query(Office).order_by(Office.name).all()
#             return dcc.Dropdown(id="asset-alloc-target", options=[{"label":o.name,"value":o.id} for o in offices],
#                                 placeholder="Select office", className="dash-dropdown")
#         if typ == "EMPLOYEE":
#             emps = s.query(Employee).order_by(Employee.name).all()
#             return dcc.Dropdown(id="asset-alloc-target", options=[{"label":e.name,"value":e.id} for e in emps],
#                                 placeholder="Select employee", className="dash-dropdown")
#         return html.Div(className="tiny", children="No specific target (Global/Unallocated).")

# def _bill_link(a):
#     if not a.bill_path:
#         return ""
#     base = _short_name(a.bill_path)
#     return f"[{base}](/uploads/{os.path.basename(a.bill_path)})"

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
#         common_inputs = html.Div(className="two-col", children=[
#             dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
#             dcc.Input(id="req-qty", type="number", value=1, className="input"),
#             dcc.Input(id="req-price", type="number", placeholder="Price (optional)", className="input"),
#             _uploader_component("req-bill"),
#         ])
#         if user.role == Role.EMP:
#             emp = _employee_for_user(user, s)
#             options = [{"label": emp.name, "value": emp.id}] if emp else []
#             return html.Div([
#                 html.B("Create Request"),
#                 dcc.Dropdown(id="req-employee", options=options, value=(emp.id if emp else None), className="dash-dropdown", disabled=True),
#                 common_inputs,
#                 html.Button("Submit Request", id="req-submit", className="btn"),
#                 html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#             ])
#         employees = s.query(Employee).filter(Employee.office_id == user.office_id).all() \
#             if user.role == Role.OM else s.query(Employee).all()
#         options = [{"label": e.name, "value": e.id} for e in employees]
#         return html.Div([
#             html.B("Create Request"),
#             dcc.Dropdown(id="req-employee", options=options, placeholder="Employee", className="dash-dropdown"),
#             common_inputs,
#             html.Button("Submit Request", id="req-submit", className="btn"),
#             html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#         ])

# @app.callback(
#     Output("req-msg", "children"),
#     Output("requests-table", "children", allow_duplicate=True),
#     Output("req-dialog","message"),
#     Output("req-dialog","displayed"),
#     Output("req-asset-name","value"),
#     Output("req-qty","value"),
#     Output("req-price","value"),
#     Output("req-bill","contents"),
#     Input("req-submit", "n_clicks"),
#     State("req-employee", "value"),
#     State("req-asset-name", "value"),
#     State("req-qty", "value"),
#     State("req-price", "value"),
#     State("req-bill", "contents"),
#     State("req-bill", "filename"),
#     prevent_initial_call=True
# )
# def create_request(n, emp_id, asset_name, qty, price, contents, filename):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     if not n or n < 1:
#         raise PreventUpdate
#     asset_name = (asset_name or "").strip()
#     try: qty = int(qty or 0)
#     except Exception: qty = 0
#     try: price_val = float(price or 0)
#     except Exception: price_val = 0
#     if not asset_name:
#         return "Please enter an asset name.", render_requests_table(), "", False, asset_name, qty, price, contents
#     if qty < 1:
#         return "Quantity must be at least 1.", render_requests_table(), "", False, asset_name, qty, price, contents
#     saved_path = None
#     if contents and filename:
#         _, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
#         saved_path = os.path.join(UPLOAD_FOLDER, fname)
#         with open(saved_path, "wb") as f:
#             f.write(decoded)
#     with SessionLocal() as s:
#         if user.role == Role.EMP and not emp_id:
#             emp = _employee_for_user(user, s)
#             emp_id = emp.id if emp else None
#         if not emp_id:
#             return "Select an employee.", render_requests_table(), "", False, asset_name, qty, price, contents
#         emp = s.get(Employee, emp_id)
#         if not emp:
#             return "Invalid employee.", render_requests_table(), "", False, asset_name, qty, price, contents
#         if user.role == Role.OM and emp.office_id != user.office_id:
#             return "You can only submit requests for your office.", render_requests_table(), "", False, asset_name, qty, price, contents
#         s.add(Request(employee_id=emp.id, office_id=emp.office_id, asset_name=asset_name, quantity=qty, price=price_val, bill_path=saved_path))
#         s.commit()
#     return "", render_requests_table(), "Request submitted.", True, "", 1, "", None

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
#         def bill_cell(r):
#             if not r.bill_path: return ""
#             return f"[{_short_name(r.bill_path)}](/uploads/{os.path.basename(r.bill_path)})"
#         data = [{"id":r.id,"employee_id":r.employee_id,"office_id":r.office_id,"asset":r.asset_name,
#                  "qty":r.quantity,"price":(r.price or 0),"status":r.status.value,"remark":r.remark or "",
#                  "bill": bill_cell(r),
#                  "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")} for r in rows]
#     cols = [{"name": n, "id": n} for n in ["id","employee_id","office_id","asset","qty","price","status","remark","bill","created_at"]]

#     user = current_user()
#     controls = html.Div(className="stack", children=[
#         dcc.Textarea(id="mgr-remark", placeholder="Remark…", className="input", style={"height":"60px", "width":"420px"}),
#         html.Button("Approve", id="btn-approve", className="btn"),
#         html.Button("Reject", id="btn-reject", className="btn btn-danger"),
#         html.Button("Mark Return Pending", id="btn-return-pending", className="btn btn-outline"),
#         html.Button("Mark Returned", id="btn-returned", className="btn btn-outline"),
#     ]) if user and user.role in (Role.GM, Role.OM) else html.Div()

#     table = dash_table.DataTable(data=data, columns=cols, id="req-table", row_selectable="single", page_size=10, style_table={"overflowX":"auto"})
#     return html.Div([table, html.Div(id="req-action-msg", style={"marginTop":"8px"}), controls])

# def _update_after_status_change(refresh_reports=True):
#     """Helper to return consistent outputs for status update callbacks."""
#     return (
#         render_requests_table(),  # requests table refreshed
#         "" if not refresh_reports else render_reports("/reports"),  # rebuild reports content
#         load_kpis("/"),  # dashboard KPIs
#         "",  # clear mgr remark
#         []   # clear selection
#     )

# @app.callback(
#     Output("req-action-msg", "children", allow_duplicate=True),
#     Output("requests-table", "children", allow_duplicate=True),
#     Output("reports-content", "children", allow_duplicate=True),
#     Output("dashboard-cards", "children", allow_duplicate=True),
#     Output("mgr-remark", "value", allow_duplicate=True),
#     Output("req-table", "selected_rows", allow_duplicate=True),
#     Input("btn-approve", "n_clicks"),
#     State("req-table", "selected_rows"), State("req-table", "data"),
#     State("mgr-remark", "value"), prevent_initial_call=True)
# def approve_req(n, selected, data, remark):
#     if not n: raise PreventUpdate
#     msg = handle_request_update(selected, data, remark, RequestStatus.APPROVED, create_asset_on_approve=True)
#     return (msg,) + _update_after_status_change(refresh_reports=True)

# @app.callback(
#     Output("req-action-msg", "children", allow_duplicate=True),
#     Output("requests-table", "children", allow_duplicate=True),
#     Output("reports-content", "children", allow_duplicate=True),
#     Output("dashboard-cards", "children", allow_duplicate=True),
#     Output("mgr-remark", "value", allow_duplicate=True),
#     Output("req-table", "selected_rows", allow_duplicate=True),
#     Input("btn-reject", "n_clicks"),
#     State("req-table", "selected_rows"), State("req-table", "data"),
#     State("mgr-remark", "value"), prevent_initial_call=True)
# def reject_req(n, selected, data, remark):
#     if not n: raise PreventUpdate
#     msg = handle_request_update(selected, data, remark, RequestStatus.REJECTED)
#     return (msg,) + _update_after_status_change(refresh_reports=False)

# @app.callback(
#     Output("req-action-msg", "children", allow_duplicate=True),
#     Output("requests-table", "children", allow_duplicate=True),
#     Output("reports-content", "children", allow_duplicate=True),
#     Output("dashboard-cards", "children", allow_duplicate=True),
#     Output("mgr-remark", "value", allow_duplicate=True),
#     Output("req-table", "selected_rows", allow_duplicate=True),
#     Input("btn-return-pending", "n_clicks"),
#     State("req-table", "selected_rows"), State("req-table", "data"),
#     State("mgr-remark", "value"), prevent_initial_call=True)
# def pending_req(n, selected, data, remark):
#     if not n: raise PreventUpdate
#     msg = handle_request_update(selected, data, remark, RequestStatus.RETURN_PENDING)
#     return (msg,) + _update_after_status_change(refresh_reports=False)

# @app.callback(
#     Output("req-action-msg", "children", allow_duplicate=True),
#     Output("requests-table", "children", allow_duplicate=True),
#     Output("reports-content", "children", allow_duplicate=True),
#     Output("dashboard-cards", "children", allow_duplicate=True),
#     Output("mgr-remark", "value", allow_duplicate=True),
#     Output("req-table", "selected_rows", allow_duplicate=True),
#     Input("btn-returned", "n_clicks"),
#     State("req-table", "selected_rows"), State("req-table", "data"),
#     State("mgr-remark", "value"), prevent_initial_call=True)
# def returned_req(n, selected, data, remark):
#     if not n: raise PreventUpdate
#     msg = handle_request_update(selected, data, remark, RequestStatus.RETURNED)
#     return (msg,) + _update_after_status_change(refresh_reports=True)

# def handle_request_update(selected, data, remark, status, create_asset_on_approve=False):
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
#         # Create an asset on approval
#         if create_asset_on_approve and status == RequestStatus.APPROVED:
#             s.add(Asset(
#                 name=r.asset_name,
#                 price=(r.price or 0),
#                 quantity=r.quantity,
#                 bill_path=r.bill_path,
#                 allocation_type=AllocationType.EMPLOYEE,
#                 allocation_id=r.employee_id
#             ))
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
#     return dash_table.DataTable(data=data, columns=cols, page_size=10, style_table={"overflowX":"auto"})

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

# # ---------- GM Admin ----------
# @app.callback(Output("om-office","options"), Output("om-existing","options"), Input("url","pathname"))
# @login_required(Role.GM)
# def load_admin_dropdowns(_):
#     with SessionLocal() as s:
#         offices = s.query(Office).order_by(Office.name).all()
#         oms = s.query(User).filter(User.role == Role.OM).order_by(User.username).all()
#         return (
#             [{"label": o.name, "value": o.id} for o in offices],
#             [{"label": u.username, "value": u.id} for u in oms]
#         )

# # refresh dropdowns instantly after adding office
# @app.callback(Output("msg-add-office","children"),
#               Output("om-office","options", allow_duplicate=True),
#               Input("btn-add-office","n_clicks"),
#               State("new-office-name","value"),
#               prevent_initial_call=True)
# @login_required(Role.GM)
# def add_office(n, office_name):
#     name = (office_name or "").strip()
#     if not name:
#         return "Office name is required.", no_update
#     with SessionLocal() as s:
#         if s.query(Office).filter(Office.name.ilike(name)).first():
#             return "Office already exists.", no_update
#         s.add(Office(name=name))
#         s.commit()
#         offices = s.query(Office).order_by(Office.name).all()
#     return "Office created.", [{"label": o.name, "value": o.id} for o in offices]

# @app.callback(
#     Output("msg-create-om","children"),
#     Output("admin-dialog","message"),
#     Output("admin-dialog","displayed"),
#     Output("om-username","value"),
#     Output("om-password","value"),
#     Output("om-existing","options", allow_duplicate=True),
#     State("om-office","value"),
#     State("om-username","value"),
#     State("om-password","value"),
#     Input("btn-create-om","n_clicks"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def create_om(office_id, uname, pwd, n):
#     uname = (uname or "").strip()
#     pwd = (pwd or "")
#     if not office_id or not uname or not pwd:
#         return ("All fields are required.", "", False, uname, pwd, no_update)
#     with SessionLocal() as s:
#         if not s.get(Office, office_id):
#             return ("Invalid office.", "", False, uname, pwd, no_update)
#         if s.query(User).filter(User.username == uname).first():
#             return ("Username already exists.", "", False, uname, pwd, no_update)
#         s.add(User(username=uname, password_hash=generate_password_hash(pwd), role=Role.OM, office_id=office_id))
#         s.commit()
#         oms = s.query(User).filter(User.role == Role.OM).order_by(User.username).all()
#     return ("OM created.", "Office Manager created successfully.", True, "", "", [{"label": u.username, "value": u.id} for u in oms])

# @app.callback(
#     Output("msg-om-reset","children"),
#     State("om-existing","value"),
#     State("om-new-pass","value"),
#     Input("btn-om-reset","n_clicks"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def reset_om_password(om_id, new_pass, n):
#     new_pass = (new_pass or "").strip()
#     if not om_id or not new_pass:
#         return "Select an OM and enter a new password."
#     with SessionLocal() as s:
#         u = s.get(User, om_id)
#         if not u or u.role != Role.OM:
#             return "Invalid OM selected."
#         u.password_hash = generate_password_hash(new_pass)
#         s.commit()
#     return "Password reset."

# # ---------- Reports (GM + OM) ----------
# @app.callback(Output("reports-content","children"), Input("url","pathname"))
# def render_reports(_):
#     user = current_user()
#     if not user or user.role == Role.EMP:
#         raise PreventUpdate

#     with SessionLocal() as s:
#         if user.role == Role.GM:
#             all_assets = s.query(Asset).all()
#             company_count = len(all_assets)
#             company_cost = sum(a.price * a.quantity for a in all_assets)
#             company_pending = sum(1 for a in all_assets if not a.returned)

#             offices = s.query(Office).order_by(Office.name).all()
#             office_options = [{"label": o.name, "value": o.id} for o in offices]
#             emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).order_by(Employee.name)]

#             return html.Div([
#                 html.Div(className="stack", children=[
#                     html.Div(className="kpi", children=[html.Div("Company assets", className="label"), html.Div(company_count, className="value")]),
#                     html.Div(className="kpi", children=[html.Div("Company total cost", className="label"), html.Div(f"${company_cost:,.2f}", className="value")]),
#                     html.Div(className="kpi", children=[html.Div("Company pending returns", className="label"), html.Div(company_pending, className="value")]),
#                 ]),
#                 html.Div(className="hr"),
#                 html.B("Per-Office Analytics"),
#                 dcc.Dropdown(id="rep-office", options=office_options, placeholder="Select office", className="dash-dropdown"),
#                 html.Div(id="rep-office-kpis", style={"marginTop":"8px"}),
#                 html.Div(className="hr"),
#                 html.B("Per-Employee Analytics"),
#                 dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#                 html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
#                 html.Div(className="hr"),
#                 html.B("Add Remark for Employee"),
#                 dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#                 dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input", style={"height":"80px"}),
#                 html.Button("Add Remark", id="rep-add-remark", className="btn"),
#                 html.Div(id="rep-remark-msg", className="muted", style={"marginTop":"6px"})
#             ])

#         # OM scope
#         emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#         office_assets = s.query(Asset).filter(
#             ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#             ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#         ).all()
#         office_count = len(office_assets)
#         office_cost = sum(a.price * a.quantity for a in office_assets)
#         emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).filter(Employee.office_id == user.office_id)]

#         return html.Div([
#             html.Div(className="kpi", children=[html.Div("Assets in my office", className="label"), html.Div(office_count, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Total cost for my office", className="label"), html.Div(f"${office_cost:,.2f}", className="value")]),
#             html.Div(className="hr"),
#             html.B("Per-Employee Analytics"),
#             dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#             html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
#             html.Div(className="hr"),
#             html.B("Add Remark for Employee"),
#             dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#             dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input", style={"height":"80px"}),
#             html.Button("Add Remark", id="rep-add-remark", className="btn"),
#             html.Div(id="rep-remark-msg", className="muted", style={"marginTop":"6px"})
#         ])

# @app.callback(Output("rep-office-kpis","children"), Input("rep-office","value"), prevent_initial_call=True)
# @login_required(Role.GM)
# def per_office_kpis(office_id):
#     if not office_id:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == office_id)]
#         assets = s.query(Asset).filter(
#             ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == office_id)) |
#             ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#         ).all()
#         count = len(assets)
#         pending = sum(1 for a in assets if not a.returned)
#         cost = sum(a.price * a.quantity for a in assets)
#     return html.Ul([
#         html.Li(f"Assets in office: {count}"),
#         html.Li(f"Pending returns: {pending}"),
#         html.Li(f"Total cost: ${cost:,.2f}")
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
#               Output("rep-remark-text","value", allow_duplicate=True),
#               Input("rep-add-remark","n_clicks"),
#               State("rep-emp-remark","value"),
#               State("rep-remark-text","value"),
#               prevent_initial_call=True)
# def add_remark(n, emp_id, textv):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     if not emp_id or not (textv or "").strip():
#         return "Select an employee and enter a remark.", no_update
#     with SessionLocal() as s:
#         s.add(Remark(author_user_id=user.id, target_type="EMPLOYEE", target_id=int(emp_id), content=(textv or "").strip()))
#         s.commit()
#     return "Remark added.", ""

# # ---------- Profile ----------
# @app.callback(Output("profile-form", "children"), Input("url", "pathname"))
# def load_profile(_):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         emp = _employee_for_user(user, s) if user.role == Role.EMP else None
#         office = s.get(Office, user.office_id) if user.office_id else None
#         remarks_block = html.Div()
#         if emp:
#             rms = s.query(Remark).filter(Remark.target_type == "EMPLOYEE", Remark.target_id == emp.id).order_by(Remark.created_at.desc()).all()
#             remarks_block = html.Div([
#                 html.Div(className="hr"),
#                 html.H4("Manager Remarks"),
#                 html.Ul([html.Li(f"{r.created_at.strftime('%Y-%m-%d %H:%M')}: {r.content}") for r in rms]) if rms else html.Div("No remarks yet.", className="muted")
#             ])
#         return html.Div([
#             html.Div([
#                 html.Div(f"User: {user.username}"),
#                 html.Div(f"Role: {role_name(user.role.value)}"),
#                 html.Div(f"Employee ID: {emp.id if emp else '—'}"),
#                 html.Div(f"Office ID: {office.id if office else '—'}"),
#                 html.Div(f"Office Name: {office.name if office else '—'}"),
#             ], style={"marginBottom":"8px"}),
#             dcc.Input(id="profile-emp-name", placeholder="Employee name", value=(emp.name if emp else ""), className="input"),
#             dcc.Input(id="profile-phone", placeholder="Phone number", value=getattr(emp, "phone", "") if emp else "", className="input"),
#             html.Button("Save Profile", id="btn-save-profile", n_clicks=0, type="button", className="btn"),
#             remarks_block
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


# =============================================================== above code is good ====================================================================================================
# # app.py
# from sqlalchemy import text
# import os, datetime, base64
# from functools import wraps
# from urllib.parse import quote

# import dash
# from dash import Dash, html, dcc, Input, Output, State, dash_table, ctx
# from dash.exceptions import PreventUpdate
# from werkzeug.security import check_password_hash, generate_password_hash
# from flask import session, send_from_directory

# from db import (
#     init_db, SessionLocal, Role, AllocationType, RequestStatus,
#     Office, User, Employee, Asset, Request, Remark, engine
# )

# # ---------- tiny migrations (idempotent) ----------
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
# # ensure request extras exist even if db.py migration didn't run yet
# _safe_add_column("requests", "price FLOAT")
# _safe_add_column("requests", "bill_path VARCHAR")
# _safe_add_column("requests", "fulfilled_asset_id INTEGER")

# UPLOAD_FOLDER = os.environ.get("RMS_UPLOAD_DIR", "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Initialize DB
# if not os.path.exists("rms.db"):
#     init_db(seed=True)
# else:
#     init_db(seed=False)

# # ---------- Dash ----------
# app = Dash(__name__, suppress_callback_exceptions=True, serve_locally=False)
# server = app.server
# server.secret_key = os.environ.get("RMS_SECRET", "dev-secret-key")

# # Pretty HTML shell + theme
# app.index_string = """
# <!DOCTYPE html>
# <html>
# <head>
#   <meta charset="UTF-8">
#   <title>RMS</title>
#   <link rel="preconnect" href="https://fonts.googleapis.com">
#   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
#   <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
#   {%metas%}{%favicon%}{%css%}
#   <style>
#     :root{
#       --bg:#f7f8fb; --card:#ffffff; --text:#131824; --muted:#6b7280;
#       --primary:#6366f1; --primary-600:#5458ee; --danger:#ef4444; --border:#e5e7eb;
#       --radius:12px; --shadow:0 6px 18px rgba(17,24,39,.06);
#     }
#     html,body{height:100%;}
#     body{background:var(--bg); font-family:'Inter',system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial; color:var(--text); line-height:1.35; padding:24px;}
#     nav a{ color:var(--primary); text-decoration:none; font-weight:600; }
#     nav a:hover{ text-decoration:underline; }
#     nav{ background:var(--card); padding:10px 14px; border:1px solid var(--border);
#          border-radius:var(--radius); box-shadow:var(--shadow); margin-bottom:16px;}
#     h2,h3,h4{ margin:8px 0 12px 0; }
#     .card{ background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
#            box-shadow:var(--shadow); padding:16px; margin:10px 0;}
#     .btn{ background:var(--primary); color:white; border:none; padding:8px 14px;
#           border-radius:10px; font-weight:600; cursor:pointer; transition:.15s transform ease, .15s background ease;
#           margin-right:8px; margin-top:6px;}
#     .btn:hover{ background:var(--primary-600); transform:translateY(-1px); }
#     .btn-outline{ background:transparent; color:var(--primary); border:1px solid var(--primary); }
#     .btn-danger{ background:var(--danger); }
#     .input, .dash-dropdown, textarea{ padding:8px 10px; border:1px solid var(--border); border-radius:10px;
#        background:white; outline:none; width:100%; max-width:560px; margin-right:8px; margin-bottom:8px;}
#     .two-col{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }
#     .kpi{ display:inline-block; min-width:210px; padding:14px 16px; margin-right:10px;
#           background:linear-gradient(180deg, #fff, #fbfbff); border:1px solid var(--border);
#           border-radius:14px; box-shadow:var(--shadow); }
#     .kpi .label{ color:#6b7280; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.06em;}
#     .kpi .value{ font-size:22px; font-weight:700; margin-top:4px;}
#     .hr{ height:1px; background:var(--border); margin:16px 0;}
#     .muted{ color:#6b7280; }
#     .stack{ display:flex; flex-wrap:wrap; gap:8px; align-items:center;}
#   </style>
# </head>
# <body>
#   {%app_entry%}
#   <footer>{%config%}{%scripts%}{%renderer%}</footer>
# </body>
# </html>
# """

# # ---------- Helpers ----------
# def current_user():
#     uid = session.get("user_id")
#     if not uid:
#         return None
#     with SessionLocal() as s:
#         u = s.get(User, uid)
#         if not u:
#             return None
#         if u.office_id:
#             _ = s.get(Office, u.office_id)
#         return u

# def _employee_for_user(user, s):
#     if not user or not user.office_id:
#         return None
#     emp = s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.username == user.username
#     ).first()
#     if emp:
#         return emp
#     return s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.name.ilike((user.username or "").strip())
#     ).first()

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
#     items = []
#     if user.role == Role.EMP:
#         items = [
#             dcc.Link("Dashboard", href="/"), html.Span(" | "),
#             dcc.Link("My Assets", href="/assets"), html.Span(" | "),
#             dcc.Link("Requests", href="/requests"), html.Span(" | "),
#             dcc.Link("My Profile", href="/profile"), html.Span(" | "),
#         ]
#     else:
#         items = [
#             dcc.Link("Dashboard", href="/"), html.Span(" | "),
#             dcc.Link("Assets", href="/assets"), html.Span(" | "),
#             dcc.Link("Requests", href="/requests"), html.Span(" | "),
#             dcc.Link("Reports", href="/reports"), html.Span(" | "),
#         ]
#         if user.role == Role.GM:
#             items.extend([dcc.Link("Admin", href="/admin"), html.Span(" | ")])
#         else:
#             items.extend([dcc.Link("Employees", href="/employees"), html.Span(" | ")])
#     items.append(dcc.Link("Logout", href="/logout"))
#     return html.Nav(items)

# def login_layout():
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H2("Resource Management System — Login"),
#             dcc.Input(id="login-username", placeholder="Username", className="input"),
#             dcc.Input(id="login-password", type="password", placeholder="Password", className="input"),
#             html.Button("Login", id="login-btn", className="btn"),
#             html.Div(id="login-msg", style={"color": "crimson", "marginTop": "8px"}),
#             html.Div(className="muted", children="Default demo users: admin/admin, om_east/om_east, alice/alice")
#         ])
#     ])

# def dashboard_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     scope = "Company-wide" if user.role == Role.GM else "Your office"
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(f"Dashboard — {role_name(user.role.value)}"),
#             html.Div(className="muted", children=scope),
#             html.Div(id="dashboard-cards", className="pad-top")
#         ])
#     ])

# def _uploader_component(id_):
#     return dcc.Upload(
#         id=id_,
#         children=html.Button("Upload Bill / Drag & Drop", className="btn btn-outline"),
#         multiple=False
#     )

# def assets_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     header = "My Assets" if user.role == Role.EMP else "Assets"
#     button_label = "Add to My Profile" if user.role == Role.EMP else "Add Asset"
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(header),
#             _uploader_component("upload-bill"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="asset-name", placeholder="Asset name *", className="input"),
#                 dcc.Input(id="asset-price", placeholder="Price *", type="number", className="input"),
#                 dcc.Input(id="asset-qty", placeholder="Quantity *", type="number", value=1, className="input"),
#             ]),
#             dcc.RadioItems(
#                 id="alloc-type",
#                 options=[
#                     {"label":"Global / Unallocated", "value": AllocationType.UNALLOCATED.value},
#                     {"label":"Allocate to Office", "value": AllocationType.OFFICE.value},
#                     {"label":"Allocate to Employee", "value": AllocationType.EMPLOYEE.value},
#                 ],
#                 value=AllocationType.UNALLOCATED.value,
#                 labelStyle={"display":"block", "margin":"6px 0"}
#             ),
#             dcc.Dropdown(id="alloc-target", placeholder="Choose office/employee (if applicable)", className="dash-dropdown"),
#             html.Button(button_label, id="add-asset-btn", className="btn"),
#             html.Div(id="asset-add-msg", style={"color":"crimson", "marginTop":"6px"}),
#             dcc.ConfirmDialog(id="asset-dialog"),
#         ]),
#         html.Div(className="card", children=[
#             html.H4(f"{header} Table"),
#             html.Div(id="assets-table")
#         ])
#     ])

# def requests_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Requests"),
#             html.Div(id="request-form"),
#             dcc.ConfirmDialog(id="req-dialog")
#         ]),
#         html.Div(className="card", children=[
#             html.H4("Open Requests"),
#             html.Div(id="requests-table")
#         ])
#     ])

# def reports_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role == Role.EMP:
#         return html.Div([navbar(), html.Div(className="card", children="Reports are not available for Employees.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Reports"),
#             html.Div(id="reports-content"),
#             dcc.ConfirmDialog(id="reports-dialog"),
#             html.Div(id="reports-msg", style={"color":"crimson", "marginTop":"6px"}),
#         ])
#     ])

# def employees_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role != Role.OM:
#         return html.Div([navbar(), html.Div(className="card", children="Only Office Managers can manage employees.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Manage Employees"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="emp-new-name", placeholder="Employee name *", className="input"),
#                 dcc.Input(id="emp-new-phone", placeholder="Phone", className="input"),
#                 dcc.Input(id="emp-new-username", placeholder="Username *", className="input"),
#                 dcc.Input(id="emp-new-password", placeholder="Password *", className="input"),
#             ]),
#             html.Button("Add Employee", id="emp-add-btn", className="btn"),
#             dcc.ConfirmDialog(id="emp-dialog"),
#             html.Div(id="emp-add-msg", style={"color":"crimson", "marginTop":"6px"})
#         ]),
#         html.Div(className="card", children=[
#             html.H4("Employees in My Office"),
#             html.Div(id="emp-table")
#         ])
#     ])

# def admin_layout():
#     user = current_user()
#     if not user or user.role != Role.GM:
#         return html.Div([navbar(), html.Div(className="card", children="Admins only.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Admin — Offices & Managers"),
#             html.H4("Create Office"),
#             dcc.Input(id="new-office-name", placeholder="Office name *", className="input"),
#             html.Button("Add Office", id="btn-add-office", className="btn"),
#             html.Div(id="msg-add-office", className="muted", style={"marginTop":"6px"}),
#             html.Div(className="hr"),
#             html.H4("Create Office Manager"),
#             html.Div(className="two-col", children=[
#                 dcc.Dropdown(id="om-office", placeholder="Select office", className="dash-dropdown"),
#                 dcc.Input(id="om-username", placeholder="Username *", className="input"),
#                 dcc.Input(id="om-password", placeholder="Password *", className="input"),
#             ]),
#             html.Button("Create OM", id="btn-create-om", className="btn"),
#             dcc.ConfirmDialog(id="admin-dialog"),
#             html.Div(id="msg-create-om", className="muted", style={"marginTop":"6px"}),
#             html.Div(className="hr"),
#             html.H4("Reset OM Password"),
#             html.Div(className="two-col", children=[
#                 dcc.Dropdown(id="om-existing", placeholder="Select OM user", className="dash-dropdown"),
#                 dcc.Input(id="om-new-pass", placeholder="New password *", className="input"),
#             ]),
#             html.Button("Reset Password", id="btn-om-reset", className="btn btn-outline"),
#             html.Div(id="msg-om-reset", className="muted", style={"marginTop":"6px"}),
#         ])
#     ])

# def profile_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("My Profile"),
#             html.Div(id="profile-form"),
#             dcc.ConfirmDialog(id="profile-dialog"),
#             html.Div(id="profile-msg", style={"color":"crimson", "marginTop":"6px"}),
#         ])
#     ])

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
#     if path == "/admin":
#         return admin_layout()
#     if path == "/profile":
#         return profile_layout()
#     return html.Div([navbar(), html.Div(className="card", children=html.H3("Not Found"))])

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

# # ---------- Dashboard KPIs ----------
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
#             count = s.query(Asset).count()
#             pending = s.query(Asset).filter(Asset.returned == False).count()  # noqa: E712
#         else:
#             emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#             assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#             ).all()
#             total_assets_cost = sum(a.price * a.quantity for a in assets)
#             count = len(assets)
#             pending = sum(1 for a in assets if not a.returned)
#         return html.Div(className="stack", children=[
#             html.Div(className="kpi", children=[html.Div("Assets", className="label"), html.Div(count, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Pending Returns", className="label"), html.Div(pending, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Total Cost", className="label"), html.Div(f"${total_assets_cost:,.2f}", className="value")]),
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
#     State("alloc-type", "value"), State("alloc-target", "value"),
#     prevent_initial_call=True
# )
# def add_asset(n, name, price, qty, contents, filename, alloc_type, alloc_target):
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
#         _, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
#         saved_path = os.path.join(UPLOAD_FOLDER, fname)
#         with open(saved_path, "wb") as f:
#             f.write(decoded)

#     with SessionLocal() as s:
#         a_type = AllocationType.UNALLOCATED
#         a_id = None
#         if alloc_type == AllocationType.OFFICE.value:
#             a_type = AllocationType.OFFICE
#             a_id = int(alloc_target) if alloc_target else (current_user().office_id or None)
#         elif alloc_type == AllocationType.EMPLOYEE.value:
#             a_type = AllocationType.EMPLOYEE
#             if alloc_target:
#                 a_id = int(alloc_target)
#             elif current_user().role == Role.EMP:
#                 emp = _employee_for_user(current_user(), s)
#                 a_id = emp.id if emp else None

#         s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
#                     allocation_type=a_type, allocation_id=a_id))
#         s.commit()
#     return ("", render_assets_table(), "Asset added.", True, "", "", 1, None)

# def _bill_link_path(path):
#     if not path:
#         return ""
#     base = os.path.basename(path)
#     return f"[{base}](/uploads/{quote(base)})"

# def _bill_link_asset(a):
#     return _bill_link_path(a.bill_path)

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
#             rows = [{"asset_no": i, "name": a.name, "price": a.price, "qty": a.quantity, "bill": _bill_link_asset(a)}
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
#         rows = [{"id":a.id,"name":a.name,"price":a.price,"qty":a.quantity,"bill":_bill_link_asset(a),
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

# # Dynamic options for allocation target
# @app.callback(
#     Output("alloc-target", "options"),
#     Output("alloc-target", "value"),
#     Output("alloc-target", "placeholder"),
#     Input("alloc-type", "value"),
#     Input("url", "pathname"),
# )
# def update_alloc_options(alloc_type, _):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         if alloc_type == AllocationType.OFFICE.value:
#             if user.role == Role.GM:
#                 offices = s.query(Office).order_by(Office.name).all()
#                 opts = [{"label": o.name, "value": o.id} for o in offices]
#                 return opts, None, "Select office"
#             else:
#                 return [{"label": "My Office", "value": user.office_id}], user.office_id, "My Office"
#         elif alloc_type == AllocationType.EMPLOYEE.value:
#             q = s.query(Employee)
#             if user.role == Role.OM:
#                 q = q.filter(Employee.office_id == user.office_id)
#             elif user.role == Role.EMP:
#                 emp = _employee_for_user(user, s)
#                 if emp:
#                     return [{"label": emp.name, "value": emp.id}], emp.id, "Myself"
#             emps = q.order_by(Employee.name).all()
#             return [{"label": e.name, "value": e.id} for e in emps], None, "Select employee"
#         return [], None, "No target (Global/Unallocated)"

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
#                 html.B("Create Request"),
#                 dcc.Dropdown(id="req-employee", options=options, value=(emp.id if emp else None), className="dash-dropdown", disabled=True),
#                 html.Div(className="two-col", children=[
#                     dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
#                     dcc.Input(id="req-qty", type="number", value=1, className="input"),
#                     dcc.Input(id="req-price", placeholder="Price", type="number", className="input"),
#                 ]),
#                 _uploader_component("req-bill"),
#                 html.Button("Submit Request", id="req-submit", className="btn"),
#                 html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#             ])
#         employees = s.query(Employee).filter(Employee.office_id == user.office_id).all() \
#             if user.role == Role.OM else s.query(Employee).all()
#         options = [{"label": e.name, "value": e.id} for e in employees]
#         return html.Div([
#             html.B("Create Request"),
#             dcc.Dropdown(id="req-employee", options=options, placeholder="Employee", className="dash-dropdown"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
#                 dcc.Input(id="req-qty", type="number", value=1, className="input"),
#                 dcc.Input(id="req-price", placeholder="Price", type="number", className="input"),
#             ]),
#             _uploader_component("req-bill"),
#             html.Button("Submit Request", id="req-submit", className="btn"),
#             html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#         ])

# @app.callback(
#     Output("req-msg", "children"),
#     Output("requests-table", "children", allow_duplicate=True),
#     Output("req-dialog","message"),
#     Output("req-dialog","displayed"),
#     Output("req-asset-name","value"),
#     Output("req-qty","value"),
#     Output("req-price","value"),
#     Output("req-bill","contents"),
#     Input("req-submit", "n_clicks"),
#     State("req-employee", "value"),
#     State("req-asset-name", "value"),
#     State("req-qty", "value"),
#     State("req-price", "value"),
#     State("req-bill", "contents"),
#     State("req-bill", "filename"),
#     prevent_initial_call=True
# )
# def create_request(n, emp_id, asset_name, qty, price, contents, filename):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     if not n or n < 1:
#         raise PreventUpdate
#     asset_name = (asset_name or "").strip()
#     try: qty = int(qty or 0)
#     except Exception: qty = 0
#     try: price_val = float(price or 0)
#     except Exception: price_val = 0.0
#     if not asset_name:
#         return "Please enter an asset name.", render_requests_table(), "", False, asset_name, qty, price, contents
#     if qty < 1:
#         return "Quantity must be at least 1.", render_requests_table(), "", False, asset_name, qty, price, contents

#     saved_path = None
#     if contents and filename:
#         _, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
#         saved_path = os.path.join(UPLOAD_FOLDER, fname)
#         with open(saved_path, "wb") as f:
#             f.write(decoded)

#     with SessionLocal() as s:
#         if user.role == Role.EMP and not emp_id:
#             emp = _employee_for_user(user, s)
#             emp_id = emp.id if emp else None
#         if not emp_id:
#             return "Select an employee.", render_requests_table(), "", False, asset_name, qty, price, contents
#         emp = s.get(Employee, emp_id)
#         if not emp:
#             return "Invalid employee.", render_requests_table(), "", False, asset_name, qty, price, contents
#         if user.role == Role.OM and emp.office_id != user.office_id:
#             return "You can only submit requests for your office.", render_requests_table(), "", False, asset_name, qty, price, contents
#         s.add(Request(employee_id=emp.id, office_id=emp.office_id, asset_name=asset_name,
#                       quantity=qty, price=price_val, bill_path=saved_path))
#         s.commit()
#     return "", render_requests_table(), "Request submitted.", True, "", 1, "", None

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
#         data = [{
#             "id":r.id,"employee_id":r.employee_id,"office_id":r.office_id,"asset":r.asset_name,
#             "qty":r.quantity,"price": r.price, "status":r.status.value,"remark":r.remark or "",
#             "bill": _bill_link_path(r.bill_path),
#             "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
#         } for r in rows]
#     cols = [
#         {"name":"id","id":"id"},
#         {"name":"employee_id","id":"employee_id"},
#         {"name":"office_id","id":"office_id"},
#         {"name":"asset","id":"asset"},
#         {"name":"qty","id":"qty"},
#         {"name":"price","id":"price"},
#         {"name":"status","id":"status"},
#         {"name":"remark","id":"remark"},
#         {"name":"bill","id":"bill","presentation":"markdown"},
#         {"name":"created_at","id":"created_at"},
#     ]

#     user = current_user()
#     controls = html.Div(className="stack", children=[
#         dcc.Textarea(id="mgr-remark", placeholder="Remark…", className="input", style={"height":"60px", "width":"420px"}),
#         html.Button("Approve", id="btn-approve", className="btn"),
#         html.Button("Reject", id="btn-reject", className="btn btn-danger"),
#         html.Button("Mark Return Pending", id="btn-return-pending", className="btn btn-outline"),
#         html.Button("Mark Returned", id="btn-returned", className="btn btn-outline"),
#     ]) if user and user.role in (Role.GM, Role.OM) else html.Div()

#     table = dash_table.DataTable(data=data, columns=cols, id="req-table",
#                                  row_selectable="single", page_size=10, style_table={"overflowX":"auto"})
#     return html.Div([table, html.Div(id="req-action-msg", style={"marginTop":"8px"}), controls])

# # ---------- Action buttons (2-phase approval-safe) ----------
# @app.callback(
#     Output("req-action-msg", "children", allow_duplicate=True),
#     Output("requests-table", "children", allow_duplicate=True),
#     Input("btn-approve", "n_clicks"),
#     Input("btn-reject", "n_clicks"),
#     Input("btn-return-pending", "n_clicks"),
#     Input("btn-returned", "n_clicks"),
#     State("req-table", "selected_rows"), State("req-table", "data"),
#     State("mgr-remark", "value"),
#     prevent_initial_call=True
# )
# def handle_request_action(n1, n2, n3, n4, selected, data, remark):
#     user = current_user()
#     if not user or user.role not in (Role.GM, Role.OM):
#         return "Not allowed.", render_requests_table()
#     if not selected:
#         return "Select a request first.", render_requests_table()

#     mapping = {
#         "btn-approve": RequestStatus.APPROVED,
#         "btn-reject": RequestStatus.REJECTED,
#         "btn-return-pending": RequestStatus.RETURN_PENDING,
#         "btn-returned": RequestStatus.RETURNED,
#     }
#     trig = ctx.triggered_id
#     status = mapping.get(trig, None)
#     if status is None:
#         raise PreventUpdate

#     req_id = data[selected[0]]["id"]

#     # Phase 1: update status/remark
#     need_asset_payload = None
#     try:
#         with SessionLocal() as s:
#             r = s.get(Request, req_id)
#             if not r:
#                 return "Request not found.", render_requests_table()
#             if user.role == Role.OM and r.office_id != user.office_id:
#                 return "You can only update requests in your office.", render_requests_table()

#             create_asset = (status == RequestStatus.APPROVED and not getattr(r, "fulfilled_asset_id", None))
#             if remark:
#                 r.remark = remark
#             r.status = status

#             if create_asset:
#                 need_asset_payload = dict(
#                     name=r.asset_name,
#                     price=float(r.price or 0),
#                     quantity=int(r.quantity or 1),
#                     bill_path=r.bill_path,
#                     allocation_type=AllocationType.EMPLOYEE,
#                     allocation_id=int(r.employee_id or 0),
#                     req_row_id=r.id
#                 )
#             s.commit()
#     except Exception as e:
#         return f"Failed to update: {e}", render_requests_table()

#     # Phase 2: create asset if needed (separate transaction)
#     if need_asset_payload:
#         if not need_asset_payload["allocation_id"]:
#             return "Approved (no employee to allocate, asset not created).", render_requests_table()
#         try:
#             with SessionLocal() as s:
#                 r2 = s.get(Request, req_id)
#                 if r2 and not getattr(r2, "fulfilled_asset_id", None):
#                     a = Asset(
#                         name=need_asset_payload["name"],
#                         price=need_asset_payload["price"],
#                         quantity=need_asset_payload["quantity"],
#                         bill_path=need_asset_payload["bill_path"],
#                         allocation_type=need_asset_payload["allocation_type"],
#                         allocation_id=need_asset_payload["allocation_id"],
#                     )
#                     s.add(a); s.flush()
#                     r2.fulfilled_asset_id = a.id
#                     s.commit()
#         except Exception as e:
#             return f"Approved (asset creation failed: {e})", render_requests_table()

#     return f"Status updated to {status.value}.", render_requests_table()

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
#     return dash_table.DataTable(data=data, columns=cols, page_size=10, style_table={"overflowX":"auto"})

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

# # ---------- GM Admin ----------
# @app.callback(Output("om-office","options"), Output("om-existing","options"), Input("url","pathname"))
# @login_required(Role.GM)
# def load_admin_dropdowns(_):
#     with SessionLocal() as s:
#         offices = s.query(Office).order_by(Office.name).all()
#         oms = s.query(User).filter(User.role == Role.OM).order_by(User.username).all()
#         return (
#             [{"label": o.name, "value": o.id} for o in offices],
#             [{"label": u.username, "value": u.id} for u in oms]
#         )

# @app.callback(
#     Output("msg-add-office","children"),
#     Output("om-office","options", allow_duplicate=True),
#     Input("btn-add-office","n_clicks"),
#     State("new-office-name","value"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def add_office(n, office_name):
#     name = (office_name or "").strip()
#     with SessionLocal() as s:
#         if not name:
#             offices = s.query(Office).order_by(Office.name).all()
#             return "Office name is required.", [{"label": o.name, "value": o.id} for o in offices]
#         if s.query(Office).filter(Office.name.ilike(name)).first():
#             offices = s.query(Office).order_by(Office.name).all()
#             return "Office already exists.", [{"label": o.name, "value": o.id} for o in offices]
#         s.add(Office(name=name))
#         s.commit()
#         offices = s.query(Office).order_by(Office.name).all()
#     return "Office created.", [{"label": o.name, "value": o.id} for o in offices]

# @app.callback(
#     Output("msg-create-om","children"),
#     Output("admin-dialog","message"),
#     Output("admin-dialog","displayed"),
#     Output("om-username","value"),
#     Output("om-password","value"),
#     State("om-office","value"),
#     State("om-username","value"),
#     State("om-password","value"),
#     Input("btn-create-om","n_clicks"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def create_om(office_id, uname, pwd, n):
#     uname = (uname or "").strip()
#     pwd = (pwd or "")
#     if not office_id or not uname or not pwd:
#         return ("All fields are required.", "", False, uname, pwd)
#     with SessionLocal() as s:
#         if not s.get(Office, office_id):
#             return ("Invalid office.", "", False, uname, pwd)
#         if s.query(User).filter(User.username == uname).first():
#             return ("Username already exists.", "", False, uname, pwd)
#         s.add(User(username=uname, password_hash=generate_password_hash(pwd), role=Role.OM, office_id=office_id))
#         s.commit()
#     return ("OM created.", "Office Manager created successfully.", True, "", "")

# @app.callback(
#     Output("msg-om-reset","children"),
#     State("om-existing","value"),
#     State("om-new-pass","value"),
#     Input("btn-om-reset","n_clicks"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def reset_om_password(om_id, new_pass, n):
#     new_pass = (new_pass or "").strip()
#     if not om_id or not new_pass:
#         return "Select an OM and enter a new password."
#     with SessionLocal() as s:
#         u = s.get(User, om_id)
#         if not u or u.role != Role.OM:
#             return "Invalid OM selected."
#         u.password_hash = generate_password_hash(new_pass)
#         s.commit()
#     return "Password reset."

# # ---------- Reports (GM + OM) ----------
# @app.callback(Output("reports-content","children"), Input("url","pathname"))
# def render_reports(_):
#     user = current_user()
#     if not user or user.role == Role.EMP:
#         raise PreventUpdate

#     with SessionLocal() as s:
#         if user.role == Role.GM:
#             all_assets = s.query(Asset).all()
#             company_count = len(all_assets)
#             company_cost = sum(a.price * a.quantity for a in all_assets)
#             company_pending = sum(1 for a in all_assets if not a.returned)

#             offices = s.query(Office).order_by(Office.name).all()
#             office_options = [{"label": o.name, "value": o.id} for o in offices]
#             emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).order_by(Employee.name)]

#             return html.Div([
#                 html.Div(className="stack", children=[
#                     html.Div(className="kpi", children=[html.Div("Company assets", className="label"), html.Div(company_count, className="value")]),
#                     html.Div(className="kpi", children=[html.Div("Company total cost", className="label"), html.Div(f"${company_cost:,.2f}", className="value")]),
#                     html.Div(className="kpi", children=[html.Div("Company pending returns", className="label"), html.Div(company_pending, className="value")]),
#                 ]),
#                 html.Div(className="hr"),
#                 html.B("Per-Office Analytics"),
#                 dcc.Dropdown(id="rep-office", options=office_options, placeholder="Select office", className="dash-dropdown"),
#                 html.Div(id="rep-office-kpis", style={"marginTop":"8px"}),
#                 html.Div(className="hr"),
#                 html.B("Per-Employee Analytics"),
#                 dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#                 html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
#                 html.Div(className="hr"),
#                 html.B("Add Remark for Employee"),
#                 dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#                 dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input", style={"height":"80px"}),
#                 html.Button("Add Remark", id="rep-add-remark", className="btn"),
#                 html.Div(id="rep-remark-msg", className="muted", style={"marginTop":"6px"})
#             ])

#         # OM scope
#         emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#         office_assets = s.query(Asset).filter(
#             ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#             ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#         ).all()
#         office_count = len(office_assets)
#         office_cost = sum(a.price * a.quantity for a in office_assets)
#         emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).filter(Employee.office_id == user.office_id)]

#         return html.Div([
#             html.Div(className="kpi", children=[html.Div("Assets in my office", className="label"), html.Div(office_count, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Total cost for my office", className="label"), html.Div(f"${office_cost:,.2f}", className="value")]),
#             html.Div(className="hr"),
#             html.B("Per-Employee Analytics"),
#             dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#             html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
#             html.Div(className="hr"),
#             html.B("Add Remark for Employee"),
#             dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#             dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input"),
#             html.Button("Add Remark", id="rep-add-remark", className="btn"),
#             html.Div(id="rep-remark-msg", className="muted", style={"marginTop":"6px"})
#         ])

# @app.callback(Output("rep-office-kpis","children"), Input("rep-office","value"), prevent_initial_call=True)
# @login_required(Role.GM)
# def per_office_kpis(office_id):
#     if not office_id:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == office_id)]
#         assets = s.query(Asset).filter(
#             ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == office_id)) |
#             ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#         ).all()
#         count = len(assets)
#         pending = sum(1 for a in assets if not a.returned)
#         cost = sum(a.price * a.quantity for a in assets)
#     return html.Ul([
#         html.Li(f"Assets in office: {count}"),
#         html.Li(f"Pending returns: {pending}"),
#         html.Li(f"Total cost: ${cost:,.2f}")
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
#         office = s.get(Office, user.office_id) if user.office_id else None
#         return html.Div([
#             html.Div([
#                 html.Div(f"User: {user.username}"),
#                 html.Div(f"Role: {role_name(user.role.value)}"),
#                 html.Div(f"Employee ID: {emp.id if emp else '—'}"),
#                 html.Div(f"Office ID: {office.id if office else '—'}"),
#                 html.Div(f"Office Name: {office.name if office else '—'}"),
#             ], style={"marginBottom":"8px"}),
#             dcc.Input(id="profile-emp-name", placeholder="Employee name", value=(emp.name if emp else ""), className="input"),
#             dcc.Input(id="profile-phone", placeholder="Phone number", value=getattr(emp, "phone", "") if emp else "", className="input"),
#             html.Button("Save Profile", id="btn-save-profile", n_clicks=0, type="button", className="btn"),
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

# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# # app.py
# from sqlalchemy import text
# import os, datetime, base64
# from functools import wraps
# from urllib.parse import quote

# import dash
# from dash import Dash, html, dcc, Input, Output, State, dash_table, ctx
# from dash.exceptions import PreventUpdate
# from werkzeug.security import check_password_hash, generate_password_hash
# from flask import session, send_from_directory

# from db import (
#     init_db, SessionLocal, Role, AllocationType, RequestStatus,
#     Office, User, Employee, Asset, Request, Remark, engine
# )

# # ---------- tiny migrations (idempotent) ----------
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
# # ensure request extras exist even if db.py migration didn't run yet
# _safe_add_column("requests", "price FLOAT")
# _safe_add_column("requests", "bill_path VARCHAR")
# _safe_add_column("requests", "fulfilled_asset_id INTEGER")

# UPLOAD_FOLDER = os.environ.get("RMS_UPLOAD_DIR", "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Initialize DB
# if not os.path.exists("rms.db"):
#     init_db(seed=True)
# else:
#     init_db(seed=False)

# # ---------- Dash ----------
# app = Dash(__name__, suppress_callback_exceptions=True, serve_locally=False)
# server = app.server
# server.secret_key = os.environ.get("RMS_SECRET", "dev-secret-key")

# # Pretty HTML shell + theme
# app.index_string = """
# <!DOCTYPE html>
# <html>
# <head>
#   <meta charset="UTF-8">
#   <title>RMS</title>
#   <link rel="preconnect" href="https://fonts.googleapis.com">
#   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
#   <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
#   {%metas%}{%favicon%}{%css%}
#   <style>
#     :root{
#       --bg:#f7f8fb; --card:#ffffff; --text:#131824; --muted:#6b7280;
#       --primary:#6366f1; --primary-600:#5458ee; --danger:#ef4444; --border:#e5e7eb;
#       --radius:12px; --shadow:0 6px 18px rgba(17,24,39,.06);
#     }
#     html,body{height:100%;}
#     body{background:var(--bg); font-family:'Inter',system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial; color:var(--text); line-height:1.35; padding:24px;}
#     nav a{ color:var(--primary); text-decoration:none; font-weight:600; }
#     nav a:hover{ text-decoration:underline; }
#     nav{ background:var(--card); padding:10px 14px; border:1px solid var(--border);
#          border-radius:var(--radius); box-shadow:var(--shadow); margin-bottom:16px;}
#     h2,h3,h4{ margin:8px 0 12px 0; }
#     .card{ background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
#            box-shadow:var(--shadow); padding:16px; margin:10px 0;}
#     .btn{ background:var(--primary); color:white; border:none; padding:8px 14px;
#           border-radius:10px; font-weight:600; cursor:pointer; transition:.15s transform ease, .15s background ease;
#           margin-right:8px; margin-top:6px;}
#     .btn:hover{ background:var(--primary-600); transform:translateY(-1px); }
#     .btn-outline{ background:transparent; color:var(--primary); border:1px solid var(--primary); }
#     .btn-danger{ background:var(--danger); }
#     .input, .dash-dropdown, textarea{ padding:8px 10px; border:1px solid var(--border); border-radius:10px;
#        background:white; outline:none; width:100%; max-width:560px; margin-right:8px; margin-bottom:8px;}
#     .two-col{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }
#     .kpi{ display:inline-block; min-width:210px; padding:14px 16px; margin-right:10px;
#           background:linear-gradient(180deg, #fff, #fbfbff); border:1px solid var(--border);
#           border-radius:14px; box-shadow:var(--shadow); }
#     .kpi .label{ color:#6b7280; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.06em;}
#     .kpi .value{ font-size:22px; font-weight:700; margin-top:4px;}
#     .hr{ height:1px; background:var(--border); margin:16px 0;}
#     .muted{ color:#6b7280; }
#     .stack{ display:flex; flex-wrap:wrap; gap:8px; align-items:center;}
#   </style>
# </head>
# <body>
#   {%app_entry%}
#   <footer>{%config%}{%scripts%}{%renderer%}</footer>
# </body>
# </html>
# """

# # ---------- Helpers ----------
# def current_user():
#     uid = session.get("user_id")
#     if not uid:
#         return None
#     with SessionLocal() as s:
#         u = s.get(User, uid)
#         if not u:
#             return None
#         if u.office_id:
#             _ = s.get(Office, u.office_id)
#         return u

# def _employee_for_user(user, s):
#     if not user or not user.office_id:
#         return None
#     emp = s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.username == user.username
#     ).first()
#     if emp:
#         return emp
#     return s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.name.ilike((user.username or "").strip())
#     ).first()

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
#     items = []
#     if user.role == Role.EMP:
#         items = [
#             dcc.Link("Dashboard", href="/"), html.Span(" | "),
#             dcc.Link("My Assets", href="/assets"), html.Span(" | "),
#             dcc.Link("Requests", href="/requests"), html.Span(" | "),
#             dcc.Link("My Profile", href="/profile"), html.Span(" | "),
#         ]
#     else:
#         items = [
#             dcc.Link("Dashboard", href="/"), html.Span(" | "),
#             dcc.Link("Assets", href="/assets"), html.Span(" | "),
#             dcc.Link("Requests", href="/requests"), html.Span(" | "),
#             dcc.Link("Reports", href="/reports"), html.Span(" | "),
#         ]
#         if user.role == Role.GM:
#             items.extend([dcc.Link("Admin", href="/admin"), html.Span(" | ")])
#         else:
#             items.extend([dcc.Link("Employees", href="/employees"), html.Span(" | ")])
#     items.append(dcc.Link("Logout", href="/logout"))
#     return html.Nav(items)

# def login_layout():
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H2("Resource Management System — Login"),
#             dcc.Input(id="login-username", placeholder="Username", className="input"),
#             dcc.Input(id="login-password", type="password", placeholder="Password", className="input"),
#             html.Button("Login", id="login-btn", className="btn"),
#             html.Div(id="login-msg", style={"color": "crimson", "marginTop": "8px"}),
#             html.Div(className="muted", children="Default demo users: admin/admin, om_east/om_east, alice/alice")
#         ])
#     ])

# def dashboard_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     scope = "Company-wide" if user.role == Role.GM else "Your office"
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(f"Dashboard — {role_name(user.role.value)}"),
#             html.Div(className="muted", children=scope),
#             html.Div(id="dashboard-cards", className="pad-top")
#         ])
#     ])

# def _uploader_component(id_):
#     return dcc.Upload(
#         id=id_,
#         children=html.Button("Upload Bill / Drag & Drop", className="btn btn-outline"),
#         multiple=False
#     )

# def assets_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     header = "My Assets" if user.role == Role.EMP else "Assets"
#     button_label = "Add to My Profile" if user.role == Role.EMP else "Add Asset"
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(header),
#             _uploader_component("upload-bill"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="asset-name", placeholder="Asset name *", className="input"),
#                 dcc.Input(id="asset-price", placeholder="Price *", type="number", className="input"),
#                 dcc.Input(id="asset-qty", placeholder="Quantity *", type="number", value=1, className="input"),
#             ]),
#             dcc.RadioItems(
#                 id="alloc-type",
#                 options=[
#                     {"label":"Global / Unallocated", "value": AllocationType.UNALLOCATED.value},
#                     {"label":"Allocate to Office", "value": AllocationType.OFFICE.value},
#                     {"label":"Allocate to Employee", "value": AllocationType.EMPLOYEE.value},
#                 ],
#                 value=AllocationType.UNALLOCATED.value,
#                 labelStyle={"display":"block", "margin":"6px 0"}
#             ),
#             dcc.Dropdown(id="alloc-target", placeholder="Choose office/employee (if applicable)", className="dash-dropdown"),
#             html.Button(button_label, id="add-asset-btn", className="btn"),
#             html.Div(id="asset-add-msg", style={"color":"crimson", "marginTop":"6px"}),
#             dcc.ConfirmDialog(id="asset-dialog"),
#         ]),
#         html.Div(className="card", children=[
#             html.H4(f"{header} Table"),
#             html.Div(id="assets-table")
#         ])
#     ])

# def requests_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Requests"),
#             html.Div(id="request-form"),
#             dcc.ConfirmDialog(id="req-dialog")
#         ]),
#         html.Div(className="card", children=[
#             html.H4("Open Requests"),
#             html.Div(id="requests-table")
#         ])
#     ])

# def reports_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role == Role.EMP:
#         return html.Div([navbar(), html.Div(className="card", children="Reports are not available for Employees.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Reports"),
#             html.Div(id="reports-content"),
#             dcc.ConfirmDialog(id="reports-dialog"),
#             html.Div(id="reports-msg", style={"color":"crimson", "marginTop":"6px"}),
#         ])
#     ])

# def employees_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role != Role.OM:
#         return html.Div([navbar(), html.Div(className="card", children="Only Office Managers can manage employees.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Manage Employees"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="emp-new-name", placeholder="Employee name *", className="input"),
#                 dcc.Input(id="emp-new-phone", placeholder="Phone", className="input"),
#                 dcc.Input(id="emp-new-username", placeholder="Username *", className="input"),
#                 dcc.Input(id="emp-new-password", placeholder="Password *", className="input"),
#             ]),
#             html.Button("Add Employee", id="emp-add-btn", className="btn"),
#             dcc.ConfirmDialog(id="emp-dialog"),
#             html.Div(id="emp-add-msg", style={"color":"crimson", "marginTop":"6px"})
#         ]),
#         html.Div(className="card", children=[
#             html.H4("Employees in My Office"),
#             html.Div(id="emp-table")
#         ])
#     ])

# def admin_layout():
#     user = current_user()
#     if not user or user.role != Role.GM:
#         return html.Div([navbar(), html.Div(className="card", children="Admins only.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Admin — Offices & Managers"),
#             html.H4("Create Office"),
#             dcc.Input(id="new-office-name", placeholder="Office name *", className="input"),
#             html.Button("Add Office", id="btn-add-office", className="btn"),
#             html.Div(id="msg-add-office", className="muted", style={"marginTop":"6px"}),
#             html.Div(className="hr"),
#             html.H4("Create Office Manager"),
#             html.Div(className="two-col", children=[
#                 dcc.Dropdown(id="om-office", placeholder="Select office", className="dash-dropdown"),
#                 dcc.Input(id="om-username", placeholder="Username *", className="input"),
#                 dcc.Input(id="om-password", placeholder="Password *", className="input"),
#             ]),
#             html.Button("Create OM", id="btn-create-om", className="btn"),
#             dcc.ConfirmDialog(id="admin-dialog"),
#             html.Div(id="msg-create-om", className="muted", style={"marginTop":"6px"}),
#             html.Div(className="hr"),
#             html.H4("Reset OM Password"),
#             html.Div(className="two-col", children=[
#                 dcc.Dropdown(id="om-existing", placeholder="Select OM user", className="dash-dropdown"),
#                 dcc.Input(id="om-new-pass", placeholder="New password *", className="input"),
#             ]),
#             html.Button("Reset Password", id="btn-om-reset", className="btn btn-outline"),
#             html.Div(id="msg-om-reset", className="muted", style={"marginTop":"6px"}),
#         ])
#     ])

# def profile_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("My Profile"),
#             html.Div(id="profile-form"),
#             dcc.ConfirmDialog(id="profile-dialog"),
#             html.Div(id="profile-msg", style={"color":"crimson", "marginTop":"6px"}),
#         ])
#     ])

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
#     if path == "/admin":
#         return admin_layout()
#     if path == "/profile":
#         return profile_layout()
#     return html.Div([navbar(), html.Div(className="card", children=html.H3("Not Found"))])

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

# # ---------- Dashboard KPIs ----------
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
#             count = s.query(Asset).count()
#             pending = s.query(Asset).filter(Asset.returned == False).count()  # noqa: E712
#         else:
#             emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#             assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#             ).all()
#             total_assets_cost = sum(a.price * a.quantity for a in assets)
#             count = len(assets)
#             pending = sum(1 for a in assets if not a.returned)
#         return html.Div(className="stack", children=[
#             html.Div(className="kpi", children=[html.Div("Assets", className="label"), html.Div(count, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Pending Returns", className="label"), html.Div(pending, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Total Cost", className="label"), html.Div(f"${total_assets_cost:,.2f}", className="value")]),
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
#     State("alloc-type", "value"), State("alloc-target", "value"),
#     prevent_initial_call=True
# )
# def add_asset(n, name, price, qty, contents, filename, alloc_type, alloc_target):
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
#         _, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
#         saved_path = os.path.join(UPLOAD_FOLDER, fname)
#         with open(saved_path, "wb") as f:
#             f.write(decoded)

#     with SessionLocal() as s:
#         a_type = AllocationType.UNALLOCATED
#         a_id = None
#         if alloc_type == AllocationType.OFFICE.value:
#             a_type = AllocationType.OFFICE
#             a_id = int(alloc_target) if alloc_target else (current_user().office_id or None)
#         elif alloc_type == AllocationType.EMPLOYEE.value:
#             a_type = AllocationType.EMPLOYEE
#             if alloc_target:
#                 a_id = int(alloc_target)
#             elif current_user().role == Role.EMP:
#                 emp = _employee_for_user(current_user(), s)
#                 a_id = emp.id if emp else None

#         s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
#                     allocation_type=a_type, allocation_id=a_id))
#         s.commit()
#     return ("", render_assets_table(), "Asset added.", True, "", "", 1, None)

# def _bill_link_path(path):
#     if not path:
#         return ""
#     base = os.path.basename(path)
#     return f"[{base}](/uploads/{quote(base)})"

# def _bill_link_asset(a):
#     return _bill_link_path(a.bill_path)

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
#             rows = [{"asset_no": i, "name": a.name, "price": a.price, "qty": a.quantity, "bill": _bill_link_asset(a)}
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
#         rows = [{"id":a.id,"name":a.name,"price":a.price,"qty":a.quantity,"bill":_bill_link_asset(a),
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

# # Dynamic options for allocation target
# @app.callback(
#     Output("alloc-target", "options"),
#     Output("alloc-target", "value"),
#     Output("alloc-target", "placeholder"),
#     Input("alloc-type", "value"),
#     Input("url", "pathname"),
# )
# def update_alloc_options(alloc_type, _):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         if alloc_type == AllocationType.OFFICE.value:
#             if user.role == Role.GM:
#                 offices = s.query(Office).order_by(Office.name).all()
#                 opts = [{"label": o.name, "value": o.id} for o in offices]
#                 return opts, None, "Select office"
#             else:
#                 return [{"label": "My Office", "value": user.office_id}], user.office_id, "My Office"
#         elif alloc_type == AllocationType.EMPLOYEE.value:
#             q = s.query(Employee)
#             if user.role == Role.OM:
#                 q = q.filter(Employee.office_id == user.office_id)
#             elif user.role == Role.EMP:
#                 emp = _employee_for_user(user, s)
#                 if emp:
#                     return [{"label": emp.name, "value": emp.id}], emp.id, "Myself"
#             emps = q.order_by(Employee.name).all()
#             return [{"label": e.name, "value": e.id} for e in emps], None, "Select employee"
#         return [], None, "No target (Global/Unallocated)"

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
#                 html.B("Create Request"),
#                 dcc.Dropdown(id="req-employee", options=options, value=(emp.id if emp else None), className="dash-dropdown", disabled=True),
#                 html.Div(className="two-col", children=[
#                     dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
#                     dcc.Input(id="req-qty", type="number", value=1, className="input"),
#                     dcc.Input(id="req-price", placeholder="Price", type="number", className="input"),
#                 ]),
#                 _uploader_component("req-bill"),
#                 html.Button("Submit Request", id="req-submit", className="btn"),
#                 html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#             ])
#         employees = s.query(Employee).filter(Employee.office_id == user.office_id).all() \
#             if user.role == Role.OM else s.query(Employee).all()
#         options = [{"label": e.name, "value": e.id} for e in employees]
#         return html.Div([
#             html.B("Create Request"),
#             dcc.Dropdown(id="req-employee", options=options, placeholder="Employee", className="dash-dropdown"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
#                 dcc.Input(id="req-qty", type="number", value=1, className="input"),
#                 dcc.Input(id="req-price", placeholder="Price", type="number", className="input"),
#             ]),
#             _uploader_component("req-bill"),
#             html.Button("Submit Request", id="req-submit", className="btn"),
#             html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#         ])

# @app.callback(
#     Output("req-msg", "children"),
#     Output("requests-table", "children", allow_duplicate=True),
#     Output("req-dialog","message"),
#     Output("req-dialog","displayed"),
#     Output("req-asset-name","value"),
#     Output("req-qty","value"),
#     Output("req-price","value"),
#     Output("req-bill","contents"),
#     Input("req-submit", "n_clicks"),
#     State("req-employee", "value"),
#     State("req-asset-name", "value"),
#     State("req-qty", "value"),
#     State("req-price", "value"),
#     State("req-bill", "contents"),
#     State("req-bill", "filename"),
#     prevent_initial_call=True
# )
# def create_request(n, emp_id, asset_name, qty, price, contents, filename):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     if not n or n < 1:
#         raise PreventUpdate
#     asset_name = (asset_name or "").strip()
#     try: qty = int(qty or 0)
#     except Exception: qty = 0
#     try: price_val = float(price or 0)
#     except Exception: price_val = 0.0
#     if not asset_name:
#         return "Please enter an asset name.", render_requests_table(), "", False, asset_name, qty, price, contents
#     if qty < 1:
#         return "Quantity must be at least 1.", render_requests_table(), "", False, asset_name, qty, price, contents

#     saved_path = None
#     if contents and filename:
#         _, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
#         saved_path = os.path.join(UPLOAD_FOLDER, fname)
#         with open(saved_path, "wb") as f:
#             f.write(decoded)

#     with SessionLocal() as s:
#         if user.role == Role.EMP and not emp_id:
#             emp = _employee_for_user(user, s)
#             emp_id = emp.id if emp else None
#         if not emp_id:
#             return "Select an employee.", render_requests_table(), "", False, asset_name, qty, price, contents
#         emp = s.get(Employee, emp_id)
#         if not emp:
#             return "Invalid employee.", render_requests_table(), "", False, asset_name, qty, price, contents
#         if user.role == Role.OM and emp.office_id != user.office_id:
#             return "You can only submit requests for your office.", render_requests_table(), "", False, asset_name, qty, price, contents
#         s.add(Request(employee_id=emp.id, office_id=emp.office_id, asset_name=asset_name,
#                       quantity=qty, price=price_val, bill_path=saved_path))
#         s.commit()
#     return "", render_requests_table(), "Request submitted.", True, "", 1, "", None

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
#         data = [{
#             "id":r.id,"employee_id":r.employee_id,"office_id":r.office_id,"asset":r.asset_name,
#             "qty":r.quantity,"price": r.price, "status":r.status.value,"remark":r.remark or "",
#             "bill": _bill_link_path(r.bill_path),
#             "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
#         } for r in rows]
#     cols = [
#         {"name":"id","id":"id"},
#         {"name":"employee_id","id":"employee_id"},
#         {"name":"office_id","id":"office_id"},
#         {"name":"asset","id":"asset"},
#         {"name":"qty","id":"qty"},
#         {"name":"price","id":"price"},
#         {"name":"status","id":"status"},
#         {"name":"remark","id":"remark"},
#         {"name":"bill","id":"bill","presentation":"markdown"},
#         {"name":"created_at","id":"created_at"},
#     ]

#     user = current_user()
#     controls = html.Div(className="stack", children=[
#         dcc.Textarea(id="mgr-remark", placeholder="Remark…", className="input", style={"height":"60px", "width":"420px"}),
#         html.Button("Approve", id="btn-approve", className="btn"),
#         html.Button("Reject", id="btn-reject", className="btn btn-danger"),
#         html.Button("Mark Return Pending", id="btn-return-pending", className="btn btn-outline"),
#         html.Button("Mark Returned", id="btn-returned", className="btn btn-outline"),
#     ]) if user and user.role in (Role.GM, Role.OM) else html.Div()

#     table = dash_table.DataTable(data=data, columns=cols, id="req-table",
#                                  row_selectable="single", page_size=10, style_table={"overflowX":"auto"})
#     return html.Div([table, html.Div(id="req-action-msg", style={"marginTop":"8px"}), controls])

# # ---------- Action buttons (approve-safe + proper undo) ----------
# @app.callback(
#     Output("req-action-msg", "children", allow_duplicate=True),
#     Output("requests-table", "children", allow_duplicate=True),
#     Input("btn-approve", "n_clicks"),
#     Input("btn-reject", "n_clicks"),
#     Input("btn-return-pending", "n_clicks"),
#     Input("btn-returned", "n_clicks"),
#     State("req-table", "selected_rows"), State("req-table", "data"),
#     State("mgr-remark", "value"),
#     prevent_initial_call=True
# )
# def handle_request_action(n1, n2, n3, n4, selected, data, remark):
#     user = current_user()
#     if not user or user.role not in (Role.GM, Role.OM):
#         return "Not allowed.", render_requests_table()
#     if not selected:
#         return "Select a request first.", render_requests_table()

#     mapping = {
#         "btn-approve": RequestStatus.APPROVED,
#         "btn-reject": RequestStatus.REJECTED,
#         "btn-return-pending": RequestStatus.RETURN_PENDING,
#         "btn-returned": RequestStatus.RETURNED,
#     }
#     trig = ctx.triggered_id
#     status = mapping.get(trig, None)
#     if status is None:
#         raise PreventUpdate

#     req_id = data[selected[0]]["id"]

#     with SessionLocal() as s:
#         r = s.get(Request, req_id)
#         if not r:
#             return "Request not found.", render_requests_table()
#         if user.role == Role.OM and r.office_id != user.office_id:
#             return "You can only update requests in your office.", render_requests_table()

#         if remark:
#             r.remark = remark

#         if status == RequestStatus.APPROVED:
#             # Create asset only once
#             if not getattr(r, "fulfilled_asset_id", None):
#                 a = Asset(
#                     name=r.asset_name,
#                     price=float(r.price or 0),
#                     quantity=int(r.quantity or 1),
#                     bill_path=r.bill_path,
#                     allocation_type=AllocationType.EMPLOYEE,
#                     allocation_id=r.employee_id
#                 )
#                 s.add(a); s.flush()
#                 r.fulfilled_asset_id = a.id
#             r.status = RequestStatus.APPROVED

#         else:
#             # Moving away from approved:
#             if getattr(r, "fulfilled_asset_id", None):
#                 asset = s.get(Asset, r.fulfilled_asset_id)
#                 if asset:
#                     if status == RequestStatus.RETURNED:
#                         asset.returned = True
#                     elif status in (RequestStatus.REJECTED, RequestStatus.RETURN_PENDING):
#                         s.delete(asset)
#                         r.fulfilled_asset_id = None
#             r.status = status

#         s.commit()

#     return f"Status updated to {status.value}.", render_requests_table()

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
#     return dash_table.DataTable(data=data, columns=cols, page_size=10, style_table={"overflowX":"auto"})

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

# # ---------- GM Admin ----------
# @app.callback(Output("om-office","options"), Output("om-existing","options"), Input("url","pathname"))
# @login_required(Role.GM)
# def load_admin_dropdowns(_):
#     with SessionLocal() as s:
#         offices = s.query(Office).order_by(Office.name).all()
#         oms = s.query(User).filter(User.role == Role.OM).order_by(User.username).all()
#         return (
#             [{"label": o.name, "value": o.id} for o in offices],
#             [{"label": u.username, "value": u.id} for u in oms]
#         )

# @app.callback(
#     Output("msg-add-office","children"),
#     Output("om-office","options", allow_duplicate=True),
#     Input("btn-add-office","n_clicks"),
#     State("new-office-name","value"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def add_office(n, office_name):
#     name = (office_name or "").strip()
#     with SessionLocal() as s:
#         if not name:
#             offices = s.query(Office).order_by(Office.name).all()
#             return "Office name is required.", [{"label": o.name, "value": o.id} for o in offices]
#         if s.query(Office).filter(Office.name.ilike(name)).first():
#             offices = s.query(Office).order_by(Office.name).all()
#             return "Office already exists.", [{"label": o.name, "value": o.id} for o in offices]
#         s.add(Office(name=name))
#         s.commit()
#         offices = s.query(Office).order_by(Office.name).all()
#     return "Office created.", [{"label": o.name, "value": o.id} for o in offices]

# @app.callback(
#     Output("msg-create-om","children"),
#     Output("admin-dialog","message"),
#     Output("admin-dialog","displayed"),
#     Output("om-username","value"),
#     Output("om-password","value"),
#     State("om-office","value"),
#     State("om-username","value"),
#     State("om-password","value"),
#     Input("btn-create-om","n_clicks"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def create_om(office_id, uname, pwd, n):
#     uname = (uname or "").strip()
#     pwd = (pwd or "")
#     if not office_id or not uname or not pwd:
#         return ("All fields are required.", "", False, uname, pwd)
#     with SessionLocal() as s:
#         if not s.get(Office, office_id):
#             return ("Invalid office.", "", False, uname, pwd)
#         if s.query(User).filter(User.username == uname).first():
#             return ("Username already exists.", "", False, uname, pwd)
#         s.add(User(username=uname, password_hash=generate_password_hash(pwd), role=Role.OM, office_id=office_id))
#         s.commit()
#     return ("OM created.", "Office Manager created successfully.", True, "", "")

# @app.callback(
#     Output("msg-om-reset","children"),
#     State("om-existing","value"),
#     State("om-new-pass","value"),
#     Input("btn-om-reset","n_clicks"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def reset_om_password(om_id, new_pass, n):
#     new_pass = (new_pass or "").strip()
#     if not om_id or not new_pass:
#         return "Select an OM and enter a new password."
#     with SessionLocal() as s:
#         u = s.get(User, om_id)
#         if not u or u.role != Role.OM:
#             return "Invalid OM selected."
#         u.password_hash = generate_password_hash(new_pass)
#         s.commit()
#     return "Password reset."

# # ---------- Reports (GM + OM) ----------
# @app.callback(Output("reports-content","children"), Input("url","pathname"))
# def render_reports(_):
#     user = current_user()
#     if not user or user.role == Role.EMP:
#         raise PreventUpdate

#     with SessionLocal() as s:
#         if user.role == Role.GM:
#             all_assets = s.query(Asset).all()
#             company_count = len(all_assets)
#             company_cost = sum(a.price * a.quantity for a in all_assets)
#             company_pending = sum(1 for a in all_assets if not a.returned)

#             offices = s.query(Office).order_by(Office.name).all()
#             office_options = [{"label": o.name, "value": o.id} for o in offices]
#             emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).order_by(Employee.name)]

#             return html.Div([
#                 html.Div(className="stack", children=[
#                     html.Div(className="kpi", children=[html.Div("Company assets", className="label"), html.Div(company_count, className="value")]),
#                     html.Div(className="kpi", children=[html.Div("Company total cost", className="label"), html.Div(f"${company_cost:,.2f}", className="value")]),
#                     html.Div(className="kpi", children=[html.Div("Company pending returns", className="label"), html.Div(company_pending, className="value")]),
#                 ]),
#                 html.Div(className="hr"),
#                 html.B("Per-Office Analytics"),
#                 dcc.Dropdown(id="rep-office", options=office_options, placeholder="Select office", className="dash-dropdown"),
#                 html.Div(id="rep-office-kpis", style({"marginTop":"8px"})),
#                 html.Div(className="hr"),
#                 html.B("Per-Employee Analytics"),
#                 dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#                 html.Div(id="rep-emp-kpis", style({"marginTop":"8px"})),
#                 html.Div(className="hr"),
#                 html.B("Add Remark for Employee"),
#                 dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#                 dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input", style={"height":"80px"}),
#                 html.Button("Add Remark", id="rep-add-remark", className="btn"),
#                 html.Div(id="rep-remark-msg", className="muted", style({"marginTop":"6px"}))
#             ])

#         # OM scope
#         emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#         office_assets = s.query(Asset).filter(
#             ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#             ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#         ).all()
#         office_count = len(office_assets)
#         office_cost = sum(a.price * a.quantity for a in office_assets)
#         emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).filter(Employee.office_id == user.office_id)]

#         return html.Div([
#             html.Div(className="kpi", children=[html.Div("Assets in my office", className="label"), html.Div(office_count, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Total cost for my office", className="label"), html.Div(f"${office_cost:,.2f}", className="value")]),
#             html.Div(className="hr"),
#             html.B("Per-Employee Analytics"),
#             dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#             html.Div(id="rep-emp-kpis", style({"marginTop":"8px"})),
#             html.Div(className="hr"),
#             html.B("Add Remark for Employee"),
#             dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#             dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input"),
#             html.Button("Add Remark", id="rep-add-remark", className="btn"),
#             html.Div(id="rep-remark-msg", className="muted", style({"marginTop":"6px"}))
#         ])

# @app.callback(Output("rep-office-kpis","children"), Input("rep-office","value"), prevent_initial_call=True)
# @login_required(Role.GM)
# def per_office_kpis(office_id):
#     if not office_id:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == office_id)]
#         assets = s.query(Asset).filter(
#             ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == office_id)) |
#             ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#         ).all()
#         count = len(assets)
#         pending = sum(1 for a in assets if not a.returned)
#         cost = sum(a.price * a.quantity for a in assets)
#     return html.Ul([
#         html.Li(f"Assets in office: {count}"),
#         html.Li(f"Pending returns: {pending}"),
#         html.Li(f"Total cost: ${cost:,.2f}")
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
#         office = s.get(Office, user.office_id) if user.office_id else None
#         return html.Div([
#             html.Div([
#                 html.Div(f"User: {user.username}"),
#                 html.Div(f"Role: {role_name(user.role.value)}"),
#                 html.Div(f"Employee ID: {emp.id if emp else '—'}"),
#                 html.Div(f"Office ID: {office.id if office else '—'}"),
#                 html.Div(f"Office Name: {office.name if office else '—'}"),
#             ], style={"marginBottom":"8px"}),
#             dcc.Input(id="profile-emp-name", placeholder="Employee name", value=(emp.name if emp else ""), className="input"),
#             dcc.Input(id="profile-phone", placeholder="Phone number", value=getattr(emp, "phone", "") if emp else "", className="input"),
#             html.Button("Save Profile", id="btn-save-profile", n_clicks=0, type="button", className="btn"),
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


# ---------------------------------------------------------------- above is okok good ------------------------------------------------------------------------------------------------------------------

# # app.py
# from sqlalchemy import text
# import os, datetime, base64
# from functools import wraps
# from urllib.parse import quote

# import dash
# from dash import Dash, html, dcc, Input, Output, State, dash_table, ctx
# from dash.exceptions import PreventUpdate
# from werkzeug.security import check_password_hash, generate_password_hash
# from flask import session, send_from_directory

# from db import (
#     init_db, SessionLocal, Role, AllocationType, RequestStatus,
#     Office, User, Employee, Asset, Request, Remark, engine
# )

# # ---------- tiny migrations (idempotent) ----------
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
# # ensure request extras exist even if db.py migration didn't run yet
# _safe_add_column("requests", "price FLOAT")
# _safe_add_column("requests", "bill_path VARCHAR")
# _safe_add_column("requests", "fulfilled_asset_id INTEGER")

# UPLOAD_FOLDER = os.environ.get("RMS_UPLOAD_DIR", "uploads")
# os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# # Initialize DB
# if not os.path.exists("rms.db"):
#     init_db(seed=True)
# else:
#     init_db(seed=False)

# # ---------- Dash ----------
# app = Dash(__name__, suppress_callback_exceptions=True, serve_locally=False)
# server = app.server
# server.secret_key = os.environ.get("RMS_SECRET", "dev-secret-key")

# # Pretty HTML shell + theme
# app.index_string = """
# <!DOCTYPE html>
# <html>
# <head>
#   <meta charset="UTF-8">
#   <title>RMS</title>
#   <link rel="preconnect" href="https://fonts.googleapis.com">
#   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
#   <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
#   {%metas%}{%favicon%}{%css%}
#   <style>
#     :root{
#       --bg:#f7f8fb; --card:#ffffff; --text:#131824; --muted:#6b7280;
#       --primary:#6366f1; --primary-600:#5458ee; --danger:#ef4444; --border:#e5e7eb;
#       --radius:12px; --shadow:0 6px 18px rgba(17,24,39,.06);
#     }
#     html,body{height:100%;}
#     body{background:var(--bg); font-family:'Inter',system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial; color:var(--text); line-height:1.35; padding:24px;}
#     nav a{ color:var(--primary); text-decoration:none; font-weight:600; }
#     nav a:hover{ text-decoration:underline; }
#     nav{ background:var(--card); padding:10px 14px; border:1px solid var(--border);
#          border-radius:var(--radius); box-shadow:var(--shadow); margin-bottom:16px;}
#     h2,h3,h4{ margin:8px 0 12px 0; }
#     .card{ background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
#            box-shadow:var(--shadow); padding:16px; margin:10px 0;}
#     .btn{ background:var(--primary); color:white; border:none; padding:8px 14px;
#           border-radius:10px; font-weight:600; cursor:pointer; transition:.15s transform ease, .15s background ease;
#           margin-right:8px; margin-top:6px;}
#     .btn:hover{ background:var(--primary-600); transform:translateY(-1px); }
#     .btn-outline{ background:transparent; color:var(--primary); border:1px solid var(--primary); }
#     .btn-danger{ background:var(--danger); }
#     .input, .dash-dropdown, textarea{ padding:8px 10px; border:1px solid var(--border); border-radius:10px;
#        background:white; outline:none; width:100%; max-width:560px; margin-right:8px; margin-bottom:8px;}
#     .two-col{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }
#     .kpi{ display:inline-block; min-width:210px; padding:14px 16px; margin-right:10px;
#           background:linear-gradient(180deg, #fff, #fbfbff); border:1px solid var(--border);
#           border-radius:14px; box-shadow:var(--shadow); }
#     .kpi .label{ color:#6b7280; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.06em;}
#     .kpi .value{ font-size:22px; font-weight:700; margin-top:4px;}
#     .hr{ height:1px; background:var(--border); margin:16px 0;}
#     .muted{ color:#6b7280; }
#     .stack{ display:flex; flex-wrap:wrap; gap:8px; align-items:center;}
#   </style>
# </head>
# <body>
#   {%app_entry%}
#   <footer>{%config%}{%scripts%}{%renderer%}</footer>
# </body>
# </html>
# """

# # ---------- Helpers ----------
# def current_user():
#     uid = session.get("user_id")
#     if not uid:
#         return None
#     with SessionLocal() as s:
#         u = s.get(User, uid)
#         if not u:
#             return None
#         if u.office_id:
#             _ = s.get(Office, u.office_id)
#         return u

# def _employee_for_user(user, s):
#     if not user or not user.office_id:
#         return None
#     emp = s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.username == user.username
#     ).first()
#     if emp:
#         return emp
#     return s.query(Employee).filter(
#         Employee.office_id == user.office_id,
#         Employee.name.ilike((user.username or "").strip())
#     ).first()

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
#     items = []
#     if user.role == Role.EMP:
#         items = [
#             dcc.Link("Dashboard", href="/"), html.Span(" | "),
#             dcc.Link("My Assets", href="/assets"), html.Span(" | "),
#             dcc.Link("Requests", href="/requests"), html.Span(" | "),
#             dcc.Link("My Profile", href="/profile"), html.Span(" | "),
#         ]
#     else:
#         items = [
#             dcc.Link("Dashboard", href="/"), html.Span(" | "),
#             dcc.Link("Assets", href="/assets"), html.Span(" | "),
#             dcc.Link("Requests", href="/requests"), html.Span(" | "),
#             dcc.Link("Reports", href="/reports"), html.Span(" | "),
#         ]
#         if user.role == Role.GM:
#             items.extend([dcc.Link("Admin", href="/admin"), html.Span(" | ")])
#         else:
#             items.extend([dcc.Link("Employees", href="/employees"), html.Span(" | ")])
#     items.append(dcc.Link("Logout", href="/logout"))
#     return html.Nav(items)

# def login_layout():
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H2("Resource Management System — Login"),
#             dcc.Input(id="login-username", placeholder="Username", className="input"),
#             dcc.Input(id="login-password", type="password", placeholder="Password", className="input"),
#             html.Button("Login", id="login-btn", className="btn"),
#             html.Div(id="login-msg", style={"color": "crimson", "marginTop": "8px"}),
#             html.Div(className="muted", children="Default demo users: admin/admin, om_east/om_east, alice/alice")
#         ])
#     ])

# def dashboard_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     scope = "Company-wide" if user.role == Role.GM else "Your office"
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(f"Dashboard — {role_name(user.role.value)}"),
#             html.Div(className="muted", children=scope),
#             html.Div(id="dashboard-cards", className="pad-top")
#         ])
#     ])

# def _uploader_component(id_):
#     return dcc.Upload(
#         id=id_,
#         children=html.Button("Upload Bill / Drag & Drop", className="btn btn-outline"),
#         multiple=False
#     )

# def assets_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     header = "My Assets" if user.role == Role.EMP else "Assets"
#     button_label = "Add to My Profile" if user.role == Role.EMP else "Add Asset"
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(header),
#             _uploader_component("upload-bill"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="asset-name", placeholder="Asset name *", className="input"),
#                 dcc.Input(id="asset-price", placeholder="Price *", type="number", className="input"),
#                 dcc.Input(id="asset-qty", placeholder="Quantity *", type="number", value=1, className="input"),
#             ]),
#             dcc.RadioItems(
#                 id="alloc-type",
#                 options=[
#                     {"label":"Global / Unallocated", "value": AllocationType.UNALLOCATED.value},
#                     {"label":"Allocate to Office", "value": AllocationType.OFFICE.value},
#                     {"label":"Allocate to Employee", "value": AllocationType.EMPLOYEE.value},
#                 ],
#                 value=AllocationType.UNALLOCATED.value,
#                 labelStyle={"display":"block", "margin":"6px 0"}
#             ),
#             dcc.Dropdown(id="alloc-target", placeholder="Choose office/employee (if applicable)", className="dash-dropdown"),
#             html.Button(button_label, id="add-asset-btn", className="btn"),
#             html.Div(id="asset-add-msg", style={"color":"crimson", "marginTop":"6px"}),
#             dcc.ConfirmDialog(id="asset-dialog"),
#         ]),
#         html.Div(className="card", children=[
#             html.H4(f"{header} Table"),
#             html.Div(id="assets-table")
#         ])
#     ])

# def requests_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Requests"),
#             html.Div(id="request-form"),
#             dcc.ConfirmDialog(id="req-dialog")
#         ]),
#         html.Div(className="card", children=[
#             html.H4("Open Requests"),
#             html.Div(id="requests-table")
#         ])
#     ])

# def reports_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role == Role.EMP:
#         return html.Div([navbar(), html.Div(className="card", children="Reports are not available for Employees.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Reports"),
#             html.Div(id="reports-content"),
#             dcc.ConfirmDialog(id="reports-dialog"),
#             html.Div(id="reports-msg", style={"color":"crimson", "marginTop":"6px"}),
#         ])
#     ])

# def employees_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role != Role.OM:
#         return html.Div([navbar(), html.Div(className="card", children="Only Office Managers can manage employees.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Manage Employees"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="emp-new-name", placeholder="Employee name *", className="input"),
#                 dcc.Input(id="emp-new-phone", placeholder="Phone", className="input"),
#                 dcc.Input(id="emp-new-username", placeholder="Username *", className="input"),
#                 dcc.Input(id="emp-new-password", placeholder="Password *", className="input"),
#             ]),
#             html.Button("Add Employee", id="emp-add-btn", className="btn"),
#             dcc.ConfirmDialog(id="emp-dialog"),
#             html.Div(id="emp-add-msg", style={"color":"crimson", "marginTop":"6px"})
#         ]),
#         html.Div(className="card", children=[
#             html.H4("Employees in My Office"),
#             html.Div(id="emp-table")
#         ])
#     ])

# def admin_layout():
#     user = current_user()
#     if not user or user.role != Role.GM:
#         return html.Div([navbar(), html.Div(className="card", children="Admins only.")])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("Admin — Offices & Managers"),
#             html.H4("Create Office"),
#             dcc.Input(id="new-office-name", placeholder="Office name *", className="input"),
#             html.Button("Add Office", id="btn-add-office", className="btn"),
#             html.Div(id="msg-add-office", className="muted", style={"marginTop":"6px"}),
#             html.Div(className="hr"),
#             html.H4("Create Office Manager"),
#             html.Div(className="two-col", children=[
#                 dcc.Dropdown(id="om-office", placeholder="Select office", className="dash-dropdown"),
#                 dcc.Input(id="om-username", placeholder="Username *", className="input"),
#                 dcc.Input(id="om-password", placeholder="Password *", className="input"),
#             ]),
#             html.Button("Create OM", id="btn-create-om", className="btn"),
#             dcc.ConfirmDialog(id="admin-dialog"),
#             html.Div(id="msg-create-om", className="muted", style={"marginTop":"6px"}),
#             html.Div(className="hr"),
#             html.H4("Reset OM Password"),
#             html.Div(className="two-col", children=[
#                 dcc.Dropdown(id="om-existing", placeholder="Select OM user", className="dash-dropdown"),
#                 dcc.Input(id="om-new-pass", placeholder="New password *", className="input"),
#             ]),
#             html.Button("Reset Password", id="btn-om-reset", className="btn btn-outline"),
#             html.Div(id="msg-om-reset", className="muted", style={"marginTop":"6px"}),
#         ])
#     ])

# def profile_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("My Profile"),
#             html.Div(id="profile-form"),
#             dcc.ConfirmDialog(id="profile-dialog"),
#             html.Div(id="profile-msg", style={"color":"crimson", "marginTop":"6px"}),
#         ])
#     ])

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
#     if path == "/admin":
#         return admin_layout()
#     if path == "/profile":
#         return profile_layout()
#     return html.Div([navbar(), html.Div(className="card", children=html.H3("Not Found"))])

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

# # ---------- Dashboard KPIs ----------
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
#             count = s.query(Asset).count()
#             pending = s.query(Asset).filter(Asset.returned == False).count()  # noqa: E712
#         else:
#             emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#             assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#             ).all()
#             total_assets_cost = sum(a.price * a.quantity for a in assets)
#             count = len(assets)
#             pending = sum(1 for a in assets if not a.returned)
#         return html.Div(className="stack", children=[
#             html.Div(className="kpi", children=[html.Div("Assets", className="label"), html.Div(count, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Pending Returns", className="label"), html.Div(pending, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Total Cost", className="label"), html.Div(f"${total_assets_cost:,.2f}", className="value")]),
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
#     State("alloc-type", "value"), State("alloc-target", "value"),
#     prevent_initial_call=True
# )
# def add_asset(n, name, price, qty, contents, filename, alloc_type, alloc_target):
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
#         _, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
#         saved_path = os.path.join(UPLOAD_FOLDER, fname)
#         with open(saved_path, "wb") as f:
#             f.write(decoded)

#     with SessionLocal() as s:
#         a_type = AllocationType.UNALLOCATED
#         a_id = None
#         if alloc_type == AllocationType.OFFICE.value:
#             a_type = AllocationType.OFFICE
#             a_id = int(alloc_target) if alloc_target else (current_user().office_id or None)
#         elif alloc_type == AllocationType.EMPLOYEE.value:
#             a_type = AllocationType.EMPLOYEE
#             if alloc_target:
#                 a_id = int(alloc_target)
#             elif current_user().role == Role.EMP:
#                 emp = _employee_for_user(current_user(), s)
#                 a_id = emp.id if emp else None

#         s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
#                     allocation_type=a_type, allocation_id=a_id))
#         s.commit()
#     return ("", render_assets_table(), "Asset added.", True, "", "", 1, None)

# def _bill_link_path(path):
#     if not path:
#         return ""
#     base = os.path.basename(path)
#     return f"[{base}](/uploads/{quote(base)})"

# def _bill_link_asset(a):
#     return _bill_link_path(a.bill_path)

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
#             rows = [{"asset_no": i, "name": a.name, "price": a.price, "qty": a.quantity, "bill": _bill_link_asset(a)}
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
#         rows = [{"id":a.id,"name":a.name,"price":a.price,"qty":a.quantity,"bill":_bill_link_asset(a),
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

# # Dynamic options for allocation target
# @app.callback(
#     Output("alloc-target", "options"),
#     Output("alloc-target", "value"),
#     Output("alloc-target", "placeholder"),
#     Input("alloc-type", "value"),
#     Input("url", "pathname"),
# )
# def update_alloc_options(alloc_type, _):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         if alloc_type == AllocationType.OFFICE.value:
#             if user.role == Role.GM:
#                 offices = s.query(Office).order_by(Office.name).all()
#                 opts = [{"label": o.name, "value": o.id} for o in offices]
#                 return opts, None, "Select office"
#             else:
#                 return [{"label": "My Office", "value": user.office_id}], user.office_id, "My Office"
#         elif alloc_type == AllocationType.EMPLOYEE.value:
#             q = s.query(Employee)
#             if user.role == Role.OM:
#                 q = q.filter(Employee.office_id == user.office_id)
#             elif user.role == Role.EMP:
#                 emp = _employee_for_user(user, s)
#                 if emp:
#                     return [{"label": emp.name, "value": emp.id}], emp.id, "Myself"
#             emps = q.order_by(Employee.name).all()
#             return [{"label": e.name, "value": e.id} for e in emps], None, "Select employee"
#         return [], None, "No target (Global/Unallocated)"

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
#                 html.B("Create Request"),
#                 dcc.Dropdown(id="req-employee", options=options, value=(emp.id if emp else None), className="dash-dropdown", disabled=True),
#                 html.Div(className="two-col", children=[
#                     dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
#                     dcc.Input(id="req-qty", type="number", value=1, className="input"),
#                     dcc.Input(id="req-price", placeholder="Price", type="number", className="input"),
#                 ]),
#                 _uploader_component("req-bill"),
#                 html.Button("Submit Request", id="req-submit", className="btn"),
#                 html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#             ])
#         employees = s.query(Employee).filter(Employee.office_id == user.office_id).all() \
#             if user.role == Role.OM else s.query(Employee).all()
#         options = [{"label": e.name, "value": e.id} for e in employees]
#         return html.Div([
#             html.B("Create Request"),
#             dcc.Dropdown(id="req-employee", options=options, placeholder="Employee", className="dash-dropdown"),
#             html.Div(className="two-col", children=[
#                 dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
#                 dcc.Input(id="req-qty", type="number", value=1, className="input"),
#                 dcc.Input(id="req-price", placeholder="Price", type="number", className="input"),
#             ]),
#             _uploader_component("req-bill"),
#             html.Button("Submit Request", id="req-submit", className="btn"),
#             html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
#         ])

# @app.callback(
#     Output("req-msg", "children"),
#     Output("requests-table", "children", allow_duplicate=True),
#     Output("req-dialog","message"),
#     Output("req-dialog","displayed"),
#     Output("req-asset-name","value"),
#     Output("req-qty","value"),
#     Output("req-price","value"),
#     Output("req-bill","contents"),
#     Input("req-submit", "n_clicks"),
#     State("req-employee", "value"),
#     State("req-asset-name", "value"),
#     State("req-qty", "value"),
#     State("req-price", "value"),
#     State("req-bill", "contents"),
#     State("req-bill", "filename"),
#     prevent_initial_call=True
# )
# def create_request(n, emp_id, asset_name, qty, price, contents, filename):
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     if not n or n < 1:
#         raise PreventUpdate
#     asset_name = (asset_name or "").strip()
#     try: qty = int(qty or 0)
#     except Exception: qty = 0
#     try: price_val = float(price or 0)
#     except Exception: price_val = 0.0
#     if not asset_name:
#         return "Please enter an asset name.", render_requests_table(), "", False, asset_name, qty, price, contents
#     if qty < 1:
#         return "Quantity must be at least 1.", render_requests_table(), "", False, asset_name, qty, price, contents

#     saved_path = None
#     if contents and filename:
#         _, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
#         saved_path = os.path.join(UPLOAD_FOLDER, fname)
#         with open(saved_path, "wb") as f:
#             f.write(decoded)

#     with SessionLocal() as s:
#         if user.role == Role.EMP and not emp_id:
#             emp = _employee_for_user(user, s)
#             emp_id = emp.id if emp else None
#         if not emp_id:
#             return "Select an employee.", render_requests_table(), "", False, asset_name, qty, price, contents
#         emp = s.get(Employee, emp_id)
#         if not emp:
#             return "Invalid employee.", render_requests_table(), "", False, asset_name, qty, price, contents
#         if user.role == Role.OM and emp.office_id != user.office_id:
#             return "You can only submit requests for your office.", render_requests_table(), "", False, asset_name, qty, price, contents
#         s.add(Request(employee_id=emp.id, office_id=emp.office_id, asset_name=asset_name,
#                       quantity=qty, price=price_val, bill_path=saved_path))
#         s.commit()
#     return "", render_requests_table(), "Request submitted.", True, "", 1, "", None

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
#         data = [{
#             "id":r.id,"employee_id":r.employee_id,"office_id":r.office_id,"asset":r.asset_name,
#             "qty":r.quantity,"price": r.price, "status":r.status.value,"remark":r.remark or "",
#             "bill": _bill_link_path(r.bill_path),
#             "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
#         } for r in rows]
#     cols = [
#         {"name":"id","id":"id"},
#         {"name":"employee_id","id":"employee_id"},
#         {"name":"office_id","id":"office_id"},
#         {"name":"asset","id":"asset"},
#         {"name":"qty","id":"qty"},
#         {"name":"price","id":"price"},
#         {"name":"status","id":"status"},
#         {"name":"remark","id":"remark"},
#         {"name":"bill","id":"bill","presentation":"markdown"},
#         {"name":"created_at","id":"created_at"},
#     ]

#     user = current_user()
#     controls = html.Div(className="stack", children=[
#         dcc.Textarea(id="mgr-remark", placeholder="Remark…", className="input", style={"height":"60px", "width":"420px"}),
#         html.Button("Approve", id="btn-approve", className="btn"),
#         html.Button("Reject", id="btn-reject", className="btn btn-danger"),
#         html.Button("Mark Return Pending", id="btn-return-pending", className="btn btn-outline"),
#         html.Button("Mark Returned", id="btn-returned", className="btn btn-outline"),
#     ]) if user and user.role in (Role.GM, Role.OM) else html.Div()

#     table = dash_table.DataTable(data=data, columns=cols, id="req-table",
#                                  row_selectable="single", page_size=10, style_table={"overflowX":"auto"})
#     return html.Div([table, html.Div(id="req-action-msg", style={"marginTop":"8px"}), controls])

# # ---------- Action buttons (approve-safe + proper undo) ----------
# @app.callback(
#     Output("req-action-msg", "children", allow_duplicate=True),
#     Output("requests-table", "children", allow_duplicate=True),
#     Input("btn-approve", "n_clicks"),
#     Input("btn-reject", "n_clicks"),
#     Input("btn-return-pending", "n_clicks"),
#     Input("btn-returned", "n_clicks"),
#     State("req-table", "selected_rows"), State("req-table", "data"),
#     State("mgr-remark", "value"),
#     prevent_initial_call=True
# )
# def handle_request_action(n1, n2, n3, n4, selected, data, remark):
#     user = current_user()
#     if not user or user.role not in (Role.GM, Role.OM):
#         return "Not allowed.", render_requests_table()
#     if not selected:
#         return "Select a request first.", render_requests_table()

#     mapping = {
#         "btn-approve": RequestStatus.APPROVED,
#         "btn-reject": RequestStatus.REJECTED,
#         "btn-return-pending": RequestStatus.RETURN_PENDING,
#         "btn-returned": RequestStatus.RETURNED,
#     }
#     trig = ctx.triggered_id
#     status = mapping.get(trig, None)
#     if status is None:
#         raise PreventUpdate

#     req_id = data[selected[0]]["id"]

#     with SessionLocal() as s:
#         r = s.get(Request, req_id)
#         if not r:
#             return "Request not found.", render_requests_table()
#         if user.role == Role.OM and r.office_id != user.office_id:
#             return "You can only update requests in your office.", render_requests_table()

#         if remark:
#             r.remark = remark

#         if status == RequestStatus.APPROVED:
#             # Create asset only once
#             if not getattr(r, "fulfilled_asset_id", None):
#                 a = Asset(
#                     name=r.asset_name,
#                     price=float(r.price or 0),
#                     quantity=int(r.quantity or 1),
#                     bill_path=r.bill_path,
#                     allocation_type=AllocationType.EMPLOYEE,
#                     allocation_id=r.employee_id
#                 )
#                 s.add(a); s.flush()
#                 r.fulfilled_asset_id = a.id
#             r.status = RequestStatus.APPROVED

#         else:
#             # Moving away from approved:
#             if getattr(r, "fulfilled_asset_id", None):
#                 asset = s.get(Asset, r.fulfilled_asset_id)
#                 if asset:
#                     if status == RequestStatus.RETURNED:
#                         asset.returned = True
#                     elif status in (RequestStatus.REJECTED, RequestStatus.RETURN_PENDING):
#                         s.delete(asset)
#                         r.fulfilled_asset_id = None
#             r.status = status

#         s.commit()

#     return f"Status updated to {status.value}.", render_requests_table()

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
#     return dash_table.DataTable(data=data, columns=cols, page_size=10, style_table={"overflowX":"auto"})

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

# # ---------- GM Admin ----------
# @app.callback(Output("om-office","options"), Output("om-existing","options"), Input("url","pathname"))
# @login_required(Role.GM)
# def load_admin_dropdowns(_):
#     with SessionLocal() as s:
#         offices = s.query(Office).order_by(Office.name).all()
#         oms = s.query(User).filter(User.role == Role.OM).order_by(User.username).all()
#         return (
#             [{"label": o.name, "value": o.id} for o in offices],
#             [{"label": u.username, "value": u.id} for u in oms]
#         )

# @app.callback(
#     Output("msg-add-office","children"),
#     Output("om-office","options", allow_duplicate=True),
#     Input("btn-add-office","n_clicks"),
#     State("new-office-name","value"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def add_office(n, office_name):
#     name = (office_name or "").strip()
#     with SessionLocal() as s:
#         if not name:
#             offices = s.query(Office).order_by(Office.name).all()
#             return "Office name is required.", [{"label": o.name, "value": o.id} for o in offices]
#         if s.query(Office).filter(Office.name.ilike(name)).first():
#             offices = s.query(Office).order_by(Office.name).all()
#             return "Office already exists.", [{"label": o.name, "value": o.id} for o in offices]
#         s.add(Office(name=name))
#         s.commit()
#         offices = s.query(Office).order_by(Office.name).all()
#     return "Office created.", [{"label": o.name, "value": o.id} for o in offices]

# @app.callback(
#     Output("msg-create-om","children"),
#     Output("admin-dialog","message"),
#     Output("admin-dialog","displayed"),
#     Output("om-username","value"),
#     Output("om-password","value"),
#     State("om-office","value"),
#     State("om-username","value"),
#     State("om-password","value"),
#     Input("btn-create-om","n_clicks"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def create_om(office_id, uname, pwd, n):
#     uname = (uname or "").strip()
#     pwd = (pwd or "")
#     if not office_id or not uname or not pwd:
#         return ("All fields are required.", "", False, uname, pwd)
#     with SessionLocal() as s:
#         if not s.get(Office, office_id):
#             return ("Invalid office.", "", False, uname, pwd)
#         if s.query(User).filter(User.username == uname).first():
#             return ("Username already exists.", "", False, uname, pwd)
#         s.add(User(username=uname, password_hash=generate_password_hash(pwd), role=Role.OM, office_id=office_id))
#         s.commit()
#     return ("OM created.", "Office Manager created successfully.", True, "", "")

# @app.callback(
#     Output("msg-om-reset","children"),
#     State("om-existing","value"),
#     State("om-new-pass","value"),
#     Input("btn-om-reset","n_clicks"),
#     prevent_initial_call=True
# )
# @login_required(Role.GM)
# def reset_om_password(om_id, new_pass, n):
#     new_pass = (new_pass or "").strip()
#     if not om_id or not new_pass:
#         return "Select an OM and enter a new password."
#     with SessionLocal() as s:
#         u = s.get(User, om_id)
#         if not u or u.role != Role.OM:
#             return "Invalid OM selected."
#         u.password_hash = generate_password_hash(new_pass)
#         s.commit()
#     return "Password reset."

# # ---------- Reports (GM + OM) ----------
# @app.callback(Output("reports-content","children"), Input("url","pathname"))
# def render_reports(_):
#     user = current_user()
#     if not user or user.role == Role.EMP:
#         raise PreventUpdate

#     with SessionLocal() as s:
#         if user.role == Role.GM:
#             all_assets = s.query(Asset).all()
#             company_count = len(all_assets)
#             company_cost = sum(a.price * a.quantity for a in all_assets)
#             company_pending = sum(1 for a in all_assets if not a.returned)

#             offices = s.query(Office).order_by(Office.name).all()
#             office_options = [{"label": o.name, "value": o.id} for o in offices]
#             emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).order_by(Employee.name)]

#             return html.Div([
#                 html.Div(className="stack", children=[
#                     html.Div(className="kpi", children=[html.Div("Company assets", className="label"), html.Div(company_count, className="value")]),
#                     html.Div(className="kpi", children=[html.Div("Company total cost", className="label"), html.Div(f"${company_cost:,.2f}", className="value")]),
#                     html.Div(className="kpi", children=[html.Div("Company pending returns", className="label"), html.Div(company_pending, className="value")]),
#                 ]),
#                 html.Div(className="hr"),
#                 html.B("Per-Office Analytics"),
#                 dcc.Dropdown(id="rep-office", options=office_options, placeholder="Select office", className="dash-dropdown"),
#                 html.Div(id="rep-office-kpis", style={"marginTop":"8px"}),
#                 html.Div(className="hr"),
#                 html.B("Per-Employee Analytics"),
#                 dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#                 html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
#                 html.Div(className="hr"),
#                 html.B("Add Remark for Employee"),
#                 dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#                 dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input", style={"height":"80px"}),
#                 html.Button("Add Remark", id="rep-add-remark", className="btn"),
#                 html.Div(id="rep-remark-msg", className="muted", style={"marginTop":"6px"})
#             ])

#         # OM scope
#         emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#         office_assets = s.query(Asset).filter(
#             ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#             ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#         ).all()
#         office_count = len(office_assets)
#         office_cost = sum(a.price * a.quantity for a in office_assets)
#         emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).filter(Employee.office_id == user.office_id)]

#         return html.Div([
#             html.Div(className="kpi", children=[html.Div("Assets in my office", className="label"), html.Div(office_count, className="value")]),
#             html.Div(className="kpi", children=[html.Div("Total cost for my office", className="label"), html.Div(f"${office_cost:,.2f}", className="value")]),
#             html.Div(className="hr"),
#             html.B("Per-Employee Analytics"),
#             dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#             html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
#             html.Div(className="hr"),
#             html.B("Add Remark for Employee"),
#             dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
#             dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input"),
#             html.Button("Add Remark", id="rep-add-remark", className="btn"),
#             html.Div(id="rep-remark-msg", className="muted", style={"marginTop":"6px"})
#         ])

# @app.callback(Output("rep-office-kpis","children"), Input("rep-office","value"), prevent_initial_call=True)
# @login_required(Role.GM)
# def per_office_kpis(office_id):
#     if not office_id:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == office_id)]
#         assets = s.query(Asset).filter(
#             ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == office_id)) |
#             ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#         ).all()
#         count = len(assets)
#         pending = sum(1 for a in assets if not a.returned)
#         cost = sum(a.price * a.quantity for a in assets)
#     return html.Ul([
#         html.Li(f"Assets in office: {count}"),
#         html.Li(f"Pending returns: {pending}"),
#         html.Li(f"Total cost: ${cost:,.2f}")
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
#         office = s.get(Office, user.office_id) if user.office_id else None
#         return html.Div([
#             html.Div([
#                 html.Div(f"User: {user.username}"),
#                 html.Div(f"Role: {role_name(user.role.value)}"),
#                 html.Div(f"Employee ID: {emp.id if emp else '—'}"),
#                 html.Div(f"Office ID: {office.id if office else '—'}"),
#                 html.Div(f"Office Name: {office.name if office else '—'}"),
#             ], style={"marginBottom":"8px"}),
#             dcc.Input(id="profile-emp-name", placeholder="Employee name", value=(emp.name if emp else ""), className="input"),
#             dcc.Input(id="profile-phone", placeholder="Phone number", value=getattr(emp, "phone", "") if emp else "", className="input"),
#             html.Button("Save Profile", id="btn-save-profile", n_clicks=0, type="button", className="btn"),
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



# -----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# app.py
from sqlalchemy import text
import os, datetime, base64
from functools import wraps
from urllib.parse import quote

import dash
from dash import Dash, html, dcc, Input, Output, State, dash_table, ctx
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
_safe_add_column("requests", "price FLOAT")
_safe_add_column("requests", "bill_path VARCHAR")
_safe_add_column("requests", "fulfilled_asset_id INTEGER")

UPLOAD_FOLDER = os.environ.get("RMS_UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize DB
if not os.path.exists("rms.db"):
    init_db(seed=True)
else:
    init_db(seed=False)

# ---------- Dash ----------
app = Dash(__name__, suppress_callback_exceptions=True, serve_locally=False)
server = app.server
server.secret_key = os.environ.get("RMS_SECRET", "dev-secret-key")

# Pretty HTML shell + theme
app.index_string = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>RMS</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
  {%metas%}{%favicon%}{%css%}
  <style>
    :root{
      --bg:#f7f8fb; --card:#ffffff; --text:#131824; --muted:#6b7280;
      --primary:#6366f1; --primary-600:#5458ee; --danger:#ef4444; --border:#e5e7eb;
      --radius:12px; --shadow:0 6px 18px rgba(17,24,39,.06);
    }
    html,body{height:100%;}
    body{background:var(--bg); font-family:'Inter',system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,'Helvetica Neue',Arial; color:var(--text); line-height:1.35; padding:24px;}
    nav a{ color:var(--primary); text-decoration:none; font-weight:600; }
    nav a:hover{ text-decoration:underline; }
    nav{ background:var(--card); padding:10px 14px; border:1px solid var(--border);
         border-radius:var(--radius); box-shadow:var(--shadow); margin-bottom:16px;}
    h2,h3,h4{ margin:8px 0 12px 0; }
    .card{ background:var(--card); border:1px solid var(--border); border-radius:var(--radius);
           box-shadow:var(--shadow); padding:16px; margin:10px 0;}
    .btn{ background:var(--primary); color:white; border:none; padding:8px 14px;
          border-radius:10px; font-weight:600; cursor:pointer; transition:.15s transform ease, .15s background ease;
          margin-right:8px; margin-top:6px;}
    .btn:hover{ background:var(--primary-600); transform:translateY(-1px); }
    .btn-outline{ background:transparent; color:var(--primary); border:1px solid var(--primary); }
    .btn-danger{ background:var(--danger); }
    .input, .dash-dropdown, textarea{ padding:8px 10px; border:1px solid var(--border); border-radius:10px;
       background:white; outline:none; width:100%; max-width:560px; margin-right:8px; margin-bottom:8px;}
    .two-col{ display:grid; grid-template-columns:1fr 1fr; gap:16px; }
    .kpi{ display:inline-block; min-width:210px; padding:14px 16px; margin-right:10px;
          background:linear-gradient(180deg, #fff, #fbfbff); border:1px solid var(--border);
          border-radius:14px; box-shadow:var(--shadow); }
    .kpi .label{ color:#6b7280; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.06em;}
    .kpi .value{ font-size:22px; font-weight:700; margin-top:4px;}
    .hr{ height:1px; background:var(--border); margin:16px 0;}
    .muted{ color:#6b7280; }
    .stack{ display:flex; flex-wrap:wrap; gap:8px; align-items:center;}
  </style>
</head>
<body>
  {%app_entry%}
  <footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
"""

# ---------- Helpers ----------
def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    with SessionLocal() as s:
        u = s.get(User, uid)
        if not u:
            return None
        if u.office_id:
            _ = s.get(Office, u.office_id)
        return u

def _employee_for_user(user, s):
    if not user or not user.office_id:
        return None
    emp = s.query(Employee).filter(
        Employee.office_id == user.office_id,
        Employee.username == user.username
    ).first()
    if emp:
        return emp
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
    items = []
    if user.role == Role.EMP:
        items = [
            dcc.Link("Dashboard", href="/"), html.Span(" | "),
            dcc.Link("My Assets", href="/assets"), html.Span(" | "),
            dcc.Link("Requests", href="/requests"), html.Span(" | "),
            dcc.Link("My Profile", href="/profile"), html.Span(" | "),
        ]
    else:
        items = [
            dcc.Link("Dashboard", href="/"), html.Span(" | "),
            dcc.Link("Assets", href="/assets"), html.Span(" | "),
            dcc.Link("Requests", href="/requests"), html.Span(" | "),
            dcc.Link("Reports", href="/reports"), html.Span(" | "),
        ]
        if user.role == Role.GM:
            items.extend([dcc.Link("Admin", href="/admin"), html.Span(" | ")])
        else:
            items.extend([dcc.Link("Employees", href="/employees"), html.Span(" | ")])
    items.append(dcc.Link("Logout", href="/logout"))
    return html.Nav(items)

def login_layout():
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H2("Resource Management System — Login"),
            dcc.Input(id="login-username", placeholder="Username", className="input"),
            dcc.Input(id="login-password", type="password", placeholder="Password", className="input"),
            html.Button("Login", id="login-btn", className="btn"),
            html.Div(id="login-msg", style={"color": "crimson", "marginTop": "8px"}),
            html.Div(className="muted", children="Default demo users: admin/admin, om_east/om_east, alice/alice")
        ])
    ])

def dashboard_layout():
    user = current_user()
    if not user:
        return login_layout()
    scope = "Company-wide" if user.role == Role.GM else "Your office"
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3(f"Dashboard — {role_name(user.role.value)}"),
            html.Div(className="muted", children=scope),
            html.Div(id="dashboard-cards", className="pad-top")
        ])
    ])

def _uploader_component(id_):
    return dcc.Upload(
        id=id_,
        children=html.Button("Upload Bill / Drag & Drop", className="btn btn-outline"),
        multiple=False
    )

def assets_layout():
    user = current_user()
    if not user:
        return login_layout()
    header = "My Assets" if user.role == Role.EMP else "Assets"
    button_label = "Add to My Profile" if user.role == Role.EMP else "Add Asset"
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3(header),
            _uploader_component("upload-bill"),
            html.Div(className="two-col", children=[
                dcc.Input(id="asset-name", placeholder="Asset name *", className="input"),
                dcc.Input(id="asset-price", placeholder="Price *", type="number", className="input"),
                dcc.Input(id="asset-qty", placeholder="Quantity *", type="number", value=1, className="input"),
            ]),
            dcc.RadioItems(
                id="alloc-type",
                options=[
                    {"label":"Global / Unallocated", "value": AllocationType.UNALLOCATED.value},
                    {"label":"Allocate to Office", "value": AllocationType.OFFICE.value},
                    {"label":"Allocate to Employee", "value": AllocationType.EMPLOYEE.value},
                ],
                value=AllocationType.UNALLOCATED.value,
                labelStyle={"display":"block", "margin":"6px 0"}
            ),
            dcc.Dropdown(id="alloc-target", placeholder="Choose office/employee (if applicable)", className="dash-dropdown"),
            html.Button(button_label, id="add-asset-btn", className="btn"),
            html.Div(id="asset-add-msg", style={"color":"crimson", "marginTop":"6px"}),
            dcc.ConfirmDialog(id="asset-dialog"),
        ]),
        html.Div(className="card", children=[
            html.H4(f"{header} Table"),
            html.Div(id="assets-table")
        ])
    ])

def requests_layout():
    user = current_user()
    if not user:
        return login_layout()
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("Requests"),
            html.Div(id="request-form"),
            dcc.ConfirmDialog(id="req-dialog")
        ]),
        html.Div(className="card", children=[
            html.H4("Open Requests"),
            html.Div(id="requests-table")
        ])
    ])

def reports_layout():
    user = current_user()
    if not user:
        return login_layout()
    if user.role == Role.EMP:
        return html.Div([navbar(), html.Div(className="card", children="Reports are not available for Employees.")])
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("Reports"),
            html.Div(id="reports-content"),
            dcc.ConfirmDialog(id="reports-dialog"),
            html.Div(id="reports-msg", style={"color":"crimson", "marginTop":"6px"}),
        ])
    ])

def employees_layout():
    user = current_user()
    if not user:
        return login_layout()
    if user.role != Role.OM:
        return html.Div([navbar(), html.Div(className="card", children="Only Office Managers can manage employees.")])
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("Manage Employees"),
            html.Div(className="two-col", children=[
                dcc.Input(id="emp-new-name", placeholder="Employee name *", className="input"),
                dcc.Input(id="emp-new-phone", placeholder="Phone", className="input"),
                dcc.Input(id="emp-new-username", placeholder="Username *", className="input"),
                dcc.Input(id="emp-new-password", placeholder="Password *", className="input"),
            ]),
            html.Button("Add Employee", id="emp-add-btn", className="btn"),
            dcc.ConfirmDialog(id="emp-dialog"),
            html.Div(id="emp-add-msg", style={"color":"crimson", "marginTop":"6px"})
        ]),
        html.Div(className="card", children=[
            html.H4("Employees in My Office"),
            html.Div(id="emp-table")
        ])
    ])

def admin_layout():
    user = current_user()
    if not user or user.role != Role.GM:
        return html.Div([navbar(), html.Div(className="card", children="Admins only.")])
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("Admin — Offices & Managers"),
            html.H4("Create Office"),
            dcc.Input(id="new-office-name", placeholder="Office name *", className="input"),
            html.Button("Add Office", id="btn-add-office", className="btn"),
            html.Div(id="msg-add-office", className="muted", style={"marginTop":"6px"}),
            html.Div(className="hr"),
            html.H4("Create Office Manager"),
            html.Div(className="two-col", children=[
                dcc.Dropdown(id="om-office", placeholder="Select office", className="dash-dropdown"),
                dcc.Input(id="om-username", placeholder="Username *", className="input"),
                dcc.Input(id="om-password", placeholder="Password *", className="input"),
            ]),
            html.Button("Create OM", id="btn-create-om", className="btn"),
            dcc.ConfirmDialog(id="admin-dialog"),
            html.Div(id="msg-create-om", className="muted", style={"marginTop":"6px"}),
            html.Div(className="hr"),
            html.H4("Reset OM Password"),
            html.Div(className="two-col", children=[
                dcc.Dropdown(id="om-existing", placeholder="Select OM user", className="dash-dropdown"),
                dcc.Input(id="om-new-pass", placeholder="New password *", className="input"),
            ]),
            html.Button("Reset Password", id="btn-om-reset", className="btn btn-outline"),
            html.Div(id="msg-om-reset", className="muted", style={"marginTop":"6px"}),
        ])
    ])

def profile_layout():
    user = current_user()
    if not user:
        return login_layout()
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("My Profile"),
            html.Div(id="profile-form"),
            dcc.ConfirmDialog(id="profile-dialog"),
            html.Div(id="profile-msg", style={"color":"crimson", "marginTop":"6px"}),
        ])
    ])

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
    if path == "/admin":
        return admin_layout()
    if path == "/profile":
        return profile_layout()
    return html.Div([navbar(), html.Div(className="card", children=html.H3("Not Found"))])

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
            count = s.query(Asset).count()
            pending = s.query(Asset).filter(Asset.returned == False).count()  # noqa: E712
        else:
            emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
            assets = s.query(Asset).filter(
                ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
                ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
            ).all()
            total_assets_cost = sum(a.price * a.quantity for a in assets)
            count = len(assets)
            pending = sum(1 for a in assets if not a.returned)
        return html.Div(className="stack", children=[
            html.Div(className="kpi", children=[html.Div("Assets", className="label"), html.Div(count, className="value")]),
            html.Div(className="kpi", children=[html.Div("Pending Returns", className="label"), html.Div(pending, className="value")]),
            html.Div(className="kpi", children=[html.Div("Total Cost", className="label"), html.Div(f"${total_assets_cost:,.2f}", className="value")]),
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
    State("alloc-type", "value"), State("alloc-target", "value"),
    prevent_initial_call=True
)
def add_asset(n, name, price, qty, contents, filename, alloc_type, alloc_target):
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
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
        saved_path = os.path.join(UPLOAD_FOLDER, fname)
        with open(saved_path, "wb") as f:
            f.write(decoded)

    with SessionLocal() as s:
        a_type = AllocationType.UNALLOCATED
        a_id = None
        if alloc_type == AllocationType.OFFICE.value:
            a_type = AllocationType.OFFICE
            a_id = int(alloc_target) if alloc_target else (current_user().office_id or None)
        elif alloc_type == AllocationType.EMPLOYEE.value:
            a_type = AllocationType.EMPLOYEE
            if alloc_target:
                a_id = int(alloc_target)
            elif current_user().role == Role.EMP:
                emp = _employee_for_user(current_user(), s)
                a_id = emp.id if emp else None

        s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
                    allocation_type=a_type, allocation_id=a_id))
        s.commit()
    return ("", render_assets_table(), "Asset added.", True, "", "", 1, None)

def _bill_link_path(path):
    if not path:
        return ""
    base = os.path.basename(path)
    return f"[{base}](/uploads/{quote(base)})"

def _bill_link_asset(a):
    return _bill_link_path(a.bill_path)

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
            rows = [{"asset_no": i, "name": a.name, "price": a.price, "qty": a.quantity, "bill": _bill_link_asset(a)}
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
        rows = [{"id":a.id,"name":a.name,"price":a.price,"qty":a.quantity,"bill":_bill_link_asset(a),
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

# Dynamic options for allocation target
@app.callback(
    Output("alloc-target", "options"),
    Output("alloc-target", "value"),
    Output("alloc-target", "placeholder"),
    Input("alloc-type", "value"),
    Input("url", "pathname"),
)
def update_alloc_options(alloc_type, _):
    user = current_user()
    if not user:
        raise PreventUpdate
    with SessionLocal() as s:
        if alloc_type == AllocationType.OFFICE.value:
            if user.role == Role.GM:
                offices = s.query(Office).order_by(Office.name).all()
                opts = [{"label": o.name, "value": o.id} for o in offices]
                return opts, None, "Select office"
            else:
                return [{"label": "My Office", "value": user.office_id}], user.office_id, "My Office"
        elif alloc_type == AllocationType.EMPLOYEE.value:
            q = s.query(Employee)
            if user.role == Role.OM:
                q = q.filter(Employee.office_id == user.office_id)
            elif user.role == Role.EMP:
                emp = _employee_for_user(user, s)
                if emp:
                    return [{"label": emp.name, "value": emp.id}], emp.id, "Myself"
            emps = q.order_by(Employee.name).all()
            return [{"label": e.name, "value": e.id} for e in emps], None, "Select employee"
        return [], None, "No target (Global/Unallocated)"

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
                html.B("Create Request"),
                dcc.Dropdown(id="req-employee", options=options, value=(emp.id if emp else None), className="dash-dropdown", disabled=True),
                html.Div(className="two-col", children=[
                    dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
                    dcc.Input(id="req-qty", type="number", value=1, className="input"),
                    dcc.Input(id="req-price", placeholder="Price", type="number", className="input"),
                ]),
                _uploader_component("req-bill"),
                html.Button("Submit Request", id="req-submit", className="btn"),
                html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
            ])
        employees = s.query(Employee).filter(Employee.office_id == user.office_id).all() \
            if user.role == Role.OM else s.query(Employee).all()
        options = [{"label": e.name, "value": e.id} for e in employees]
        return html.Div([
            html.B("Create Request"),
            dcc.Dropdown(id="req-employee", options=options, placeholder="Employee", className="dash-dropdown"),
            html.Div(className="two-col", children=[
                dcc.Input(id="req-asset-name", placeholder="Asset name", className="input"),
                dcc.Input(id="req-qty", type="number", value=1, className="input"),
                dcc.Input(id="req-price", placeholder="Price", type="number", className="input"),
            ]),
            _uploader_component("req-bill"),
            html.Button("Submit Request", id="req-submit", className="btn"),
            html.Div(id="req-msg", style={"marginTop":"6px","color":"crimson"})
        ])

@app.callback(
    Output("req-msg", "children"),
    Output("requests-table", "children", allow_duplicate=True),
    Output("req-dialog","message"),
    Output("req-dialog","displayed"),
    Output("req-asset-name","value"),
    Output("req-qty","value"),
    Output("req-price","value"),
    Output("req-bill","contents"),
    Input("req-submit", "n_clicks"),
    State("req-employee", "value"),
    State("req-asset-name", "value"),
    State("req-qty", "value"),
    State("req-price", "value"),
    State("req-bill", "contents"),
    State("req-bill", "filename"),
    prevent_initial_call=True
)
def create_request(n, emp_id, asset_name, qty, price, contents, filename):
    user = current_user()
    if not user:
        raise PreventUpdate
    if not n or n < 1:
        raise PreventUpdate
    asset_name = (asset_name or "").strip()
    try: qty = int(qty or 0)
    except Exception: qty = 0
    try: price_val = float(price or 0)
    except Exception: price_val = 0.0
    if not asset_name:
        return "Please enter an asset name.", render_requests_table(), "", False, asset_name, qty, price, contents
    if qty < 1:
        return "Quantity must be at least 1.", render_requests_table(), "", False, asset_name, qty, price, contents

    saved_path = None
    if contents and filename:
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
        saved_path = os.path.join(UPLOAD_FOLDER, fname)
        with open(saved_path, "wb") as f:
            f.write(decoded)

    with SessionLocal() as s:
        if user.role == Role.EMP and not emp_id:
            emp = _employee_for_user(user, s)
            emp_id = emp.id if emp else None
        if not emp_id:
            return "Select an employee.", render_requests_table(), "", False, asset_name, qty, price, contents
        emp = s.get(Employee, emp_id)
        if not emp:
            return "Invalid employee.", render_requests_table(), "", False, asset_name, qty, price, contents
        if user.role == Role.OM and emp.office_id != user.office_id:
            return "You can only submit requests for your office.", render_requests_table(), "", False, asset_name, qty, price, contents
        s.add(Request(employee_id=emp.id, office_id=emp.office_id, asset_name=asset_name,
                      quantity=qty, price=price_val, bill_path=saved_path))
        s.commit()
    return "", render_requests_table(), "Request submitted.", True, "", 1, "", None

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
        data = [{
            "id":r.id,"employee_id":r.employee_id,"office_id":r.office_id,"asset":r.asset_name,
            "qty":r.quantity,"price": r.price, "status":r.status.value,"remark":r.remark or "",
            "bill": _bill_link_path(r.bill_path),
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M")
        } for r in rows]
    cols = [
        {"name":"id","id":"id"},
        {"name":"employee_id","id":"employee_id"},
        {"name":"office_id","id":"office_id"},
        {"name":"asset","id":"asset"},
        {"name":"qty","id":"qty"},
        {"name":"price","id":"price"},
        {"name":"status","id":"status"},
        {"name":"remark","id":"remark"},
        {"name":"bill","id":"bill","presentation":"markdown"},
        {"name":"created_at","id":"created_at"},
    ]

    user = current_user()
    controls = html.Div(className="stack", children=[
        dcc.Textarea(id="mgr-remark", placeholder="Remark…", className="input", style={"height":"60px", "width":"420px"}),
        html.Button("Approve", id="btn-approve", className="btn"),
        html.Button("Reject", id="btn-reject", className="btn btn-danger"),
        html.Button("Mark Return Pending", id="btn-return-pending", className="btn btn-outline"),
        html.Button("Mark Returned", id="btn-returned", className="btn btn-outline"),
    ]) if user and user.role in (Role.GM, Role.OM) else html.Div()

    table = dash_table.DataTable(data=data, columns=cols, id="req-table",
                                 row_selectable="single", page_size=10, style_table={"overflowX":"auto"})
    return html.Div([table, html.Div(id="req-action-msg", style={"marginTop":"8px"}), controls])

# ---------- Helper to find a matching asset ----------
def _find_matching_asset(session, req):
    q = session.query(Asset).filter(
        Asset.allocation_type == AllocationType.EMPLOYEE,
        Asset.allocation_id == req.employee_id,
        Asset.name == req.asset_name,
        Asset.price == (req.price or 0),
        Asset.quantity == (req.quantity or 1),
    )
    if req.bill_path:
        q = q.filter(Asset.bill_path == req.bill_path)
    return q.first()

# ---------- Action buttons with hard guards & popups ----------
@app.callback(
    Output("req-action-msg", "children", allow_duplicate=True),
    Output("requests-table", "children", allow_duplicate=True),
    Output("req-dialog", "message", allow_duplicate=True),
    Output("req-dialog", "displayed", allow_duplicate=True),
    Input("btn-approve", "n_clicks"),
    Input("btn-reject", "n_clicks"),
    Input("btn-return-pending", "n_clicks"),
    Input("btn-returned", "n_clicks"),
    State("req-table", "selected_rows"), State("req-table", "data"),
    State("mgr-remark", "value"),
    prevent_initial_call=True
)
def handle_request_action(n1, n2, n3, n4, selected, data, remark):
    user = current_user()
    if not user or user.role not in (Role.GM, Role.OM):
        return "Not allowed.", render_requests_table(), "", False
    if not selected:
        return "Select a request first.", render_requests_table(), "", False

    mapping = {
        "btn-approve": RequestStatus.APPROVED,
        "btn-reject": RequestStatus.REJECTED,
        "btn-return-pending": RequestStatus.RETURN_PENDING,
        "btn-returned": RequestStatus.RETURNED,
    }
    trig = ctx.triggered_id
    status = mapping.get(trig, None)
    if status is None:
        raise PreventUpdate

    req_id = data[selected[0]]["id"]

    with SessionLocal() as s:
        r = s.get(Request, req_id)
        if not r:
            return "Request not found.", render_requests_table(), "", False
        if user.role == Role.OM and r.office_id != user.office_id:
            return "You can only update requests in your office.", render_requests_table(), "", False

        # hard guards ---------------------------------------------------------
        if trig == "btn-approve":
            if r.status == RequestStatus.APPROVED:
                return "No change.", render_requests_table(), "This request is already approved.", True
            if r.status == RequestStatus.RETURNED:
                return "No change.", render_requests_table(), "This request is already marked Returned.", True

        if trig == "btn-reject":
            if r.status == RequestStatus.APPROVED:
                return "No change.", render_requests_table(), "Approved requests can't be rejected.", True
            if r.status == RequestStatus.RETURNED:
                return "No change.", render_requests_table(), "Returned requests can't be rejected.", True

        if trig == "btn-return-pending" and r.status != RequestStatus.APPROVED:
            return "No change.", render_requests_table(), "Only approved requests can be marked return pending.", True

        # apply remark
        if remark:
            r.remark = remark

        matched_asset = _find_matching_asset(s, r)

        if status == RequestStatus.APPROVED:
            if not matched_asset:
                a = Asset(
                    name=r.asset_name,
                    price=float(r.price or 0),
                    quantity=int(r.quantity or 1),
                    bill_path=r.bill_path,
                    allocation_type=AllocationType.EMPLOYEE,
                    allocation_id=r.employee_id
                )
                s.add(a)
            r.status = RequestStatus.APPROVED

        elif status == RequestStatus.RETURN_PENDING:
            # do NOT delete asset; only change status
            r.status = RequestStatus.RETURN_PENDING

        elif status == RequestStatus.RETURNED:
            if matched_asset:
                matched_asset.returned = True
            r.status = RequestStatus.RETURNED

        elif status == RequestStatus.REJECTED:
            # allowed only if not previously approved (guarded above)
            if matched_asset:
                s.delete(matched_asset)
            r.status = RequestStatus.REJECTED

        s.commit()

    return f"Status updated to {status.value}.", render_requests_table(), "", False

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
    return dash_table.DataTable(data=data, columns=cols, page_size=10, style_table={"overflowX":"auto"})

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

# ---------- GM Admin ----------
@app.callback(Output("om-office","options"), Output("om-existing","options"), Input("url","pathname"))
@login_required(Role.GM)
def load_admin_dropdowns(_):
    with SessionLocal() as s:
        offices = s.query(Office).order_by(Office.name).all()
        oms = s.query(User).filter(User.role == Role.OM).order_by(User.username).all()
        return (
            [{"label": o.name, "value": o.id} for o in offices],
            [{"label": u.username, "value": u.id} for u in oms]
        )

@app.callback(
    Output("msg-add-office","children"),
    Output("om-office","options", allow_duplicate=True),
    Input("btn-add-office","n_clicks"),
    State("new-office-name","value"),
    prevent_initial_call=True
)
@login_required(Role.GM)
def add_office(n, office_name):
    name = (office_name or "").strip()
    with SessionLocal() as s:
        if not name:
            offices = s.query(Office).order_by(Office.name).all()
            return "Office name is required.", [{"label": o.name, "value": o.id} for o in offices]
        if s.query(Office).filter(Office.name.ilike(name)).first():
            offices = s.query(Office).order_by(Office.name).all()
            return "Office already exists.", [{"label": o.name, "value": o.id} for o in offices]
        s.add(Office(name=name))
        s.commit()
        offices = s.query(Office).order_by(Office.name).all()
    return "Office created.", [{"label": o.name, "value": o.id} for o in offices]

@app.callback(
    Output("msg-create-om","children"),
    Output("admin-dialog","message"),
    Output("admin-dialog","displayed"),
    Output("om-username","value"),
    Output("om-password","value"),
    State("om-office","value"),
    State("om-username","value"),
    State("om-password","value"),
    Input("btn-create-om","n_clicks"),
    prevent_initial_call=True
)
@login_required(Role.GM)
def create_om(office_id, uname, pwd, n):
    uname = (uname or "").strip()
    pwd = (pwd or "")
    if not office_id or not uname or not pwd:
        return ("All fields are required.", "", False, uname, pwd)
    with SessionLocal() as s:
        if not s.get(Office, office_id):
            return ("Invalid office.", "", False, uname, pwd)
        if s.query(User).filter(User.username == uname).first():
            return ("Username already exists.", "", False, uname, pwd)
        s.add(User(username=uname, password_hash=generate_password_hash(pwd), role=Role.OM, office_id=office_id))
        s.commit()
    return ("OM created.", "Office Manager created successfully.", True, "", "")

@app.callback(
    Output("msg-om-reset","children"),
    State("om-existing","value"),
    State("om-new-pass","value"),
    Input("btn-om-reset","n_clicks"),
    prevent_initial_call=True
)
@login_required(Role.GM)
def reset_om_password(om_id, new_pass, n):
    new_pass = (new_pass or "").strip()
    if not om_id or not new_pass:
        return "Select an OM and enter a new password."
    with SessionLocal() as s:
        u = s.get(User, om_id)
        if not u or u.role != Role.OM:
            return "Invalid OM selected."
        u.password_hash = generate_password_hash(new_pass)
        s.commit()
    return "Password reset."

# ---------- Reports (GM + OM) ----------
@app.callback(Output("reports-content","children"), Input("url","pathname"))
def render_reports(_):
    user = current_user()
    if not user or user.role == Role.EMP:
        raise PreventUpdate

    with SessionLocal() as s:
        if user.role == Role.GM:
            all_assets = s.query(Asset).all()
            company_count = len(all_assets)
            company_cost = sum(a.price * a.quantity for a in all_assets)
            company_pending = sum(1 for a in all_assets if not a.returned)

            offices = s.query(Office).order_by(Office.name).all()
            office_options = [{"label": o.name, "value": o.id} for o in offices]
            emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).order_by(Employee.name)]

            return html.Div([
                html.Div(className="stack", children=[
                    html.Div(className="kpi", children=[html.Div("Company assets", className="label"), html.Div(company_count, className="value")]),
                    html.Div(className="kpi", children=[html.Div("Company total cost", className="label"), html.Div(f\"${company_cost:,.2f}\", className="value")]),
                    html.Div(className="kpi", children=[html.Div("Company pending returns", className="label"), html.Div(company_pending, className="value")]),
                ]),
                html.Div(className="hr"),
                html.B("Per-Office Analytics"),
                dcc.Dropdown(id="rep-office", options=office_options, placeholder="Select office", className="dash-dropdown"),
                html.Div(id="rep-office-kpis", style={"marginTop":"8px"}),
                html.Div(className="hr"),
                html.B("Per-Employee Analytics"),
                dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
                html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
                html.Div(className="hr"),
                html.B("Add Remark for Employee"),
                dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
                dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input", style={"height":"80px"}),
                html.Button("Add Remark", id="rep-add-remark", className="btn"),
                html.Div(id="rep-remark-msg", className="muted", style={"marginTop":"6px"})
            ])

        # OM scope
        emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
        office_assets = s.query(Asset).filter(
            ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
            ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
        ).all()
        office_count = len(office_assets)
        office_cost = sum(a.price * a.quantity for a in office_assets)
        emp_options = [{"label": e.name, "value": e.id} for e in s.query(Employee).filter(Employee.office_id == user.office_id)]

        return html.Div([
            html.Div(className="kpi", children=[html.Div("Assets in my office", className="label"), html.Div(office_count, className="value")]),
            html.Div(className="kpi", children=[html.Div("Total cost for my office", className="label"), html.Div(f\"${office_cost:,.2f}\", className="value")]),
            html.Div(className="hr"),
            html.B("Per-Employee Analytics"),
            dcc.Dropdown(id="rep-emp", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
            html.Div(id="rep-emp-kpis", style={"marginTop":"8px"}),
            html.Div(className="hr"),
            html.B("Add Remark for Employee"),
            dcc.Dropdown(id="rep-emp-remark", options=emp_options, placeholder="Select employee", className="dash-dropdown"),
            dcc.Textarea(id="rep-remark-text", placeholder="Write a remark...", className="input"),
            html.Button("Add Remark", id="rep-add-remark", className="btn"),
            html.Div(id="rep-remark-msg", className="muted", style={"marginTop":"6px"})
        ])

@app.callback(Output("rep-office-kpis","children"), Input("rep-office","value"), prevent_initial_call=True)
@login_required(Role.GM)
def per_office_kpis(office_id):
    if not office_id:
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
    return html.Ul([
        html.Li(f"Assets in office: {count}"),
        html.Li(f"Pending returns: {pending}"),
        html.Li(f"Total cost: ${cost:,.2f}")
    ])

@app.callback(Output("rep-emp-kpis","children"), Input("rep-emp","value"), prevent_initial_call=True)
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
        html.Li(f"Pending resources (not returned): {pending}"),
        html.Li(f"Total asset cost for this employee: ${cost:,.2f}")
    ])

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
        s.add(Remark(author_user_id=user.id, target_type="EMPLOYEE", target_id=int(emp_id), content=(textv or "").strip()))
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
        office = s.get(Office, user.office_id) if user.office_id else None
        return html.Div([
            html.Div([
                html.Div(f"User: {user.username}"),
                html.Div(f"Role: {role_name(user.role.value)}"),
                html.Div(f"Employee ID: {emp.id if emp else '—'}"),
                html.Div(f"Office ID: {office.id if office else '—'}"),
                html.Div(f"Office Name: {office.name if office else '—'}"),
            ], style={"marginBottom":"8px"}),
            dcc.Input(id="profile-emp-name", placeholder="Employee name", value=(emp.name if emp else ""), className="input"),
            dcc.Input(id="profile-phone", placeholder="Phone number", value=getattr(emp, "phone", "") if emp else "", className="input"),
            html.Button("Save Profile", id="btn-save-profile", n_clicks=0, type="button", className="btn"),
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

