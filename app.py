
# # ---------------------------------------------------------------------------
# # app.py (RMS — pastel blue / glassmorphism, with requested fixes)
# # ---------------------------------------------------------------------------
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

# # Pretty HTML shell + theme (unchanged pastel blue / glassmorphism)
# app.index_string = """
# <!DOCTYPE html>
# <html>
# <head>
#   <meta charset="UTF-8">
#   <title>RMS - Resource Management System</title>
#   <link rel="preconnect" href="https://fonts.googleapis.com">
#   <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
#   <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
#   {%metas%}{%favicon%}{%css%}
#   <style>
#     :root{
#       --bg:#f3f4f6; --bg-alt:#ffffff;
#       --card:#ffffff; --card-hover:#fafbfc;
#       --text:#0f172a; --text-secondary:#475569; --muted:#64748b;
#       --primary:#3b82f6; --primary-hover:#2563eb; --primary-light:#dbeafe;
#       --success:#10b981; --success-light:#d1fae5;
#       --warning:#f59e0b; --warning-light:#fef3c7;
#       --danger:#ef4444; --danger-hover:#dc2626; --danger-light:#fee2e2;
#       --border:#e2e8f0; --border-focus:#3b82f6;
#       --radius:10px; --radius-lg:14px;
#       --shadow:0 1px 3px rgba(15,23,42,.08), 0 1px 2px rgba(15,23,42,.06);
#       --shadow-lg:0 10px 25px -5px rgba(15,23,42,.1), 0 8px 10px -6px rgba(15,23,42,.04);
#       --shadow-xl:0 20px 30px -10px rgba(15,23,42,.12);
#     }
    
#     * { box-sizing: border-box; }
    
#     html, body { 
#       height: 100%; 
#       margin: 0; 
#       padding: 0;
#     }
    
#     body { 
#       background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
#       font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Ubuntu, 'Helvetica Neue', Arial, sans-serif;
#       color: var(--text);
#       line-height: 1.6;
#       padding: 20px;
#       min-height: 100vh;
#     }
    
#     /* Typography */
#     h2, h3, h4 { 
#       margin: 0 0 20px 0; 
#       font-weight: 700;
#       color: var(--text);
#       letter-spacing: -0.02em;
#     }
#     h2 { font-size: 28px; }
#     h3 { font-size: 24px; }
#     h4 { 
#       font-size: 18px; 
#       font-weight: 600;
#       margin-bottom: 16px;
#     }
    
#     /* Enhanced Navigation */
#     nav { 
#       background: var(--card);
#       padding: 16px 24px;
#       border: 1px solid var(--border);
#       border-radius: var(--radius-lg);
#       box-shadow: var(--shadow-lg);
#       margin-bottom: 24px;
#       display: flex;
#       align-items: center;
#       flex-wrap: wrap;
#       gap: 8px;
#     }
    
#     nav a { 
#       color: var(--text-secondary);
#       text-decoration: none;
#       font-weight: 600;
#       font-size: 14px;
#       padding: 8px 16px;
#       border-radius: var(--radius);
#       transition: all 0.2s ease;
#       position: relative;
#     }
    
#     nav a:hover { 
#       color: var(--primary);
#       background: var(--primary-light);
#       transform: translateY(-1px);
#     }
    
#     nav span { 
#       color: var(--border);
#       margin: 0 4px;
#     }
    
#     /* Enhanced Cards */
#     .card { 
#       background: var(--card);
#       border: 1px solid var(--border);
#       border-radius: var(--radius-lg);
#       box-shadow: var(--shadow-lg);
#       padding: 28px;
#       margin: 16px 0;
#       transition: all 0.3s ease;
#     }
    
#     .card:hover {
#       box-shadow: var(--shadow-xl);
#     }
    
#     /* Enhanced Buttons */
#     .btn { 
#       background: var(--primary);
#       color: white;
#       border: none;
#       padding: 11px 20px;
#       border-radius: var(--radius);
#       font-weight: 600;
#       font-size: 14px;
#       cursor: pointer;
#       transition: all 0.2s ease;
#       margin-right: 10px;
#       margin-top: 8px;
#       box-shadow: 0 1px 2px rgba(59,130,246,.2);
#       display: inline-flex;
#       align-items: center;
#       gap: 6px;
#     }
    
#     .btn:hover { 
#       background: var(--primary-hover);
#       transform: translateY(-2px);
#       box-shadow: 0 4px 8px rgba(59,130,246,.3);
#     }
    
#     .btn:active {
#       transform: translateY(0);
#     }
    
#     .btn-outline { 
#       background: transparent;
#       color: var(--primary);
#       border: 2px solid var(--primary);
#       box-shadow: none;
#     }
    
#     .btn-outline:hover {
#       background: var(--primary-light);
#       box-shadow: 0 2px 4px rgba(59,130,246,.15);
#     }
    
#     .btn-danger { 
#       background: var(--danger);
#       box-shadow: 0 1px 2px rgba(239,68,68,.2);
#     }
    
#     .btn-danger:hover {
#       background: var(--danger-hover);
#       box-shadow: 0 4px 8px rgba(239,68,68,.3);
#     }
    
#     /* Enhanced Inputs */
#     .input, .dash-dropdown, textarea { 
#       padding: 11px 14px;
#       border: 2px solid var(--border);
#       border-radius: var(--radius);
#       background: var(--bg-alt);
#       outline: none;
#       width: 100%;
#       max-width: 560px;
#       margin-right: 10px;
#       margin-bottom: 12px;
#       font-size: 14px;
#       font-family: inherit;
#       transition: all 0.2s ease;
#       color: var(--text);
#     }
    
#     .input:focus, textarea:focus {
#       border-color: var(--border-focus);
#       box-shadow: 0 0 0 3px rgba(59,130,246,.1);
#     }
    
#     .input::placeholder, textarea::placeholder {
#       color: var(--muted);
#     }
    
#     textarea {
#       resize: vertical;
#       min-height: 80px;
#     }
    
#     /* Form Layouts */
#     .two-col { 
#       display: grid;
#       grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
#       gap: 16px;
#       margin-bottom: 16px;
#     }
    
#     .form-group {
#       margin-bottom: 20px;
#     }
    
#     .form-label {
#       display: block;
#       font-weight: 600;
#       font-size: 13px;
#       color: var(--text-secondary);
#       margin-bottom: 8px;
#       text-transform: uppercase;
#       letter-spacing: 0.05em;
#     }
    
#     /* Enhanced KPI Cards */
#     .kpi { 
#       display: inline-block;
#       min-width: 240px;
#       padding: 20px 24px;
#       margin: 8px;
#       background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
#       border: 1px solid var(--border);
#       border-radius: var(--radius-lg);
#       box-shadow: var(--shadow);
#       transition: all 0.3s ease;
#       position: relative;
#       overflow: hidden;
#     }
    
#     .kpi::before {
#       content: '';
#       position: absolute;
#       top: 0;
#       left: 0;
#       width: 4px;
#       height: 100%;
#       background: var(--primary);
#       opacity: 0;
#       transition: opacity 0.3s ease;
#     }
    
#     .kpi:hover {
#       transform: translateY(-4px);
#       box-shadow: var(--shadow-lg);
#     }
    
#     .kpi:hover::before {
#       opacity: 1;
#     }
    
#     .kpi .label { 
#       color: var(--muted);
#       font-size: 11px;
#       font-weight: 700;
#       text-transform: uppercase;
#       letter-spacing: 0.08em;
#       margin-bottom: 8px;
#     }
    
#     .kpi .value { 
#       font-size: 28px;
#       font-weight: 800;
#       margin-top: 6px;
#       color: var(--text);
#       line-height: 1.2;
#     }
    
#     /* Utilities */
#     .hr { 
#       height: 1px;
#       background: linear-gradient(to right, transparent, var(--border), transparent);
#       margin: 28px 0;
#       border: none;
#     }
    
#     .muted { 
#       color: var(--muted);
#       font-size: 14px;
#     }
    
#     .stack { 
#       display: flex;
#       flex-wrap: wrap;
#       gap: 12px;
#       align-items: center;
#       margin: 16px 0;
#     }
    
#     .pad-top {
#       padding-top: 16px;
#     }
    
#     /* Status Badges */
#     .badge {
#       display: inline-block;
#       padding: 4px 12px;
#       border-radius: 12px;
#       font-size: 12px;
#       font-weight: 600;
#       text-transform: uppercase;
#       letter-spacing: 0.05em;
#     }
    
#     .badge-success {
#       background: var(--success-light);
#       color: var(--success);
#     }
    
#     .badge-warning {
#       background: var(--warning-light);
#       color: var(--warning);
#     }
    
#     .badge-danger {
#       background: var(--danger-light);
#       color: var(--danger);
#     }
    
#     .badge-info {
#       background: var(--primary-light);
#       color: var(--primary);
#     }
    
#     /* Message Styles */
#     .message {
#       padding: 12px 16px;
#       border-radius: var(--radius);
#       margin: 12px 0;
#       font-size: 14px;
#       font-weight: 500;
#     }
    
#     .message-error {
#       background: var(--danger-light);
#       color: var(--danger);
#       border-left: 4px solid var(--danger);
#     }
    
#     .message-success {
#       background: var(--success-light);
#       color: var(--success);
#       border-left: 4px solid var(--success);
#     }
    
#     .message-info {
#       background: var(--primary-light);
#       color: var(--primary);
#       border-left: 4px solid var(--primary);
#     }
    
#     .message-warning {
#       background: var(--warning-light);
#       color: var(--warning);
#       border-left: 4px solid var(--warning);
#     }
    
#     /* Table Enhancements */
#     .dash-table-container {
#       margin-top: 16px;
#       border-radius: var(--radius);
#       overflow: hidden;
#       border: 1px solid var(--border);
#     }
    
#     .dash-spreadsheet {
#       border: none !important;
#     }
    
#     .dash-spreadsheet-container {
#       overflow-x: auto;
#     }
    
#     /* Radio Items Enhancement */
#     input[type="radio"] {
#       margin-right: 8px;
#       accent-color: var(--primary);
#     }
    
#     /* Upload Component */
#     .dash-upload {
#       display: inline-block;
#       margin-bottom: 16px;
#     }
    
#     /* Dropdown Enhancement */
#     .Select-control {
#       border-color: var(--border) !important;
#       border-width: 2px !important;
#       border-radius: var(--radius) !important;
#     }
    
#     .Select-control:hover {
#       border-color: var(--primary) !important;
#     }
    
#     .is-focused .Select-control {
#       border-color: var(--border-focus) !important;
#       box-shadow: 0 0 0 3px rgba(59,130,246,.1) !important;
#     }
    
#     /* Responsive Design */
#     @media (max-width: 768px) {
#       body {
#         padding: 12px;
#       }
      
#       .card {
#         padding: 20px;
#       }
      
#       nav {
#         padding: 12px 16px;
#       }
      
#       .two-col {
#         grid-template-columns: 1fr;
#       }
      
#       .kpi {
#         min-width: 100%;
#         margin: 8px 0;
#       }
      
#       h2 { font-size: 24px; }
#       h3 { font-size: 20px; }
#     }
    
#     /* Loading State */
#     ._dash-loading {
#       opacity: 0.7;
#     }
    
#     /* Scrollbar Styling */
#     ::-webkit-scrollbar {
#       width: 8px;
#       height: 8px;
#     }
    
#     ::-webkit-scrollbar-track {
#       background: var(--bg);
#     }
    
#     ::-webkit-scrollbar-thumb {
#       background: var(--border);
#       border-radius: 4px;
#     }
    
#     ::-webkit-scrollbar-thumb:hover {
#       background: var(--muted);
#     }
    
#     /* Tooltip styling for better UX */
#     [title] {
#       position: relative;
#       cursor: help;
#     }
    
#     /* Focus indicators for accessibility */
#     a:focus, button:focus, input:focus, select:focus, textarea:focus {
#       outline: 2px solid var(--primary);
#       outline-offset: 2px;
#     }
    
#     /* Better link hover states */
#     a {
#       transition: all 0.2s ease;
#     }
    
#     /* Smooth animations */
#     * {
#       transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
#     }
    
#     /* Help text styling */
#     .help-text {
#       font-size: 12px;
#       color: var(--muted);
#       margin-top: 4px;
#       font-style: italic;
#     }
    
#     /* Empty state styling */
#     .empty-state {
#       text-align: center;
#       padding: 60px 20px;
#       color: var(--muted);
#     }
    
#     .empty-state h3 {
#       color: var(--text-secondary);
#       margin-bottom: 12px;
#     }
    
#     /* Active navigation indicator */
#     nav a.active {
#       background: var(--primary-light);
#       color: var(--primary);
#       font-weight: 700;
#     }
    
#     /* Better table styling */
#     .dash-table-container table {
#       border-collapse: separate;
#       border-spacing: 0;
#     }
    
#     /* Loading animation */
#     @keyframes pulse {
#       0%, 100% { opacity: 1; }
#       50% { opacity: 0.5; }
#     }
    
#     ._dash-loading-callback {
#       animation: pulse 1.5s ease-in-out infinite;
#     }
    
#     /* Success/Error state animations */
#     .message {
#       animation: slideInDown 0.3s ease-out;
#     }
    
#     @keyframes slideInDown {
#       from {
#         opacity: 0;
#         transform: translateY(-10px);
#       }
#       to {
#         opacity: 1;
#         transform: translateY(0);
#       }
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
    
#     # Logo section
#     logo = html.Div([
#         html.Img(
#             src="https://starlab-public.s3.us-east-1.amazonaws.com/starlab_images/transparent-slc-rgb.png",
#             style={
#                 "height": "36px",
#                 "marginRight": "16px",
#                 "objectFit": "contain",
#                 "cursor": "pointer"
#             },
#             title="Starlab Capital - Resource Management System"
#         ),
#         html.Div([
#             html.Div("RMS", style={"fontSize": "16px", "fontWeight": "700", "color": "var(--text)", "lineHeight": "1"}),
#             html.Div("Resource Mgmt", style={"fontSize": "9px", "color": "var(--muted)", "lineHeight": "1", "marginTop": "2px"})
#         ], style={"display": "flex", "flexDirection": "column", "marginRight": "24px"})
#     ], style={"display": "flex", "alignItems": "center", "marginRight": "auto"})
    
#     # Build navigation items based on role
#     nav_items = []
#     if user.role == Role.EMP:
#         nav_items = [
#             dcc.Link("📊 Dashboard", href="/", title="View your overview"),
#             dcc.Link("💼 My Assets", href="/assets", title="View and manage your assets"),
#             dcc.Link("📝 Requests", href="/requests", title="Submit and track resource requests"),
#             dcc.Link("👤 My Profile", href="/profile", title="Update your profile information"),
#         ]
#     else:
#         nav_items = [
#             dcc.Link("📊 Dashboard", href="/", title="View system overview"),
#             dcc.Link("💼 Assets", href="/assets", title="Manage all assets"),
#             dcc.Link("📝 Requests", href="/requests", title="Review and approve requests"),
#             dcc.Link("📈 Reports", href="/reports", title="View analytics and reports"),
#         ]
#         if user.role == Role.GM:
#             nav_items.append(dcc.Link("⚙️ Admin", href="/admin", title="System administration"))
#         else:
#             nav_items.append(dcc.Link("👥 Employees", href="/employees", title="Manage your team"))
    
#     # Add user info and logout
#     user_info = html.Div([
#         html.Span(f"{user.username}", style={"color": "var(--text-secondary)", "fontWeight": "600", "marginRight": "12px"}),
#         html.Span(f"({role_name(user.role.value)})", style={"color": "var(--muted)", "fontSize": "13px", "marginRight": "16px"}),
#         dcc.Link("🚪 Logout", href="/logout", style={"color": "var(--danger)"}, title="Sign out of your account")
#     ], style={"marginLeft": "auto", "display": "flex", "alignItems": "center"})
    
#     return html.Nav([logo] + nav_items + [user_info], style={"display": "flex", "alignItems": "center", "gap": "4px"})

# def login_layout():
#     return html.Div([
#         navbar(),
#         html.Div(style={"maxWidth": "480px", "margin": "60px auto"}, children=[
#         html.Div(className="card", children=[
#                 html.Div(style={"textAlign": "center", "marginBottom": "32px"}, children=[
#                     html.Img(
#                         src="https://starlab-public.s3.us-east-1.amazonaws.com/starlab_images/transparent-slc-rgb.png",
#                         style={
#                             "height": "80px",
#                             "marginBottom": "24px",
#                             "objectFit": "contain"
#                         }
#                     ),
#                     html.H2("🔐 Welcome to RMS", style={"marginBottom": "8px"}),
#                     html.Div("Resource Management System", className="muted", style={"marginBottom": "4px"}),
#                     html.Div("Powered by Starlab Capital", style={"fontSize": "12px", "color": "var(--muted)", "fontWeight": "500"})
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("Username", className="form-label"),
#                     dcc.Input(id="login-username", placeholder="Enter your username", className="input", style={"maxWidth": "100%"}, n_submit=0),
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("Password", className="form-label"),
#                     dcc.Input(id="login-password", type="password", placeholder="Enter your password", className="input", style={"maxWidth": "100%"}, n_submit=0),
#                 ]),
#                 html.Button("🔓 Login", id="login-btn", className="btn", style={"width": "100%", "marginTop": "8px"}),
#                 html.Div(id="login-msg", style={"marginTop": "16px"}),
#             ])
#         ])
#     ])

# def dashboard_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     scope = "Company-wide metrics" if user.role == Role.GM else "Your office metrics"
#     welcome_emoji = "👨‍💼" if user.role == Role.GM else ("👔" if user.role == Role.OM else "👤")
    
#     # Role-specific quick guide
#     if user.role == Role.EMP:
#         quick_guide = html.Div(style={"background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "color": "white", "padding": "20px", "borderRadius": "var(--radius-lg)", "marginBottom": "20px"}, children=[
#             html.H4("🎯 Quick Start Guide", style={"color": "white", "marginBottom": "12px"}),
#             html.Div([
#                 html.Div("✓ View your assets in the 'My Assets' section", style={"marginBottom": "8px"}),
#                 html.Div("✓ Submit new resource requests in 'Requests'", style={"marginBottom": "8px"}),
#                 html.Div("✓ Update your profile information in 'My Profile'", style={"marginBottom": "8px"}),
#                 html.Div("💡 Tip: You can press Enter to submit forms!", style={"marginTop": "12px", "fontStyle": "italic", "opacity": "0.9"})
#             ], style={"fontSize": "14px"})
#         ])
#     elif user.role == Role.OM:
#         quick_guide = html.Div(style={"background": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", "color": "white", "padding": "20px", "borderRadius": "var(--radius-lg)", "marginBottom": "20px"}, children=[
#             html.H4("🎯 Manager Quick Guide", style={"color": "white", "marginBottom": "12px"}),
#             html.Div([
#                 html.Div("✓ Manage office assets in 'Assets' section", style={"marginBottom": "8px"}),
#                 html.Div("✓ Review and approve requests in 'Requests'", style={"marginBottom": "8px"}),
#                 html.Div("✓ Add new employees in 'Employees'", style={"marginBottom": "8px"}),
#                 html.Div("✓ View analytics and reports in 'Reports'", style={"marginBottom": "8px"}),
#             ], style={"fontSize": "14px"})
#         ])
#     else:  # GM
#         quick_guide = html.Div(style={"background": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)", "color": "white", "padding": "20px", "borderRadius": "var(--radius-lg)", "marginBottom": "20px"}, children=[
#             html.H4("🎯 Admin Quick Guide", style={"color": "white", "marginBottom": "12px"}),
#             html.Div([
#                 html.Div("✓ Create offices and managers in 'Admin'", style={"marginBottom": "8px"}),
#                 html.Div("✓ Manage all assets company-wide in 'Assets'", style={"marginBottom": "8px"}),
#                 html.Div("✓ Review all requests in 'Requests'", style={"marginBottom": "8px"}),
#                 html.Div("✓ View company analytics in 'Reports'", style={"marginBottom": "8px"}),
#             ], style={"fontSize": "14px"})
#         ])
    
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.Div(style={"marginBottom": "24px"}, children=[
#                 html.H3(f"{welcome_emoji} Welcome, {user.username}!", style={"marginBottom": "8px"}),
#                 html.Div(className="muted", children=[
#                     html.Span(f"{role_name(user.role.value)} • ", style={"fontWeight": "600"}),
#                     html.Span(scope)
#                 ]),
#             ]),
#             quick_guide,
#             html.Div(id="dashboard-cards", className="pad-top")
#         ])
#     ])

# def _uploader_component(id_):
#     return dcc.Upload(
#         id=id_,
#         children=html.Button("📎 Upload Bill / Drag & Drop", className="btn btn-outline"),
#         multiple=False,
#         style={
#             "width": "100%",
#             "borderRadius": "var(--radius)",
#             "border": "2px dashed var(--border)",
#             "padding": "20px",
#             "textAlign": "center",
#             "cursor": "pointer",
#             "transition": "all 0.2s ease",
#             "background": "var(--bg-alt)"
#         }
#     )

# def _alloc_radio_for_user(user):
#     """
#     Build allocation radio options per role:
#       - GM: UNALLOCATED + OFFICE + EMPLOYEE (as before)
#       - OM: OFFICE + EMPLOYEE (NO Unallocated)  <-- req #1
#       - EMP: EMPLOYEE only                       <-- req #4
#     Also returns a sensible default value per role.
#     """
#     if user.role == Role.GM:
#         options = [
#             {"label":"Global / Unallocated", "value": AllocationType.UNALLOCATED.value},
#             {"label":"Allocate to Office", "value": AllocationType.OFFICE.value},
#             {"label":"Allocate to Employee", "value": AllocationType.EMPLOYEE.value},
#         ]
#         default_val = AllocationType.UNALLOCATED.value
#     elif user.role == Role.OM:
#         options = [
#             {"label":"Allocate to Office", "value": AllocationType.OFFICE.value},
#             {"label":"Allocate to Employee", "value": AllocationType.EMPLOYEE.value},
#         ]
#         default_val = AllocationType.OFFICE.value
#     else:  # EMP
#         options = [
#             {"label":"Allocate to Me", "value": AllocationType.EMPLOYEE.value},
#         ]
#         default_val = AllocationType.EMPLOYEE.value
#     return options, default_val

# def assets_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     header = "💼 My Assets" if user.role == Role.EMP else "💼 Assets Management"
#     button_label = "➕ Add to My Profile" if user.role == Role.EMP else "➕ Add Asset"
#     radio_options, radio_default = _alloc_radio_for_user(user)
    
#     # Help text based on role
#     if user.role == Role.EMP:
#         help_text = "Add assets to your profile (e.g., laptop, desk, monitor). This helps track what resources you're using."
#     else:
#         help_text = "Add new assets to the system and assign them to offices or employees. All fields marked with * are required."
    
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3(header, style={"marginBottom": "8px"}),
#             html.Div(help_text, className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
#             html.Div(className="form-group", children=[
#                 html.Label("📄 Upload Bill (Optional)", className="form-label"),
#                 html.Div("You can upload a receipt or invoice for this asset", className="muted", style={"fontSize": "12px", "marginBottom": "8px"}),
#             _uploader_component("upload-bill"),
#             ]),
#             html.Div(className="two-col", children=[
#                 html.Div(className="form-group", children=[
#                     html.Label("Asset Name *", className="form-label"),
#                     dcc.Input(id="asset-name", placeholder="e.g., Laptop, Desk, Monitor", className="input", style={"maxWidth": "100%"}),
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("Price *", className="form-label"),
#                     dcc.Input(id="asset-price", placeholder="0.00", type="number", className="input", style={"maxWidth": "100%"}),
#                 ]),
#             ]),
#             html.Div(className="form-group", children=[
#                 html.Label("Quantity *", className="form-label"),
#                 dcc.Input(id="asset-qty", placeholder="1", type="number", value=1, className="input", style={"maxWidth": "200px"}),
#             ]),
#             html.Div(className="form-group", children=[
#                 html.Label("Allocation Type", className="form-label"),
#             dcc.RadioItems(
#                 id="alloc-type",
#                 options=radio_options,
#                 value=radio_default,
#                     labelStyle={"display":"block", "margin":"10px 0", "fontWeight": "500", "color": "var(--text-secondary)"}
#                 ),
#             ]),
#             html.Div(className="form-group", children=[
#                 html.Label("Allocation Target", className="form-label"),
#                 dcc.Dropdown(id="alloc-target", placeholder="Choose office/employee (if applicable)", className="dash-dropdown", style={"maxWidth": "100%"}),
#             ]),
#             html.Button(button_label, id="add-asset-btn", className="btn"),
#             html.Div(id="asset-add-msg", style={"marginTop":"16px"}),
#             dcc.ConfirmDialog(id="asset-dialog"),
#         ]),
#         html.Div(className="card", children=[
#             html.Div(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "16px"}, children=[
#                 html.H4(f"{header} List", style={"margin": "0"}),
#                 html.Div(className="badge badge-info", children="Live Data")
#             ]),
#             html.Div(id="assets-table")
#         ])
#     ])

# def requests_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
    
#     # Role-specific help text
#     if user.role == Role.EMP:
#         help_text = "Submit a request for new resources you need. Your manager will review and approve it."
#     else:
#         help_text = "Create requests on behalf of employees or review pending requests below."
    
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("📝 New Request", style={"marginBottom": "8px"}),
#             html.Div(help_text, className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
#             html.Div(id="request-form"),
#             dcc.ConfirmDialog(id="req-dialog")
#         ]),
#         html.Div(className="card", children=[
#             html.Div(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "8px"}, children=[
#                 html.H4("📋 All Requests", style={"margin": "0"}),
#                 html.Div(className="badge badge-warning", children="Pending Review")
#             ]),
#             html.Div("Track the status of your requests. Managers can select a request and take action below.", className="muted", style={"marginBottom": "16px", "fontSize": "13px"}) if user.role != Role.EMP else html.Div("Track the status of all your submitted requests here.", className="muted", style={"marginBottom": "16px", "fontSize": "13px"}),
#             html.Div(id="requests-table")
#         ])
#     ])

# def reports_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role == Role.EMP:
#         return html.Div([navbar(), html.Div(className="card", children=[
#             html.Div(style={"textAlign": "center", "padding": "40px"}, children=[
#                 html.H3("📊 Reports Unavailable"),
#                 html.Div("Reports are only available for Managers.", className="muted")
#             ])
#         ])])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("📈 Analytics & Reports", style={"marginBottom": "8px"}),
#             html.Div("View comprehensive analytics, track resource allocation, and add remarks for employees.", className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
#             html.Div(id="reports-content"),
#             dcc.ConfirmDialog(id="reports-dialog"),
#             html.Div(id="reports-msg", style={"marginTop":"16px"}),
#         ])
#     ])

# def employees_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     if user.role != Role.OM:
#         return html.Div([navbar(), html.Div(className="card", children=[
#             html.Div(style={"textAlign": "center", "padding": "40px"}, children=[
#                 html.H3("⚠️ Access Restricted"),
#                 html.Div("Only Office Managers can manage employees.", className="muted")
#             ])
#         ])])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("👥 Add New Employee", style={"marginBottom": "8px"}),
#             html.Div("Add employees to your office. They'll be able to login with the credentials you provide here.", className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
#             html.Div(className="two-col", children=[
#                 html.Div(className="form-group", children=[
#                     html.Label("Employee Name *", className="form-label"),
#                     dcc.Input(id="emp-new-name", placeholder="Full name", className="input", style={"maxWidth": "100%"}),
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("Phone Number", className="form-label"),
#                     dcc.Input(id="emp-new-phone", placeholder="(optional)", className="input", style={"maxWidth": "100%"}),
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("Username *", className="form-label"),
#                     dcc.Input(id="emp-new-username", placeholder="Login username", className="input", style={"maxWidth": "100%"}),
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("Password *", className="form-label"),
#                     dcc.Input(id="emp-new-password", type="password", placeholder="Initial password", className="input", style={"maxWidth": "100%"}),
#                 ]),
#             ]),
#             html.Button("➕ Add Employee", id="emp-add-btn", className="btn"),
#             dcc.ConfirmDialog(id="emp-dialog"),
#             html.Div(id="emp-add-msg", style={"marginTop":"16px"})
#         ]),
#         html.Div(className="card", children=[
#             html.Div(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "16px"}, children=[
#                 html.H4("📋 Employees in My Office", style={"margin": "0"}),
#                 html.Div(className="badge badge-info", children="Active Staff")
#             ]),
#             html.Div(id="emp-table")
#         ])
#     ])

# def admin_layout():
#     user = current_user()
#     if not user or user.role != Role.GM:
#         return html.Div([navbar(), html.Div(className="card", children=[
#             html.Div(style={"textAlign": "center", "padding": "40px"}, children=[
#                 html.H3("🔒 Admin Access Only"),
#                 html.Div("This section is restricted to General Managers.", className="muted")
#             ])
#         ])])
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("⚙️ Admin Panel", style={"marginBottom": "8px"}),
#             html.Div("System administration area. Set up your organization structure by creating offices and assigning managers.", className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
            
#             html.H4("🏢 Create Office", style={"marginTop": "24px", "marginBottom": "8px"}),
#             html.Div("First, create offices (branches/departments) for your organization.", className="muted", style={"marginBottom": "12px", "fontSize": "13px"}),
#             html.Div(className="form-group", children=[
#                 html.Label("Office Name *", className="form-label"),
#                 dcc.Input(id="new-office-name", placeholder="e.g., East Branch, West Branch", className="input"),
#             ]),
#             html.Button("➕ Add Office", id="btn-add-office", className="btn"),
#             html.Div(id="msg-add-office", style={"marginTop":"12px"}),
            
#             html.Div(className="hr"),
            
#             html.H4("👔 Create Office Manager", style={"marginBottom": "8px"}),
#             html.Div("Assign a manager to each office. They will manage employees and assets for their office.", className="muted", style={"marginBottom": "12px", "fontSize": "13px"}),
#             html.Div(className="two-col", children=[
#                 html.Div(className="form-group", children=[
#                     html.Label("Select Office *", className="form-label"),
#                     dcc.Dropdown(id="om-office", placeholder="Choose office", className="dash-dropdown", style={"maxWidth": "100%"}),
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("Username *", className="form-label"),
#                     dcc.Input(id="om-username", placeholder="Login username", className="input", style={"maxWidth": "100%"}),
#                 ]),
#             ]),
#             html.Div(className="form-group", children=[
#                 html.Label("Password *", className="form-label"),
#                 dcc.Input(id="om-password", type="password", placeholder="Initial password", className="input"),
#             ]),
#             html.Button("➕ Create OM", id="btn-create-om", className="btn"),
#             dcc.ConfirmDialog(id="admin-dialog"),
#             html.Div(id="msg-create-om", style={"marginTop":"12px"}),
            
#             html.Div(className="hr"),
            
#             html.H4("🔑 Reset OM Password", style={"marginBottom": "8px"}),
#             html.Div("Reset an Office Manager's password if they've forgotten it.", className="muted", style={"marginBottom": "12px", "fontSize": "13px"}),
#             html.Div(className="two-col", children=[
#                 html.Div(className="form-group", children=[
#                     html.Label("Select OM User *", className="form-label"),
#                     dcc.Dropdown(id="om-existing", placeholder="Choose OM", className="dash-dropdown", style={"maxWidth": "100%"}),
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("New Password *", className="form-label"),
#                     dcc.Input(id="om-new-pass", type="password", placeholder="Enter new password", className="input", style={"maxWidth": "100%"}),
#                 ]),
#             ]),
#             html.Button("🔄 Reset Password", id="btn-om-reset", className="btn btn-outline"),
#             html.Div(id="msg-om-reset", style={"marginTop":"12px"}),
#         ])
#     ])

# def profile_layout():
#     user = current_user()
#     if not user:
#         return login_layout()
#     return html.Div([
#         navbar(),
#         html.Div(className="card", children=[
#             html.H3("👤 My Profile", style={"marginBottom": "8px"}),
#             html.Div("Update your personal information. Your manager can also leave remarks here for you.", className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
#             html.Div(id="profile-form"),
#             # Kept component but we'll NEVER display it (req #5)
#             dcc.ConfirmDialog(id="profile-dialog"),
#             html.Div(id="profile-msg", style={"marginTop":"16px"}),
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
# @app.callback(
#     Output("login-msg", "children"), 
#     Input("login-btn", "n_clicks"),
#     Input("login-username", "n_submit"),
#     Input("login-password", "n_submit"),
#     State("login-username", "value"), 
#     State("login-password", "value"),
#     prevent_initial_call=True
# )
# def do_login(n_clicks, n_submit_user, n_submit_pass, username, password):
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
#             return html.Div("❌ Invalid credentials. Please try again.", className="message message-error")
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
#         return (html.Div("❌ Asset name is required.", className="message message-error"), render_assets_table(), "", False, name, price, qty, contents)
#     if price_val <= 0:
#         return (html.Div("❌ Price must be greater than 0.", className="message message-error"), render_assets_table(), "", False, name, price, qty, contents)
#     if qty_val < 1:
#         return (html.Div("❌ Quantity must be at least 1.", className="message message-error"), render_assets_table(), "", False, name, price, qty, contents)

#     saved_path = None
#     if contents and filename:
#         _, content_string = contents.split(',')
#         decoded = base64.b64decode(content_string)
#         fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
#         saved_path = os.path.join(UPLOAD_FOLDER, fname)
#         with open(saved_path, "wb") as f:
#             f.write(decoded)

#     with SessionLocal() as s:
#         # Enforce allocation rules by role (req #1 + #4)
#         if user.role == Role.GM:
#             a_type = AllocationType(alloc_type)
#             a_id = None
#             if a_type == AllocationType.OFFICE:
#                 a_id = int(alloc_target) if alloc_target else None
#             elif a_type == AllocationType.EMPLOYEE:
#                 a_id = int(alloc_target) if alloc_target else None
#         elif user.role == Role.OM:
#             # OM cannot create UNALLOCATED
#             if alloc_type == AllocationType.EMPLOYEE.value:
#                 a_type = AllocationType.EMPLOYEE
#                 a_id = int(alloc_target) if alloc_target else None
#             else:
#                 a_type = AllocationType.OFFICE
#                 a_id = user.office_id
#         else:  # EMP can only allocate to self
#             a_type = AllocationType.EMPLOYEE
#             emp = _employee_for_user(user, s)
#             a_id = emp.id if emp else None

#         s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
#                     allocation_type=a_type, allocation_id=a_id))
#         s.commit()
#     return (html.Div("✅ Asset added successfully!", className="message message-success"), render_assets_table(), "Asset added.", True, "", "", 1, None)

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
#         # Employee: only their own assets
#         if user.role == Role.EMP:
#             emp = _employee_for_user(user, s)
#             assets = [] if not emp else s.query(Asset).filter(
#                 Asset.allocation_type == AllocationType.EMPLOYEE,
#                 Asset.allocation_id == emp.id
#             ).all()

#         # Office Manager: only office assets + assets of employees in their office
#         elif user.role == Role.OM:
#             emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
#             assets = s.query(Asset).filter(
#                 ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
#                 ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
#             ).all()

#         # GM: all assets
#         else:
#             assets = s.query(Asset).all()

#         rows = [{
#             "id": a.id,
#             "name": a.name,
#             "price": a.price,
#             "qty": a.quantity,
#             "bill": _bill_link_asset(a),
#             "allocation": a.allocation_type.value,
#             "allocation_id": a.allocation_id
#         } for a in assets]

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
#         # For OM/EMP we never show unallocated (req #1 & #4)
#         return [], None, "No target"

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
#                 html.Div(className="form-group", children=[
#                     html.Label("Employee (Auto-selected)", className="form-label"),
#                     dcc.Dropdown(id="req-employee", options=options, value=(emp.id if emp else None), className="dash-dropdown", disabled=True, style={"maxWidth": "100%"}),
#                 ]),
#                 html.Div(className="two-col", children=[
#                     html.Div(className="form-group", children=[
#                         html.Label("Asset Name *", className="form-label"),
#                         dcc.Input(id="req-asset-name", placeholder="What asset do you need?", className="input", style={"maxWidth": "100%"}),
#                     ]),
#                     html.Div(className="form-group", children=[
#                         html.Label("Quantity *", className="form-label"),
#                         dcc.Input(id="req-qty", type="number", value=1, className="input", style={"maxWidth": "100%"}),
#                     ]),
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("Price (Optional)", className="form-label"),
#                     dcc.Input(id="req-price", placeholder="Estimated price", type="number", className="input"),
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("📄 Upload Bill (Optional)", className="form-label"),
#                     _uploader_component("req-bill"),
#                 ]),
#                 html.Button("✅ Submit Request", id="req-submit", className="btn"),
#                 html.Div(id="req-msg", style={"marginTop":"16px"})
#             ])
#         employees = s.query(Employee).filter(Employee.office_id == user.office_id).all() \
#             if user.role == Role.OM else s.query(Employee).all()
#         options = [{"label": e.name, "value": e.id} for e in employees]
#         return html.Div([
#             html.Div(className="form-group", children=[
#                 html.Label("Select Employee *", className="form-label"),
#                 dcc.Dropdown(id="req-employee", options=options, placeholder="Choose employee", className="dash-dropdown", style={"maxWidth": "100%"}),
#             ]),
#             html.Div(className="two-col", children=[
#                 html.Div(className="form-group", children=[
#                     html.Label("Asset Name *", className="form-label"),
#                     dcc.Input(id="req-asset-name", placeholder="What asset is needed?", className="input", style={"maxWidth": "100%"}),
#                 ]),
#                 html.Div(className="form-group", children=[
#                     html.Label("Quantity *", className="form-label"),
#                     dcc.Input(id="req-qty", type="number", value=1, className="input", style={"maxWidth": "100%"}),
#                 ]),
#             ]),
#             html.Div(className="form-group", children=[
#                 html.Label("Price (Optional)", className="form-label"),
#                 dcc.Input(id="req-price", placeholder="Estimated price", type="number", className="input"),
#             ]),
#             html.Div(className="form-group", children=[
#                 html.Label("📄 Upload Bill (Optional)", className="form-label"),
#                 _uploader_component("req-bill"),
#             ]),
#             html.Button("✅ Submit Request", id="req-submit", className="btn"),
#             html.Div(id="req-msg", style={"marginTop":"16px"})
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
#         return html.Div("❌ Please enter an asset name.", className="message message-error"), render_requests_table(), "", False, asset_name, qty, price, contents
#     if qty < 1:
#         return html.Div("❌ Quantity must be at least 1.", className="message message-error"), render_requests_table(), "", False, asset_name, qty, price, contents

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
#             return html.Div("❌ Select an employee.", className="message message-error"), render_requests_table(), "", False, asset_name, qty, price, contents
#         emp = s.get(Employee, emp_id)
#         if not emp:
#             return html.Div("❌ Invalid employee.", className="message message-error"), render_requests_table(), "", False, asset_name, qty, price, contents
#         if user.role == Role.OM and emp.office_id != user.office_id:
#             return html.Div("❌ You can only submit requests for your office.", className="message message-error"), render_requests_table(), "", False, asset_name, qty, price, contents
#         s.add(Request(employee_id=emp.id, office_id=emp.office_id, asset_name=asset_name,
#                       quantity=qty, price=price_val, bill_path=saved_path))
#         s.commit()
#     return html.Div("✅ Request submitted successfully!", className="message message-success"), render_requests_table(), "Request submitted.", True, "", 1, "", None

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
#     controls = html.Div(style={"marginTop": "24px", "padding": "20px", "background": "var(--bg-alt)", "borderRadius": "var(--radius)", "border": "1px solid var(--border)"}, children=[
#         html.Label("📝 Manager Actions", className="form-label", style={"marginBottom": "12px"}),
#         html.Div(className="form-group", children=[
#             html.Label("Add Remark (Optional)", className="form-label"),
#             dcc.Textarea(id="mgr-remark", placeholder="Add a note about this request...", className="input", style={"height":"80px", "width":"100%", "maxWidth": "100%"}),
#         ]),
#         html.Div(className="stack", children=[
#             html.Button("✅ Approve", id="btn-approve", className="btn"),
#             html.Button("❌ Reject", id="btn-reject", className="btn btn-danger"),
#             html.Button("⏳ Return Pending", id="btn-return-pending", className="btn btn-outline"),
#             html.Button("✔️ Returned", id="btn-returned", className="btn btn-outline"),
#         ])
#     ]) if user and user.role in (Role.GM, Role.OM) else html.Div()

#     table = dash_table.DataTable(data=data, columns=cols, id="req-table",
#                                  row_selectable="single", page_size=10, style_table={"overflowX":"auto"})
#     return html.Div([table, html.Div(id="req-action-msg", style={"marginTop":"8px"}), controls])

# # ---------- Helper to find a matching asset ----------
# def _find_matching_asset(session, req):
#     q = session.query(Asset).filter(
#         Asset.allocation_type == AllocationType.EMPLOYEE,
#         Asset.allocation_id == req.employee_id,
#         Asset.name == req.asset_name,
#         Asset.price == (req.price or 0),
#         Asset.quantity == (req.quantity or 1),
#     )
#     if req.bill_path:
#         q = q.filter(Asset.bill_path == req.bill_path)
#     return q.first()

# # ---------- Action buttons with hard guards & popups ----------
# @app.callback(
#     Output("req-action-msg", "children", allow_duplicate=True),
#     Output("requests-table", "children", allow_duplicate=True),
#     Output("req-dialog", "message", allow_duplicate=True),
#     Output("req-dialog", "displayed", allow_duplicate=True),
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
#         return html.Div("❌ Not allowed.", className="message message-error"), render_requests_table(), "", False
#     if not selected:
#         return html.Div("⚠️ Select a request first.", className="message message-info"), render_requests_table(), "", False

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
#             return html.Div("❌ Request not found.", className="message message-error"), render_requests_table(), "", False
#         if user.role == Role.OM and r.office_id != user.office_id:
#             return html.Div("❌ You can only update requests in your office.", className="message message-error"), render_requests_table(), "", False

#         # hard guards ---------------------------------------------------------
#         if trig == "btn-approve":
#             if r.status == RequestStatus.APPROVED:
#                 return html.Div("ℹ️ No change needed.", className="message message-info"), render_requests_table(), "This request is already approved.", True
#             if r.status == RequestStatus.RETURNED:
#                 return html.Div("ℹ️ No change needed.", className="message message-info"), render_requests_table(), "This request is already marked Returned.", True

#         if trig == "btn-reject":
#             if r.status == RequestStatus.APPROVED:
#                 return html.Div("⚠️ Cannot reject.", className="message message-warning"), render_requests_table(), "Approved requests can't be rejected.", True
#             if r.status == RequestStatus.RETURNED:
#                 return html.Div("⚠️ Cannot reject.", className="message message-warning"), render_requests_table(), "Returned requests can't be rejected.", True

#         if trig == "btn-return-pending" and r.status != RequestStatus.APPROVED:
#             return html.Div("⚠️ Invalid action.", className="message message-warning"), render_requests_table(), "Only approved requests can be marked return pending.", True

#         # apply remark
#         if remark:
#             r.remark = remark

#         matched_asset = _find_matching_asset(s, r)

#         if status == RequestStatus.APPROVED:
#             if not matched_asset:
#                 a = Asset(
#                     name=r.asset_name,
#                     price=float(r.price or 0),
#                     quantity=int(r.quantity or 1),
#                     bill_path=r.bill_path,
#                     allocation_type=AllocationType.EMPLOYEE,
#                     allocation_id=r.employee_id
#                 )
#                 s.add(a)
#             r.status = RequestStatus.APPROVED

#         elif status == RequestStatus.RETURN_PENDING:
#             r.status = RequestStatus.RETURN_PENDING

#         elif status == RequestStatus.RETURNED:
#             if matched_asset:
#                 matched_asset.returned = True
#             r.status = RequestStatus.RETURNED

#         elif status == RequestStatus.REJECTED:
#             if matched_asset:
#                 s.delete(matched_asset)
#             r.status = RequestStatus.REJECTED

#         s.commit()

#     return html.Div(f"✅ Status updated to {status.value}.", className="message message-success"), render_requests_table(), "", False

# # ---------- Employees (OM) ----------
# def _render_emp_table_for_om(user):
#     with SessionLocal() as s:
#         emps = s.query(Employee).filter(Employee.office_id == user.office_id).order_by(Employee.id).all()
#         data = [{"id": e.id, "name": e.name, "phone": getattr(e, "phone", ""), "office_id": e.office_id} for e in emps]
#     cols = [{"name": n, "id": n} for n in ["id", "name", "phone", "office_id"]]
#     return dash_table.DataTable(data=data, columns=cols, page_size=10, style_table={"overflowX":"auto"})

# @app.callback(Output("emp-table", "children"), Input("url", "pathname"))
# def list_employees(_):
#     user = current_user()
#     if not user or user.role != Role.OM:
#         raise PreventUpdate
#     return _render_emp_table_for_om(user)

# # NOTE: Update table immediately after adding employee (req #2)
# @app.callback(
#     Output("emp-add-msg","children"),
#     Output("emp-dialog","message"),
#     Output("emp-dialog","displayed"),
#     Output("emp-new-name","value"),
#     Output("emp-new-phone","value"),
#     Output("emp-new-username","value"),
#     Output("emp-new-password","value"),
#     Output("emp-table","children", allow_duplicate=True),
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
#         return (html.Div("❌ Name, username and password are required.", className="message message-error"), "", False, name, phone, uname, pwd, _render_emp_table_for_om(user))
#     with SessionLocal() as s:
#         if s.query(User).filter(User.username == uname).first():
#             return (html.Div("❌ Username already exists.", className="message message-error"), "", False, name, phone, uname, pwd, _render_emp_table_for_om(user))
#         emp = Employee(name=name, office_id=user.office_id, username=uname)
#         try: emp.phone = (phone or "").strip()
#         except Exception: pass
#         s.add(emp); s.flush()
#         s.add(User(username=uname, password_hash=generate_password_hash(pwd),
#                    role=Role.EMP, office_id=user.office_id))
#         s.commit()
#     # Clear fields, show dialog, and refresh table immediately
#     return (html.Div("✅ Employee created successfully!", className="message message-success"), "Employee created and login set.", True, "", "", "", "", _render_emp_table_for_om(user))

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
#             return html.Div("❌ Office name is required.", className="message message-error"), [{"label": o.name, "value": o.id} for o in offices]
#         if s.query(Office).filter(Office.name.ilike(name)).first():
#             offices = s.query(Office).order_by(Office.name).all()
#             return html.Div("❌ Office already exists.", className="message message-error"), [{"label": o.name, "value": o.id} for o in offices]
#         s.add(Office(name=name))
#         s.commit()
#         offices = s.query(Office).order_by(Office.name).all()
#     return html.Div("✅ Office created successfully!", className="message message-success"), [{"label": o.name, "value": o.id} for o in offices]

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
#         return (html.Div("❌ All fields are required.", className="message message-error"), "", False, uname, pwd)
#     with SessionLocal() as s:
#         if not s.get(Office, office_id):
#             return (html.Div("❌ Invalid office.", className="message message-error"), "", False, uname, pwd)
#         if s.query(User).filter(User.username == uname).first():
#             return (html.Div("❌ Username already exists.", className="message message-error"), "", False, uname, pwd)
#         s.add(User(username=uname, password_hash=generate_password_hash(pwd), role=Role.OM, office_id=office_id))
#         s.commit()
#     return (html.Div("✅ Office Manager created successfully!", className="message message-success"), "Office Manager created successfully.", True, "", "")

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
#         return html.Div("❌ Select an OM and enter a new password.", className="message message-error")
#     with SessionLocal() as s:
#         u = s.get(User, om_id)
#         if not u or u.role != Role.OM:
#             return html.Div("❌ Invalid OM selected.", className="message message-error")
#         u.password_hash = generate_password_hash(new_pass)
#         s.commit()
#     return html.Div("✅ Password reset successfully!", className="message message-success")

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
#         return html.Div("❌ Select an employee and enter a remark.", className="message message-error")
#     with SessionLocal() as s:
#         s.add(Remark(author_user_id=user.id, target_type="EMPLOYEE", target_id=int(emp_id), content=(textv or "").strip()))
#         s.commit()
#     return html.Div("✅ Remark added successfully!", className="message message-success")

# # ---------- Profile ----------
# @app.callback(Output("profile-form", "children"), Input("url", "pathname"))
# def load_profile(_):
#     """
#     Show employee's own info + ALL remarks addressed to that employee (req #3).
#     """
#     user = current_user()
#     if not user:
#         raise PreventUpdate
#     with SessionLocal() as s:
#         emp = _employee_for_user(user, s) if user.role == Role.EMP else None
#         office = s.get(Office, user.office_id) if user.office_id else None

#         # Gather remarks targeted to this employee (if exists)
#         remarks_list = []
#         if emp:
#             rs = s.query(Remark).filter(
#                 Remark.target_type == "EMPLOYEE",
#                 Remark.target_id == emp.id
#             ).order_by(Remark.created_at.desc()).all()
#             for r in rs:
#                 ts = getattr(r, "created_at", None)
#                 ts_str = ts.strftime("%Y-%m-%d %H:%M") if ts else ""
#                 remarks_list.append(html.Li([
#                     html.Span(f"{ts_str} — "),
#                     html.Span(r.content or "")
#                 ]))

#         remarks_block = html.Div([
#             html.Div(className="hr"),
#             html.H4("💬 Manager Remarks", style={"marginBottom": "16px"}),
#             html.Ul(remarks_list, style={"paddingLeft": "20px"}) if remarks_list else html.Div(className="muted", children="No remarks from management yet.")
#         ]) if emp else html.Div()

#         return html.Div([
#             html.Div(className="card", style={"background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "color": "white", "marginBottom": "20px"}, children=[
#                 html.Div(style={"fontSize": "18px", "fontWeight": "700", "marginBottom": "12px"}, children=f"👋 {user.username}"),
#                 html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))", "gap": "12px"}, children=[
#                     html.Div([
#                         html.Div("Role", style={"fontSize": "12px", "opacity": "0.9", "marginBottom": "4px"}),
#                         html.Div(role_name(user.role.value), style={"fontSize": "16px", "fontWeight": "600"})
#                     ]),
#                     html.Div([
#                         html.Div("Employee ID", style={"fontSize": "12px", "opacity": "0.9", "marginBottom": "4px"}),
#                         html.Div(emp.id if emp else '—', style={"fontSize": "16px", "fontWeight": "600"})
#                     ]),
#                     html.Div([
#                         html.Div("Office", style={"fontSize": "12px", "opacity": "0.9", "marginBottom": "4px"}),
#                         html.Div(office.name if office else '—', style={"fontSize": "16px", "fontWeight": "600"})
#                     ]),
#                 ])
#             ]),
#             html.Div(className="form-group", children=[
#                 html.Label("Full Name *", className="form-label"),
#                 dcc.Input(id="profile-emp-name", placeholder="Enter your full name", value=(emp.name if emp else ""), className="input"),
#             ]),
#             html.Div(className="form-group", children=[
#                 html.Label("Phone Number", className="form-label"),
#                 dcc.Input(id="profile-phone", placeholder="Enter your phone number", value=getattr(emp, "phone", "") if emp else "", className="input"),
#             ]),
#             html.Button("💾 Save Profile", id="btn-save-profile", n_clicks=0, type="button", className="btn"),
#             remarks_block
#         ])

# # No popup on visiting profile; after saving also DO NOT show popup (req #5)
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
#         return "", False, html.Div("❌ Name is required.", className="message message-error")
#     with SessionLocal() as s:
#         emp = _employee_for_user(user, s)
#         if not emp:
#             return "", False, html.Div("❌ No employee record.", className="message message-error")
#         emp.name = name
#         try: emp.phone = phone
#         except Exception: pass
#         s.commit()
#     # No modal; just a small status message
#     return "", False, html.Div("✅ Profile updated successfully!", className="message message-success")

# # ---------- Run ----------
# if __name__ == "__main__":
#     app.run(debug=True)



# # # # # ===========================================================================================================================================================================================================




# ---------------------------------------------------------------------------
# app.py (RMS — pastel blue / glassmorphism, with requested fixes)
# ---------------------------------------------------------------------------
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
_safe_add_column("offices", "location VARCHAR")
_safe_add_column("offices", "manager_id INTEGER")
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

# Pretty HTML shell + theme (unchanged pastel blue / glassmorphism)
app.index_string = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>RMS - Resource Management System</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  {%metas%}{%favicon%}{%css%}
  <style>
    :root{
      --bg:#f3f4f6; --bg-alt:#ffffff;
      --card:#ffffff; --card-hover:#fafbfc;
      --text:#0f172a; --text-secondary:#475569; --muted:#64748b;
      --primary:#3b82f6; --primary-hover:#2563eb; --primary-light:#dbeafe;
      --success:#10b981; --success-light:#d1fae5;
      --warning:#f59e0b; --warning-light:#fef3c7;
      --danger:#ef4444; --danger-hover:#dc2626; --danger-light:#fee2e2;
      --border:#e2e8f0; --border-focus:#3b82f6;
      --radius:10px; --radius-lg:14px;
      --shadow:0 1px 3px rgba(15,23,42,.08), 0 1px 2px rgba(15,23,42,.06);
      --shadow-lg:0 10px 25px -5px rgba(15,23,42,.1), 0 8px 10px -6px rgba(15,23,42,.04);
      --shadow-xl:0 20px 30px -10px rgba(15,23,42,.12);
    }
    
    * { box-sizing: border-box; }
    
    html, body { 
      height: 100%; 
      margin: 0; 
      padding: 0;
    }
    
    body { 
      background: linear-gradient(135deg, #f5f7fa 0%, #e9ecef 100%);
      font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', Roboto, Ubuntu, 'Helvetica Neue', Arial, sans-serif;
      color: var(--text);
      line-height: 1.6;
      padding: 20px;
      min-height: 100vh;
    }
    
    /* Typography */
    h2, h3, h4 { 
      margin: 0 0 20px 0; 
      font-weight: 700;
      color: var(--text);
      letter-spacing: -0.02em;
    }
    h2 { font-size: 28px; }
    h3 { font-size: 24px; }
    h4 { 
      font-size: 18px; 
      font-weight: 600;
      margin-bottom: 16px;
    }
    
    /* Enhanced Navigation */
    nav { 
      background: var(--card);
      padding: 16px 24px;
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-lg);
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }
    
    nav a { 
      color: var(--text-secondary);
      text-decoration: none;
      font-weight: 600;
      font-size: 14px;
      padding: 8px 16px;
      border-radius: var(--radius);
      transition: all 0.2s ease;
      position: relative;
    }
    
    nav a:hover { 
      color: var(--primary);
      background: var(--primary-light);
      transform: translateY(-1px);
    }
    
    nav span { 
      color: var(--border);
      margin: 0 4px;
    }
    
    /* Enhanced Cards */
    .card { 
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow-lg);
      padding: 28px;
      margin: 16px 0;
      transition: all 0.3s ease;
    }
    
    .card:hover {
      box-shadow: var(--shadow-xl);
    }
    
    /* Enhanced Buttons */
    .btn { 
      background: var(--primary);
      color: white;
      border: none;
      padding: 11px 20px;
      border-radius: var(--radius);
      font-weight: 600;
      font-size: 14px;
      cursor: pointer;
      transition: all 0.2s ease;
      margin-right: 10px;
      margin-top: 8px;
      box-shadow: 0 1px 2px rgba(59,130,246,.2);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    
    .btn:hover { 
      background: var(--primary-hover);
      transform: translateY(-2px);
      box-shadow: 0 4px 8px rgba(59,130,246,.3);
    }
    
    .btn:active {
      transform: translateY(0);
    }
    
    .btn-outline { 
      background: transparent;
      color: var(--primary);
      border: 2px solid var(--primary);
      box-shadow: none;
    }
    
    .btn-outline:hover {
      background: var(--primary-light);
      box-shadow: 0 2px 4px rgba(59,130,246,.15);
    }
    
    .btn-danger { 
      background: var(--danger);
      box-shadow: 0 1px 2px rgba(239,68,68,.2);
    }
    
    .btn-danger:hover {
      background: var(--danger-hover);
      box-shadow: 0 4px 8px rgba(239,68,68,.3);
    }
    
    /* Enhanced Inputs */
    .input, .dash-dropdown, textarea { 
      padding: 11px 14px;
      border: 2px solid var(--border);
      border-radius: var(--radius);
      background: var(--bg-alt);
      outline: none;
      width: 100%;
      max-width: 560px;
      margin-right: 10px;
      margin-bottom: 12px;
      font-size: 14px;
      font-family: inherit;
      transition: all 0.2s ease;
      color: var(--text);
    }
    
    .input:focus, textarea:focus {
      border-color: var(--border-focus);
      box-shadow: 0 0 0 3px rgba(59,130,246,.1);
    }
    
    .input::placeholder, textarea::placeholder {
      color: var(--muted);
    }
    
    textarea {
      resize: vertical;
      min-height: 80px;
    }
    
    /* Form Layouts */
    .two-col { 
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 16px;
      margin-bottom: 16px;
    }
    
    .form-group {
      margin-bottom: 20px;
    }
    
    .form-label {
      display: block;
      font-weight: 600;
      font-size: 13px;
      color: var(--text-secondary);
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    
    /* Enhanced KPI Cards */
    .kpi { 
      display: inline-block;
      min-width: 240px;
      padding: 20px 24px;
      margin: 8px;
      background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      box-shadow: var(--shadow);
      transition: all 0.3s ease;
      position: relative;
      overflow: hidden;
    }
    
    .kpi::before {
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      width: 4px;
      height: 100%;
      background: var(--primary);
      opacity: 0;
      transition: opacity 0.3s ease;
    }
    
    .kpi:hover {
      transform: translateY(-4px);
      box-shadow: var(--shadow-lg);
    }
    
    .kpi:hover::before {
      opacity: 1;
    }
    
    .kpi .label { 
      color: var(--muted);
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 8px;
    }
    
    .kpi .value { 
      font-size: 28px;
      font-weight: 800;
      margin-top: 6px;
      color: var(--text);
      line-height: 1.2;
    }
    
    /* Utilities */
    .hr { 
      height: 1px;
      background: linear-gradient(to right, transparent, var(--border), transparent);
      margin: 28px 0;
      border: none;
    }
    
    .muted { 
      color: var(--muted);
      font-size: 14px;
    }
    
    .stack { 
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      align-items: center;
      margin: 16px 0;
    }
    
    .pad-top {
      padding-top: 16px;
    }
    
    /* Status Badges */
    .badge {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    
    .badge-success {
      background: var(--success-light);
      color: var(--success);
    }
    
    .badge-warning {
      background: var(--warning-light);
      color: var(--warning);
    }
    
    .badge-danger {
      background: var(--danger-light);
      color: var(--danger);
    }
    
    .badge-info {
      background: var(--primary-light);
      color: var(--primary);
    }
    
    /* Message Styles */
    .message {
      padding: 12px 16px;
      border-radius: var(--radius);
      margin: 12px 0;
      font-size: 14px;
      font-weight: 500;
    }
    
    .message-error {
      background: var(--danger-light);
      color: var(--danger);
      border-left: 4px solid var(--danger);
    }
    
    .message-success {
      background: var(--success-light);
      color: var(--success);
      border-left: 4px solid var(--success);
    }
    
    .message-info {
      background: var(--primary-light);
      color: var(--primary);
      border-left: 4px solid var(--primary);
    }
    
    .message-warning {
      background: var(--warning-light);
      color: var(--warning);
      border-left: 4px solid var(--warning);
    }
    
    /* Table Enhancements */
    .dash-table-container {
      margin-top: 16px;
      border-radius: var(--radius);
      overflow: hidden;
      border: 1px solid var(--border);
    }
    
    .dash-spreadsheet {
      border: none !important;
    }
    
    .dash-spreadsheet-container {
      overflow-x: auto;
    }
    
    /* Radio Items Enhancement */
    input[type="radio"] {
      margin-right: 8px;
      accent-color: var(--primary);
    }
    
    /* Upload Component */
    .dash-upload {
      display: inline-block;
      margin-bottom: 16px;
    }
    
    /* Dropdown Enhancement */
    .Select-control {
      border-color: var(--border) !important;
      border-width: 2px !important;
      border-radius: var(--radius) !important;
    }
    
    .Select-control:hover {
      border-color: var(--primary) !important;
    }
    
    .is-focused .Select-control {
      border-color: var(--border-focus) !important;
      box-shadow: 0 0 0 3px rgba(59,130,246,.1) !important;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
      body {
        padding: 12px;
      }
      
      .card {
        padding: 20px;
      }
      
      nav {
        padding: 12px 16px;
      }
      
      .two-col {
        grid-template-columns: 1fr;
      }
      
      .kpi {
        min-width: 100%;
        margin: 8px 0;
      }
      
      h2 { font-size: 24px; }
      h3 { font-size: 20px; }
    }
    
    /* Loading State */
    ._dash-loading {
      opacity: 0.7;
    }
    
    /* Scrollbar Styling */
    ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }
    
    ::-webkit-scrollbar-track {
      background: var(--bg);
    }
    
    ::-webkit-scrollbar-thumb {
      background: var(--border);
      border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
      background: var(--muted);
    }
    
    /* Tooltip styling for better UX */
    [title] {
      position: relative;
      cursor: help;
    }
    
    /* Focus indicators for accessibility */
    a:focus, button:focus, input:focus, select:focus, textarea:focus {
      outline: 2px solid var(--primary);
      outline-offset: 2px;
    }
    
    /* Better link hover states */
    a {
      transition: all 0.2s ease;
    }
    
    /* Smooth animations */
    * {
      transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* Help text styling */
    .help-text {
      font-size: 12px;
      color: var(--muted);
      margin-top: 4px;
      font-style: italic;
    }
    
    /* Empty state styling */
    .empty-state {
      text-align: center;
      padding: 60px 20px;
      color: var(--muted);
    }
    
    .empty-state h3 {
      color: var(--text-secondary);
      margin-bottom: 12px;
    }
    
    /* Active navigation indicator */
    nav a.active {
      background: var(--primary-light);
      color: var(--primary);
      font-weight: 700;
    }
    
    /* Better table styling */
    .dash-table-container table {
      border-collapse: separate;
      border-spacing: 0;
    }
    
    /* Loading animation */
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }
    
    ._dash-loading-callback {
      animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Success/Error state animations */
    .message {
      animation: slideInDown 0.3s ease-out;
    }
    
    @keyframes slideInDown {
      from {
        opacity: 0;
        transform: translateY(-10px);
      }
      to {
        opacity: 1;
        transform: translateY(0);
      }
    }
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
    
    # Logo section
    logo = html.Div([
        html.Img(
            src="https://starlab-public.s3.us-east-1.amazonaws.com/starlab_images/transparent-slc-rgb.png",
            style={
                "height": "36px",
                "marginRight": "16px",
                "objectFit": "contain",
                "cursor": "pointer"
            },
            title="Starlab Capital - Resource Management System"
        ),
        html.Div([
            html.Div("RMS", style={"fontSize": "16px", "fontWeight": "700", "color": "var(--text)", "lineHeight": "1"}),
            html.Div("Resource Mgmt", style={"fontSize": "9px", "color": "var(--muted)", "lineHeight": "1", "marginTop": "2px"})
        ], style={"display": "flex", "flexDirection": "column", "marginRight": "24px"})
    ], style={"display": "flex", "alignItems": "center", "marginRight": "auto"})
    
    # Build navigation items based on role
    nav_items = []
    if user.role == Role.EMP:
        nav_items = [
            dcc.Link("📊 Dashboard", href="/", title="View your overview"),
            dcc.Link("💼 My Assets", href="/assets", title="View and manage your assets"),
            dcc.Link("📝 Requests", href="/requests", title="Submit and track resource requests"),
            dcc.Link("👤 My Profile", href="/profile", title="Update your profile information"),
        ]
    else:
        nav_items = [
            dcc.Link("📊 Dashboard", href="/", title="View system overview"),
            dcc.Link("💼 Assets", href="/assets", title="Manage all assets"),
            dcc.Link("📝 Requests", href="/requests", title="Review and approve requests"),
            dcc.Link("📈 Reports", href="/reports", title="View analytics and reports"),
        ]
        if user.role == Role.GM:
            nav_items.append(dcc.Link("🏢 Offices", href="/offices", title="View and manage offices"))
            nav_items.append(dcc.Link("⚙️ Admin", href="/admin", title="System administration"))
        else:
            nav_items.append(dcc.Link("👥 Employees", href="/employees", title="Manage your team"))
    
    # Add user info and logout
    user_info = html.Div([
        html.Span(f"{user.username}", style={"color": "var(--text-secondary)", "fontWeight": "600", "marginRight": "12px"}),
        html.Span(f"({role_name(user.role.value)})", style={"color": "var(--muted)", "fontSize": "13px", "marginRight": "16px"}),
        dcc.Link("🚪 Logout", href="/logout", style={"color": "var(--danger)"}, title="Sign out of your account")
    ], style={"marginLeft": "auto", "display": "flex", "alignItems": "center"})
    
    return html.Nav([logo] + nav_items + [user_info], style={"display": "flex", "alignItems": "center", "gap": "4px"})

def login_layout():
    return html.Div([
        navbar(),
        html.Div(style={"maxWidth": "480px", "margin": "60px auto"}, children=[
        html.Div(className="card", children=[
                html.Div(style={"textAlign": "center", "marginBottom": "32px"}, children=[
                    html.Img(
                        src="https://starlab-public.s3.us-east-1.amazonaws.com/starlab_images/transparent-slc-rgb.png",
                        style={
                            "height": "80px",
                            "marginBottom": "24px",
                            "objectFit": "contain"
                        }
                    ),
                    html.H2("🔐 Welcome to RMS", style={"marginBottom": "8px"}),
                    html.Div("Resource Management System", className="muted", style={"marginBottom": "4px"}),
                    html.Div("Powered by Starlab Capital", style={"fontSize": "12px", "color": "var(--muted)", "fontWeight": "500"})
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Username", className="form-label"),
                    dcc.Input(id="login-username", placeholder="Enter your username", className="input", style={"maxWidth": "100%"}, n_submit=0),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Password", className="form-label"),
                    dcc.Input(id="login-password", type="password", placeholder="Enter your password", className="input", style={"maxWidth": "100%"}, n_submit=0),
                ]),
                html.Button("🔓 Login", id="login-btn", className="btn", style={"width": "100%", "marginTop": "8px"}),
                html.Div(id="login-msg", style={"marginTop": "16px"}),
            ])
        ])
    ])

def dashboard_layout():
    user = current_user()
    if not user:
        return login_layout()
    scope = "Company-wide metrics" if user.role == Role.GM else "Your office metrics"
    welcome_emoji = "👨‍💼" if user.role == Role.GM else ("👔" if user.role == Role.OM else "👤")
    
    # Role-specific quick guide
    if user.role == Role.EMP:
        quick_guide = html.Div(style={"background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "color": "white", "padding": "20px", "borderRadius": "var(--radius-lg)", "marginBottom": "20px"}, children=[
            html.H4("🎯 Quick Start Guide", style={"color": "white", "marginBottom": "12px"}),
            html.Div([
                html.Div("✓ View your assets in the 'My Assets' section", style={"marginBottom": "8px"}),
                html.Div("✓ Submit new resource requests in 'Requests'", style={"marginBottom": "8px"}),
                html.Div("✓ Update your profile information in 'My Profile'", style={"marginBottom": "8px"}),
                html.Div("💡 Tip: You can press Enter to submit forms!", style={"marginTop": "12px", "fontStyle": "italic", "opacity": "0.9"})
            ], style={"fontSize": "14px"})
        ])
    elif user.role == Role.OM:
        quick_guide = html.Div(style={"background": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)", "color": "white", "padding": "20px", "borderRadius": "var(--radius-lg)", "marginBottom": "20px"}, children=[
            html.H4("🎯 Manager Quick Guide", style={"color": "white", "marginBottom": "12px"}),
            html.Div([
                html.Div("✓ Manage office assets in 'Assets' section", style={"marginBottom": "8px"}),
                html.Div("✓ Review and approve requests in 'Requests'", style={"marginBottom": "8px"}),
                html.Div("✓ Add new employees in 'Employees'", style={"marginBottom": "8px"}),
                html.Div("✓ View analytics and reports in 'Reports'", style={"marginBottom": "8px"}),
            ], style={"fontSize": "14px"})
        ])
    else:  # GM
        quick_guide = html.Div(style={"background": "linear-gradient(135deg, #fa709a 0%, #fee140 100%)", "color": "white", "padding": "20px", "borderRadius": "var(--radius-lg)", "marginBottom": "20px"}, children=[
            html.H4("🎯 Admin Quick Guide", style={"color": "white", "marginBottom": "12px"}),
            html.Div([
                html.Div("✓ Create offices and managers in 'Admin'", style={"marginBottom": "8px"}),
                html.Div("✓ Manage all assets company-wide in 'Assets'", style={"marginBottom": "8px"}),
                html.Div("✓ Review all requests in 'Requests'", style={"marginBottom": "8px"}),
                html.Div("✓ View company analytics in 'Reports'", style={"marginBottom": "8px"}),
            ], style={"fontSize": "14px"})
        ])
    
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.Div(style={"marginBottom": "24px"}, children=[
                html.H3(f"{welcome_emoji} Welcome, {user.username}!", style={"marginBottom": "8px"}),
                html.Div(className="muted", children=[
                    html.Span(f"{role_name(user.role.value)} • ", style={"fontWeight": "600"}),
                    html.Span(scope)
                ]),
            ]),
            quick_guide,
            html.Div(id="dashboard-cards", className="pad-top")
        ])
    ])

def _uploader_component(id_):
    return dcc.Upload(
        id=id_,
        children=html.Button("📎 Upload Bill / Drag & Drop", className="btn btn-outline"),
        multiple=False,
        style={
            "width": "100%",
            "borderRadius": "var(--radius)",
            "border": "2px dashed var(--border)",
            "padding": "20px",
            "textAlign": "center",
            "cursor": "pointer",
            "transition": "all 0.2s ease",
            "background": "var(--bg-alt)"
        }
    )

def _alloc_radio_for_user(user):
    """
    Build allocation radio options per role:
      - GM: UNALLOCATED + OFFICE + EMPLOYEE (as before)
      - OM: OFFICE + EMPLOYEE (NO Unallocated)  <-- req #1
      - EMP: EMPLOYEE only                       <-- req #4
    Also returns a sensible default value per role.
    """
    if user.role == Role.GM:
        options = [
            {"label":"Global / Unallocated", "value": AllocationType.UNALLOCATED.value},
            {"label":"Allocate to Office", "value": AllocationType.OFFICE.value},
            {"label":"Allocate to Employee", "value": AllocationType.EMPLOYEE.value},
        ]
        default_val = AllocationType.UNALLOCATED.value
    elif user.role == Role.OM:
        options = [
            {"label":"Allocate to Office", "value": AllocationType.OFFICE.value},
            {"label":"Allocate to Employee", "value": AllocationType.EMPLOYEE.value},
        ]
        default_val = AllocationType.OFFICE.value
    else:  # EMP
        options = [
            {"label":"Allocate to Me", "value": AllocationType.EMPLOYEE.value},
        ]
        default_val = AllocationType.EMPLOYEE.value
    return options, default_val

def assets_layout():
    user = current_user()
    if not user:
        return login_layout()
    header = "💼 My Assets" if user.role == Role.EMP else "💼 Assets Management"
    button_label = "➕ Add to My Profile" if user.role == Role.EMP else "➕ Add Asset"
    radio_options, radio_default = _alloc_radio_for_user(user)
    
    # Help text based on role
    if user.role == Role.EMP:
        help_text = "Add assets to your profile (e.g., laptop, desk, monitor). This helps track what resources you're using."
    else:
        help_text = "Add new assets to the system and assign them to offices or employees. All fields marked with * are required."
    
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3(header, style={"marginBottom": "8px"}),
            html.Div(help_text, className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
            html.Div(className="form-group", children=[
                html.Label("📄 Upload Bill (Optional)", className="form-label"),
                html.Div("You can upload a receipt or invoice for this asset", className="muted", style={"fontSize": "12px", "marginBottom": "8px"}),
            _uploader_component("upload-bill"),
            ]),
            html.Div(className="two-col", children=[
                html.Div(className="form-group", children=[
                    html.Label("Asset Name *", className="form-label"),
                    dcc.Input(id="asset-name", placeholder="e.g., Laptop, Desk, Monitor", className="input", style={"maxWidth": "100%"}),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Price *", className="form-label"),
                    dcc.Input(id="asset-price", placeholder="0.00", type="number", className="input", style={"maxWidth": "100%"}),
                ]),
            ]),
            html.Div(className="form-group", children=[
                html.Label("Quantity *", className="form-label"),
                dcc.Input(id="asset-qty", placeholder="1", type="number", value=1, className="input", style={"maxWidth": "200px"}),
            ]),
            html.Div(className="form-group", children=[
                html.Label("Allocation Type", className="form-label"),
            dcc.RadioItems(
                id="alloc-type",
                options=radio_options,
                value=radio_default,
                    labelStyle={"display":"block", "margin":"10px 0", "fontWeight": "500", "color": "var(--text-secondary)"}
                ),
            ]),
            html.Div(className="form-group", children=[
                html.Label("Allocation Target", className="form-label"),
                dcc.Dropdown(id="alloc-target", placeholder="Choose office/employee (if applicable)", className="dash-dropdown", style={"maxWidth": "100%"}),
            ]),
            html.Button(button_label, id="add-asset-btn", className="btn"),
            html.Div(id="asset-add-msg", style={"marginTop":"16px"}),
            dcc.ConfirmDialog(id="asset-dialog"),
        ]),
        html.Div(className="card", children=[
            html.Div(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "16px"}, children=[
                html.H4(f"{header} List", style={"margin": "0"}),
                html.Div(className="badge badge-info", children="Live Data")
            ]),
            html.Div(id="assets-table")
        ])
    ])

def requests_layout():
    user = current_user()
    if not user:
        return login_layout()
    
    # Role-specific help text
    if user.role == Role.EMP:
        help_text = "Submit a request for new resources you need. Your manager will review and approve it."
    else:
        help_text = "Create requests on behalf of employees or review pending requests below."
    
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("📝 New Request", style={"marginBottom": "8px"}),
            html.Div(help_text, className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
            html.Div(id="request-form"),
            dcc.ConfirmDialog(id="req-dialog")
        ]),
        html.Div(className="card", children=[
            html.Div(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "8px"}, children=[
                html.H4("📋 All Requests", style={"margin": "0"}),
                html.Div(className="badge badge-warning", children="Pending Review")
            ]),
            html.Div("Track the status of your requests. Managers can select a request and take action below.", className="muted", style={"marginBottom": "16px", "fontSize": "13px"}) if user.role != Role.EMP else html.Div("Track the status of all your submitted requests here.", className="muted", style={"marginBottom": "16px", "fontSize": "13px"}),
            html.Div(id="requests-table")
        ])
    ])

def reports_layout():
    user = current_user()
    if not user:
        return login_layout()
    if user.role == Role.EMP:
        return html.Div([navbar(), html.Div(className="card", children=[
            html.Div(style={"textAlign": "center", "padding": "40px"}, children=[
                html.H3("📊 Reports Unavailable"),
                html.Div("Reports are only available for Managers.", className="muted")
            ])
        ])])
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("📈 Analytics & Reports", style={"marginBottom": "8px"}),
            html.Div("View comprehensive analytics, track resource allocation, and add remarks for employees.", className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
            html.Div(id="reports-content"),
            dcc.ConfirmDialog(id="reports-dialog"),
            html.Div(id="reports-msg", style={"marginTop":"16px"}),
        ])
    ])

def employees_layout():
    user = current_user()
    if not user:
        return login_layout()
    if user.role != Role.OM:
        return html.Div([navbar(), html.Div(className="card", children=[
            html.Div(style={"textAlign": "center", "padding": "40px"}, children=[
                html.H3("⚠️ Access Restricted"),
                html.Div("Only Office Managers can manage employees.", className="muted")
            ])
        ])])
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("👥 Add New Employee", style={"marginBottom": "8px"}),
            html.Div("Add employees to your office. They'll be able to login with the credentials you provide here.", className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
            html.Div(className="two-col", children=[
                html.Div(className="form-group", children=[
                    html.Label("Employee Name *", className="form-label"),
                    dcc.Input(id="emp-new-name", placeholder="Full name", className="input", style={"maxWidth": "100%"}),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Phone Number", className="form-label"),
                    dcc.Input(id="emp-new-phone", placeholder="(optional)", className="input", style={"maxWidth": "100%"}),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Username *", className="form-label"),
                    dcc.Input(id="emp-new-username", placeholder="Login username", className="input", style={"maxWidth": "100%"}),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Password *", className="form-label"),
                    dcc.Input(id="emp-new-password", type="password", placeholder="Initial password", className="input", style={"maxWidth": "100%"}),
                ]),
            ]),
            html.Button("➕ Add Employee", id="emp-add-btn", className="btn"),
            dcc.ConfirmDialog(id="emp-dialog"),
            html.Div(id="emp-add-msg", style={"marginTop":"16px"})
        ]),
        html.Div(className="card", children=[
            html.Div(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "16px"}, children=[
                html.H4("📋 Employees in My Office", style={"margin": "0"}),
                html.Div(className="badge badge-info", children="Active Staff")
            ]),
            html.Div(id="emp-table")
        ])
    ])

def admin_layout():
    user = current_user()
    if not user or user.role != Role.GM:
        return html.Div([navbar(), html.Div(className="card", children=[
            html.Div(style={"textAlign": "center", "padding": "40px"}, children=[
                html.H3("🔒 Admin Access Only"),
                html.Div("This section is restricted to General Managers.", className="muted")
            ])
        ])])
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("⚙️ Admin Panel", style={"marginBottom": "8px"}),
            html.Div("System administration area. Set up your organization structure by creating offices and assigning managers.", className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
            
            html.H4("🏢 Create Office", style={"marginTop": "24px", "marginBottom": "8px"}),
            html.Div("First, create offices (branches/departments) for your organization.", className="muted", style={"marginBottom": "12px", "fontSize": "13px"}),
            html.Div(className="two-col", children=[
                html.Div(className="form-group", children=[
                    html.Label("Office Name *", className="form-label"),
                    dcc.Input(id="new-office-name", placeholder="e.g., East Branch, West Branch", className="input", style={"maxWidth": "100%"}),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Location (Optional)", className="form-label"),
                    dcc.Input(id="new-office-location", placeholder="City / Branch / Building", className="input", style={"maxWidth": "100%"}),
                ]),
            ]),
            html.Button("➕ Add Office", id="btn-add-office", className="btn"),
            html.Div(id="msg-add-office", style={"marginTop":"12px"}),
            
            html.Div(className="hr"),
            
            html.H4("👔 Create Office Manager", style={"marginBottom": "8px"}),
            html.Div("Assign a manager to each office. They will manage employees and assets for their office.", className="muted", style={"marginBottom": "12px", "fontSize": "13px"}),
            html.Div(className="two-col", children=[
                html.Div(className="form-group", children=[
                    html.Label("Select Office *", className="form-label"),
                    dcc.Dropdown(id="om-office", placeholder="Choose office", className="dash-dropdown", style={"maxWidth": "100%"}),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Username *", className="form-label"),
                    dcc.Input(id="om-username", placeholder="Login username", className="input", style={"maxWidth": "100%"}),
                ]),
            ]),
            html.Div(className="form-group", children=[
                html.Label("Password *", className="form-label"),
                dcc.Input(id="om-password", type="password", placeholder="Initial password", className="input"),
            ]),
            html.Button("➕ Create OM", id="btn-create-om", className="btn"),
            dcc.ConfirmDialog(id="admin-dialog"),
            html.Div(id="msg-create-om", style={"marginTop":"12px"}),
            
            html.Div(className="hr"),
            
            html.H4("🔑 Reset OM Password", style={"marginBottom": "8px"}),
            html.Div("Reset an Office Manager's password if they've forgotten it.", className="muted", style={"marginBottom": "12px", "fontSize": "13px"}),
            html.Div(className="two-col", children=[
                html.Div(className="form-group", children=[
                    html.Label("Select OM User *", className="form-label"),
                    dcc.Dropdown(id="om-existing", placeholder="Choose OM", className="dash-dropdown", style={"maxWidth": "100%"}),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("New Password *", className="form-label"),
                    dcc.Input(id="om-new-pass", type="password", placeholder="Enter new password", className="input", style={"maxWidth": "100%"}),
                ]),
            ]),
            html.Button("🔄 Reset Password", id="btn-om-reset", className="btn btn-outline"),
            html.Div(id="msg-om-reset", style={"marginTop":"12px"}),
        ])
    ])

def offices_layout():
    user = current_user()
    if not user or user.role != Role.GM:
        return html.Div([navbar(), html.Div(className="card", children=[
            html.Div(style={"textAlign": "center", "padding": "40px"}, children=[
                html.H3("🔒 GM Access Only"),
                html.Div("This section is restricted to General Managers.", className="muted")
            ])
        ])])
    
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("🏢 Offices Management", style={"marginBottom": "8px"}),
            html.Div("View all offices in the organization. You can manage office details in the Admin panel.", className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
            html.Div(style={"display": "flex", "alignItems": "center", "justifyContent": "space-between", "marginBottom": "16px"}, children=[
                html.H4("📋 All Offices", style={"margin": "0"}),
                html.Div(className="badge badge-info", children="Live Data")
            ]),
            html.Div(id="offices-table")
        ])
    ])

def profile_layout():
    user = current_user()
    if not user:
        return login_layout()
    return html.Div([
        navbar(),
        html.Div(className="card", children=[
            html.H3("👤 My Profile", style={"marginBottom": "8px"}),
            html.Div("Update your personal information. Your manager can also leave remarks here for you.", className="muted", style={"marginBottom": "24px", "fontSize": "14px"}),
            html.Div(id="profile-form"),
            # Kept component but we'll NEVER display it (req #5)
            dcc.ConfirmDialog(id="profile-dialog"),
            html.Div(id="profile-msg", style={"marginTop":"16px"}),
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
    if path == "/offices":
        return offices_layout()
    if path == "/admin":
        return admin_layout()
    if path == "/profile":
        return profile_layout()
    return html.Div([navbar(), html.Div(className="card", children=html.H3("Not Found"))])

# ---------- Login ----------
@app.callback(
    Output("login-msg", "children"), 
    Input("login-btn", "n_clicks"),
    Input("login-username", "n_submit"),
    Input("login-password", "n_submit"),
    State("login-username", "value"), 
    State("login-password", "value"),
    prevent_initial_call=True
)
def do_login(n_clicks, n_submit_user, n_submit_pass, username, password):
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
            return html.Div("❌ Invalid credentials. Please try again.", className="message message-error")
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
        return (html.Div("❌ Asset name is required.", className="message message-error"), render_assets_table(), "", False, name, price, qty, contents)
    if price_val <= 0:
        return (html.Div("❌ Price must be greater than 0.", className="message message-error"), render_assets_table(), "", False, name, price, qty, contents)
    if qty_val < 1:
        return (html.Div("❌ Quantity must be at least 1.", className="message message-error"), render_assets_table(), "", False, name, price, qty, contents)

    saved_path = None
    if contents and filename:
        _, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        fname = f"{datetime.datetime.utcnow().timestamp()}_{filename}"
        saved_path = os.path.join(UPLOAD_FOLDER, fname)
        with open(saved_path, "wb") as f:
            f.write(decoded)

    with SessionLocal() as s:
        # Enforce allocation rules by role (req #1 + #4)
        if user.role == Role.GM:
            a_type = AllocationType(alloc_type)
            a_id = None
            if a_type == AllocationType.OFFICE:
                a_id = int(alloc_target) if alloc_target else None
            elif a_type == AllocationType.EMPLOYEE:
                a_id = int(alloc_target) if alloc_target else None
        elif user.role == Role.OM:
            # OM cannot create UNALLOCATED
            if alloc_type == AllocationType.EMPLOYEE.value:
                a_type = AllocationType.EMPLOYEE
                a_id = int(alloc_target) if alloc_target else None
            else:
                a_type = AllocationType.OFFICE
                a_id = user.office_id
        else:  # EMP can only allocate to self
            a_type = AllocationType.EMPLOYEE
            emp = _employee_for_user(user, s)
            a_id = emp.id if emp else None

        s.add(Asset(name=name, price=price_val, quantity=qty_val, bill_path=saved_path,
                    allocation_type=a_type, allocation_id=a_id))
        s.commit()
    return (html.Div("✅ Asset added successfully!", className="message message-success"), render_assets_table(), "Asset added.", True, "", "", 1, None)

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
        # Employee: only their own assets
        if user.role == Role.EMP:
            emp = _employee_for_user(user, s)
            assets = [] if not emp else s.query(Asset).filter(
                Asset.allocation_type == AllocationType.EMPLOYEE,
                Asset.allocation_id == emp.id
            ).all()

        # Office Manager: only office assets + assets of employees in their office
        elif user.role == Role.OM:
            emp_ids = [e.id for e in s.query(Employee).filter(Employee.office_id == user.office_id)]
            assets = s.query(Asset).filter(
                ((Asset.allocation_type == AllocationType.OFFICE) & (Asset.allocation_id == user.office_id)) |
                ((Asset.allocation_type == AllocationType.EMPLOYEE) & (Asset.allocation_id.in_(emp_ids)))
            ).all()

        # GM: all assets
        else:
            assets = s.query(Asset).all()

        rows = [{
            "id": a.id,
            "name": a.name,
            "price": a.price,
            "qty": a.quantity,
            "bill": _bill_link_asset(a),
            "allocation": a.allocation_type.value,
            "allocation_id": a.allocation_id
        } for a in assets]

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
        # For OM/EMP we never show unallocated (req #1 & #4)
        return [], None, "No target"

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
                html.Div(className="form-group", children=[
                    html.Label("Employee (Auto-selected)", className="form-label"),
                    dcc.Dropdown(id="req-employee", options=options, value=(emp.id if emp else None), className="dash-dropdown", disabled=True, style={"maxWidth": "100%"}),
                ]),
                html.Div(className="two-col", children=[
                    html.Div(className="form-group", children=[
                        html.Label("Asset Name *", className="form-label"),
                        dcc.Input(id="req-asset-name", placeholder="What asset do you need?", className="input", style={"maxWidth": "100%"}),
                    ]),
                    html.Div(className="form-group", children=[
                        html.Label("Quantity *", className="form-label"),
                        dcc.Input(id="req-qty", type="number", value=1, className="input", style={"maxWidth": "100%"}),
                    ]),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Price (Optional)", className="form-label"),
                    dcc.Input(id="req-price", placeholder="Estimated price", type="number", className="input"),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("📄 Upload Bill (Optional)", className="form-label"),
                    _uploader_component("req-bill"),
                ]),
                html.Button("✅ Submit Request", id="req-submit", className="btn"),
                html.Div(id="req-msg", style={"marginTop":"16px"})
            ])
        employees = s.query(Employee).filter(Employee.office_id == user.office_id).all() \
            if user.role == Role.OM else s.query(Employee).all()
        options = [{"label": e.name, "value": e.id} for e in employees]
        return html.Div([
            html.Div(className="form-group", children=[
                html.Label("Select Employee *", className="form-label"),
                dcc.Dropdown(id="req-employee", options=options, placeholder="Choose employee", className="dash-dropdown", style={"maxWidth": "100%"}),
            ]),
            html.Div(className="two-col", children=[
                html.Div(className="form-group", children=[
                    html.Label("Asset Name *", className="form-label"),
                    dcc.Input(id="req-asset-name", placeholder="What asset is needed?", className="input", style={"maxWidth": "100%"}),
                ]),
                html.Div(className="form-group", children=[
                    html.Label("Quantity *", className="form-label"),
                    dcc.Input(id="req-qty", type="number", value=1, className="input", style={"maxWidth": "100%"}),
                ]),
            ]),
            html.Div(className="form-group", children=[
                html.Label("Price (Optional)", className="form-label"),
                dcc.Input(id="req-price", placeholder="Estimated price", type="number", className="input"),
            ]),
            html.Div(className="form-group", children=[
                html.Label("📄 Upload Bill (Optional)", className="form-label"),
                _uploader_component("req-bill"),
            ]),
            html.Button("✅ Submit Request", id="req-submit", className="btn"),
            html.Div(id="req-msg", style={"marginTop":"16px"})
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
        return html.Div("❌ Please enter an asset name.", className="message message-error"), render_requests_table(), "", False, asset_name, qty, price, contents
    if qty < 1:
        return html.Div("❌ Quantity must be at least 1.", className="message message-error"), render_requests_table(), "", False, asset_name, qty, price, contents

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
            return html.Div("❌ Select an employee.", className="message message-error"), render_requests_table(), "", False, asset_name, qty, price, contents
        emp = s.get(Employee, emp_id)
        if not emp:
            return html.Div("❌ Invalid employee.", className="message message-error"), render_requests_table(), "", False, asset_name, qty, price, contents
        if user.role == Role.OM and emp.office_id != user.office_id:
            return html.Div("❌ You can only submit requests for your office.", className="message message-error"), render_requests_table(), "", False, asset_name, qty, price, contents
        s.add(Request(employee_id=emp.id, office_id=emp.office_id, asset_name=asset_name,
                      quantity=qty, price=price_val, bill_path=saved_path))
        s.commit()
    return html.Div("✅ Request submitted successfully!", className="message message-success"), render_requests_table(), "Request submitted.", True, "", 1, "", None

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
    controls = html.Div(style={"marginTop": "24px", "padding": "20px", "background": "var(--bg-alt)", "borderRadius": "var(--radius)", "border": "1px solid var(--border)"}, children=[
        html.Label("📝 Manager Actions", className="form-label", style={"marginBottom": "12px"}),
        html.Div(className="form-group", children=[
            html.Label("Add Remark (Optional)", className="form-label"),
            dcc.Textarea(id="mgr-remark", placeholder="Add a note about this request...", className="input", style={"height":"80px", "width":"100%", "maxWidth": "100%"}),
        ]),
        html.Div(className="stack", children=[
            html.Button("✅ Approve", id="btn-approve", className="btn"),
            html.Button("❌ Reject", id="btn-reject", className="btn btn-danger"),
            html.Button("⏳ Return Pending", id="btn-return-pending", className="btn btn-outline"),
            html.Button("✔️ Returned", id="btn-returned", className="btn btn-outline"),
        ])
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
        return html.Div("❌ Not allowed.", className="message message-error"), render_requests_table(), "", False
    if not selected:
        return html.Div("⚠️ Select a request first.", className="message message-info"), render_requests_table(), "", False

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
            return html.Div("❌ Request not found.", className="message message-error"), render_requests_table(), "", False
        if user.role == Role.OM and r.office_id != user.office_id:
            return html.Div("❌ You can only update requests in your office.", className="message message-error"), render_requests_table(), "", False

        # hard guards ---------------------------------------------------------
        if trig == "btn-approve":
            if r.status == RequestStatus.APPROVED:
                return html.Div("ℹ️ No change needed.", className="message message-info"), render_requests_table(), "This request is already approved.", True
            if r.status == RequestStatus.RETURNED:
                return html.Div("ℹ️ No change needed.", className="message message-info"), render_requests_table(), "This request is already marked Returned.", True

        if trig == "btn-reject":
            if r.status == RequestStatus.APPROVED:
                return html.Div("⚠️ Cannot reject.", className="message message-warning"), render_requests_table(), "Approved requests can't be rejected.", True
            if r.status == RequestStatus.RETURNED:
                return html.Div("⚠️ Cannot reject.", className="message message-warning"), render_requests_table(), "Returned requests can't be rejected.", True

        if trig == "btn-return-pending" and r.status != RequestStatus.APPROVED:
            return html.Div("⚠️ Invalid action.", className="message message-warning"), render_requests_table(), "Only approved requests can be marked return pending.", True

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
            r.status = RequestStatus.RETURN_PENDING

        elif status == RequestStatus.RETURNED:
            if matched_asset:
                matched_asset.returned = True
            r.status = RequestStatus.RETURNED

        elif status == RequestStatus.REJECTED:
            if matched_asset:
                s.delete(matched_asset)
            r.status = RequestStatus.REJECTED

        s.commit()

    return html.Div(f"✅ Status updated to {status.value}.", className="message message-success"), render_requests_table(), "", False

# ---------- Employees (OM) ----------
def _render_emp_table_for_om(user):
    with SessionLocal() as s:
        emps = s.query(Employee).filter(Employee.office_id == user.office_id).order_by(Employee.id).all()
        data = [{"id": e.id, "name": e.name, "phone": getattr(e, "phone", ""), "office_id": e.office_id} for e in emps]
    cols = [{"name": n, "id": n} for n in ["id", "name", "phone", "office_id"]]
    return dash_table.DataTable(data=data, columns=cols, page_size=10, style_table={"overflowX":"auto"})

@app.callback(Output("emp-table", "children"), Input("url", "pathname"))
def list_employees(_):
    user = current_user()
    if not user or user.role != Role.OM:
        raise PreventUpdate
    return _render_emp_table_for_om(user)

# NOTE: Update table immediately after adding employee (req #2)
@app.callback(
    Output("emp-add-msg","children"),
    Output("emp-dialog","message"),
    Output("emp-dialog","displayed"),
    Output("emp-new-name","value"),
    Output("emp-new-phone","value"),
    Output("emp-new-username","value"),
    Output("emp-new-password","value"),
    Output("emp-table","children", allow_duplicate=True),
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
        return (html.Div("❌ Name, username and password are required.", className="message message-error"), "", False, name, phone, uname, pwd, _render_emp_table_for_om(user))
    with SessionLocal() as s:
        if s.query(User).filter(User.username == uname).first():
            return (html.Div("❌ Username already exists.", className="message message-error"), "", False, name, phone, uname, pwd, _render_emp_table_for_om(user))
        emp = Employee(name=name, office_id=user.office_id, username=uname)
        try: emp.phone = (phone or "").strip()
        except Exception: pass
        s.add(emp); s.flush()
        s.add(User(username=uname, password_hash=generate_password_hash(pwd),
                   role=Role.EMP, office_id=user.office_id))
        s.commit()
    # Clear fields, show dialog, and refresh table immediately
    return (html.Div("✅ Employee created successfully!", className="message message-success"), "Employee created and login set.", True, "", "", "", "", _render_emp_table_for_om(user))

# ---------- Offices (GM Only) ----------
@app.callback(Output("offices-table", "children"), Input("url", "pathname"))
@login_required(Role.GM)
def render_offices_table(_):
    """Display all offices with their details"""
    with SessionLocal() as s:
        offices = s.query(Office).order_by(Office.id).all()
        
        # Get manager names
        rows = []
        for office in offices:
            manager_name = ""
            if office.manager_id:
                emp = s.get(Employee, office.manager_id)
                if emp:
                    manager_name = emp.name
            
            rows.append({
                "office_id": office.id,
                "office_name": office.name,
                "location": office.location or "—",
                "manager_id": office.manager_id or "—",
                "manager_name": manager_name or "—"
            })
        
        cols = [
            {"name": "Office ID", "id": "office_id"},
            {"name": "Office Name", "id": "office_name"},
            {"name": "Location", "id": "location"},
            {"name": "Manager ID", "id": "manager_id"},
            {"name": "Manager Name", "id": "manager_name"},
        ]
        
        return dash_table.DataTable(
            data=rows, 
            columns=cols, 
            page_size=10, 
            style_table={"overflowX": "auto"},
            style_cell={
                'textAlign': 'left',
                'padding': '12px',
                'fontSize': '14px'
            },
            style_header={
                'fontWeight': 'bold',
                'backgroundColor': 'var(--bg)',
                'color': 'var(--text)'
            }
        )

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
    State("new-office-location","value"),
    prevent_initial_call=True
)
@login_required(Role.GM)
def add_office(n, office_name, location):
    name = (office_name or "").strip()
    loc = (location or "").strip() if location else None
    with SessionLocal() as s:
        if not name:
            offices = s.query(Office).order_by(Office.name).all()
            return html.Div("❌ Office name is required.", className="message message-error"), [{"label": o.name, "value": o.id} for o in offices]
        if s.query(Office).filter(Office.name.ilike(name)).first():
            offices = s.query(Office).order_by(Office.name).all()
            return html.Div("❌ Office already exists.", className="message message-error"), [{"label": o.name, "value": o.id} for o in offices]
        s.add(Office(name=name, location=loc))
        s.commit()
        offices = s.query(Office).order_by(Office.name).all()
    return html.Div("✅ Office created successfully!", className="message message-success"), [{"label": o.name, "value": o.id} for o in offices]

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
        return (html.Div("❌ All fields are required.", className="message message-error"), "", False, uname, pwd)
    with SessionLocal() as s:
        if not s.get(Office, office_id):
            return (html.Div("❌ Invalid office.", className="message message-error"), "", False, uname, pwd)
        if s.query(User).filter(User.username == uname).first():
            return (html.Div("❌ Username already exists.", className="message message-error"), "", False, uname, pwd)
        s.add(User(username=uname, password_hash=generate_password_hash(pwd), role=Role.OM, office_id=office_id))
        s.commit()
    return (html.Div("✅ Office Manager created successfully!", className="message message-success"), "Office Manager created successfully.", True, "", "")

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
        return html.Div("❌ Select an OM and enter a new password.", className="message message-error")
    with SessionLocal() as s:
        u = s.get(User, om_id)
        if not u or u.role != Role.OM:
            return html.Div("❌ Invalid OM selected.", className="message message-error")
        u.password_hash = generate_password_hash(new_pass)
        s.commit()
    return html.Div("✅ Password reset successfully!", className="message message-success")

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
                    html.Div(className="kpi", children=[html.Div("Company total cost", className="label"), html.Div(f"${company_cost:,.2f}", className="value")]),
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
            html.Div(className="kpi", children=[html.Div("Total cost for my office", className="label"), html.Div(f"${office_cost:,.2f}", className="value")]),
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
        return html.Div("❌ Select an employee and enter a remark.", className="message message-error")
    with SessionLocal() as s:
        s.add(Remark(author_user_id=user.id, target_type="EMPLOYEE", target_id=int(emp_id), content=(textv or "").strip()))
        s.commit()
    return html.Div("✅ Remark added successfully!", className="message message-success")

# ---------- Profile ----------
@app.callback(Output("profile-form", "children"), Input("url", "pathname"))
def load_profile(_):
    """
    Show employee's own info + ALL remarks addressed to that employee (req #3).
    """
    user = current_user()
    if not user:
        raise PreventUpdate
    with SessionLocal() as s:
        emp = _employee_for_user(user, s) if user.role == Role.EMP else None
        office = s.get(Office, user.office_id) if user.office_id else None

        # Gather remarks targeted to this employee (if exists)
        remarks_list = []
        if emp:
            rs = s.query(Remark).filter(
                Remark.target_type == "EMPLOYEE",
                Remark.target_id == emp.id
            ).order_by(Remark.created_at.desc()).all()
            for r in rs:
                ts = getattr(r, "created_at", None)
                ts_str = ts.strftime("%Y-%m-%d %H:%M") if ts else ""
                remarks_list.append(html.Li([
                    html.Span(f"{ts_str} — "),
                    html.Span(r.content or "")
                ]))

        remarks_block = html.Div([
            html.Div(className="hr"),
            html.H4("💬 Manager Remarks", style={"marginBottom": "16px"}),
            html.Ul(remarks_list, style={"paddingLeft": "20px"}) if remarks_list else html.Div(className="muted", children="No remarks from management yet.")
        ]) if emp else html.Div()

        return html.Div([
            html.Div(className="card", style={"background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "color": "white", "marginBottom": "20px"}, children=[
                html.Div(style={"fontSize": "18px", "fontWeight": "700", "marginBottom": "12px"}, children=f"👋 {user.username}"),
                html.Div(style={"display": "grid", "gridTemplateColumns": "repeat(auto-fit, minmax(200px, 1fr))", "gap": "12px"}, children=[
                    html.Div([
                        html.Div("Role", style={"fontSize": "12px", "opacity": "0.9", "marginBottom": "4px"}),
                        html.Div(role_name(user.role.value), style={"fontSize": "16px", "fontWeight": "600"})
                    ]),
                    html.Div([
                        html.Div("Employee ID", style={"fontSize": "12px", "opacity": "0.9", "marginBottom": "4px"}),
                        html.Div(emp.id if emp else '—', style={"fontSize": "16px", "fontWeight": "600"})
                    ]),
                    html.Div([
                        html.Div("Office", style={"fontSize": "12px", "opacity": "0.9", "marginBottom": "4px"}),
                        html.Div(office.name if office else '—', style={"fontSize": "16px", "fontWeight": "600"})
                    ]),
                ])
            ]),
            html.Div(className="form-group", children=[
                html.Label("Full Name *", className="form-label"),
                dcc.Input(id="profile-emp-name", placeholder="Enter your full name", value=(emp.name if emp else ""), className="input"),
            ]),
            html.Div(className="form-group", children=[
                html.Label("Phone Number", className="form-label"),
                dcc.Input(id="profile-phone", placeholder="Enter your phone number", value=getattr(emp, "phone", "") if emp else "", className="input"),
            ]),
            html.Button("💾 Save Profile", id="btn-save-profile", n_clicks=0, type="button", className="btn"),
            remarks_block
        ])

# No popup on visiting profile; after saving also DO NOT show popup (req #5)
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
        return "", False, html.Div("❌ Name is required.", className="message message-error")
    with SessionLocal() as s:
        emp = _employee_for_user(user, s)
        if not emp:
            return "", False, html.Div("❌ No employee record.", className="message message-error")
        emp.name = name
        try: emp.phone = phone
        except Exception: pass
        s.commit()
    # No modal; just a small status message
    return "", False, html.Div("✅ Profile updated successfully!", className="message message-success")

# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)


