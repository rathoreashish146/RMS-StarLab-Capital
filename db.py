
# ==========================================================================================================================================================================================================


# db.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Enum, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import text
import enum, os, datetime

# Get DATABASE_URL from environment (Render sets this automatically)
DB_PATH = os.environ.get("DATABASE_URL")

# Handle Render's postgres:// format (convert to postgresql://)
if DB_PATH and DB_PATH.startswith("postgres://"):
    DB_PATH = DB_PATH.replace("postgres://", "postgresql://", 1)

# If DATABASE_URL is not set, raise an error with helpful message
if not DB_PATH:
    raise ValueError(
        "DATABASE_URL environment variable is not set. "
        "Please configure your database connection string in Render dashboard."
    )

# ensure psycopg2-binary is installed
# Add connection pool settings for better reliability on Render
engine = create_engine(
    DB_PATH,
    echo=False,
    future=True,
    pool_pre_ping=True,  # Verify connections before using
    pool_recycle=3600,   # Recycle connections after 1 hour
    pool_size=10,        # Number of connections to maintain
    max_overflow=20      # Max connections beyond pool_size
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


class Role(str, enum.Enum):
    GM = "GM"
    OM = "OM"
    EMP = "EMP"

class AllocationType(str, enum.Enum):
    EMPLOYEE = "EMPLOYEE"
    OFFICE = "OFFICE"
    UNALLOCATED = "UNALLOCATED"

class RequestStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    RETURN_PENDING = "RETURN_PENDING"
    RETURNED = "RETURNED"

class Office(Base):
    __tablename__ = "offices"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    location = Column(String, nullable=True)  # Optional: city / branch / building
    manager_id = Column(Integer, nullable=True)  # Optional: employee_id of the Office Manager
    employees = relationship("Employee", back_populates="office")
    users = relationship("User", back_populates="office")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(Enum(Role), nullable=False)
    office_id = Column(Integer, ForeignKey("offices.id"), nullable=True)  # GM null; OM scoped; EMP office
    office = relationship("Office", back_populates="users")

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, nullable=True)  # Login username
    role = Column(Enum(Role), nullable=True)  # GM / OM / EMP
    office_id = Column(Integer, ForeignKey("offices.id"))
    office = relationship("Office", back_populates="employees")
    phone = Column(String, nullable=True)

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, default=0)
    quantity = Column(Integer, default=1)
    bill_path = Column(String, nullable=True)
    allocation_type = Column(Enum(AllocationType), default=AllocationType.UNALLOCATED)
    allocation_id = Column(Integer, nullable=True)  # employee_id or office_id
    returned = Column(Boolean, default=False)

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    office_id = Column(Integer, ForeignKey("offices.id"))
    asset_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    price = Column(Float, default=0)          # NEW: optional price
    bill_path = Column(String, nullable=True) # NEW: optional bill
    status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
    approver_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    remark = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Remark(Base):
    __tablename__ = "remarks"
    id = Column(Integer, primary_key=True)
    author_user_id = Column(Integer, ForeignKey("users.id"))
    target_type = Column(String)  # "EMPLOYEE" | "OFFICE" | "REQUEST" | "ASSET"
    target_id = Column(Integer)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

def _safe_add_column(conn, table, coldef):
    # PostgreSQL-compatible column check
    colname = coldef.split()[0]
    result = conn.execute(text("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = :table_name AND column_name = :col_name
    """), {"table_name": table, "col_name": colname}).fetchone()
    if not result:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {coldef}"))


def init_db(seed=False):
    Base.metadata.create_all(engine)

    if not seed:
        return

    from werkzeug.security import generate_password_hash
    with SessionLocal() as s:
        # ---- Skip seeding if offices already exist ----
        if s.query(Office).first():
            print("Database already seeded — skipping.")
            return

        # --- Offices ---
        cnel = Office(name="Cloud Nebula Enterprises Lucknow")
        psace = Office(name="Prof. Shamim Ahmad AI Centre of Excellence")
        s.add_all([cnel, psace])
        s.flush()  # populate IDs

        # --- Users (GM + OMs) ---
        gm_faisal = User(
            username="faisal",
            password_hash=generate_password_hash("faisal@51020"),
            role=Role.GM,
            office_id=None
        )
        om_mahtab_cnel = User(
            username="mahtab",
            password_hash=generate_password_hash("mahtab@51020"),
            role=Role.OM,
            office_id=cnel.id
        )
        om_mahtab_psace = User(
            username="mahtab_ai",
            password_hash=generate_password_hash("mahtab@51020"),
            role=Role.OM,
            office_id=psace.id
        )
        s.add_all([gm_faisal, om_mahtab_cnel, om_mahtab_psace])
        s.flush()

        # --- Employees + corresponding Users ---
        employees_cnel = [
            {"name": "Mohd Rehbar", "username": "mohd_rehbar"},
            {"name": "Mohd Yousuf Khan", "username": "mohd_yousuf"},
            {"name": "Nawab Shahzeb Uddin", "username": "nawab_shahzeb"},
            {"name": "Haider Ali", "username": "haider_ali"},
        ]
        employees_psace = [
            {"name": "Mahtab Alam", "username": "mahtab_alam"},
            {"name": "Vikalp Varshney", "username": "vikalp_varshney"},
            {"name": "Imaad Hasan", "username": "imaad_hasan"},
            {"name": "Ashish", "username": "ashish"},
            {"name": "Waqarul Hasan", "username": "waqarul_hasan"},
        ]

        def _add_emp_with_user(emp_def, office_id):
            uname = emp_def["username"]
            emp = Employee(name=emp_def["name"], office_id=office_id, username=uname, role=Role.EMP)
            s.add(emp)
            pwd = f"{uname}@51020"
            user = User(username=uname, password_hash=generate_password_hash(pwd),
                        role=Role.EMP, office_id=office_id)
            s.add(user)

        for e in employees_cnel:
            _add_emp_with_user(e, cnel.id)
        for e in employees_psace:
            _add_emp_with_user(e, psace.id)

        s.commit()
        print("✅ Seeded initial offices, users, and employees.")


# # ==========================================================================================================================================================================================================


# # db.py
# from sqlalchemy import create_engine, Column, Integer, String, Float, Enum, ForeignKey, Boolean, DateTime, Text
# from sqlalchemy.orm import declarative_base, relationship, sessionmaker
# from sqlalchemy import text
# import enum, os, datetime

# DB_PATH = os.environ.get(
#     "DATABASE_URL",
#     "postgresql://rms_38f2_user:h2XOIhTv7TQXvz72E5GuJgFx50S6QgHf@dpg-d44oeffgi27c73aeg36g-a/rms_38f2"
# )
# # ensure psycopg2-binary is installed
# engine = create_engine(DB_PATH, echo=False, future=True)
# SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
# Base = declarative_base()


# class Role(str, enum.Enum):
#     GM = "GM"
#     OM = "OM"
#     EMP = "EMP"

# class AllocationType(str, enum.Enum):
#     EMPLOYEE = "EMPLOYEE"
#     OFFICE = "OFFICE"
#     UNALLOCATED = "UNALLOCATED"

# class RequestStatus(str, enum.Enum):
#     PENDING = "PENDING"
#     APPROVED = "APPROVED"
#     REJECTED = "REJECTED"
#     RETURN_PENDING = "RETURN_PENDING"
#     RETURNED = "RETURNED"

# class Office(Base):
#     __tablename__ = "offices"
#     id = Column(Integer, primary_key=True)
#     name = Column(String, unique=True, nullable=False)
#     location = Column(String, nullable=True)  # Optional: city / branch / building
#     manager_id = Column(Integer, nullable=True)  # Optional: employee_id of the Office Manager
#     employees = relationship("Employee", back_populates="office")
#     users = relationship("User", back_populates="office")

# class User(Base):
#     __tablename__ = "users"
#     id = Column(Integer, primary_key=True)
#     username = Column(String, unique=True, nullable=False)
#     password_hash = Column(String, nullable=False)
#     role = Column(Enum(Role), nullable=False)
#     office_id = Column(Integer, ForeignKey("offices.id"), nullable=True)  # GM null; OM scoped; EMP office
#     office = relationship("Office", back_populates="users")

# class Employee(Base):
#     __tablename__ = "employees"
#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)
#     username = Column(String, unique=True, nullable=True)  # Login username
#     role = Column(Enum(Role), nullable=True)  # GM / OM / EMP
#     office_id = Column(Integer, ForeignKey("offices.id"))
#     office = relationship("Office", back_populates="employees")
#     phone = Column(String, nullable=True)

# class Asset(Base):
#     __tablename__ = "assets"
#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)
#     price = Column(Float, default=0)
#     quantity = Column(Integer, default=1)
#     bill_path = Column(String, nullable=True)
#     allocation_type = Column(Enum(AllocationType), default=AllocationType.UNALLOCATED)
#     allocation_id = Column(Integer, nullable=True)  # employee_id or office_id
#     returned = Column(Boolean, default=False)

# class Request(Base):
#     __tablename__ = "requests"
#     id = Column(Integer, primary_key=True)
#     employee_id = Column(Integer, ForeignKey("employees.id"))
#     office_id = Column(Integer, ForeignKey("offices.id"))
#     asset_name = Column(String, nullable=False)
#     quantity = Column(Integer, default=1)
#     price = Column(Float, default=0)          # NEW: optional price
#     bill_path = Column(String, nullable=True) # NEW: optional bill
#     status = Column(Enum(RequestStatus), default=RequestStatus.PENDING)
#     approver_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
#     remark = Column(Text, nullable=True)
#     created_at = Column(DateTime, default=datetime.datetime.utcnow)

# class Remark(Base):
#     __tablename__ = "remarks"
#     id = Column(Integer, primary_key=True)
#     author_user_id = Column(Integer, ForeignKey("users.id"))
#     target_type = Column(String)  # "EMPLOYEE" | "OFFICE" | "REQUEST" | "ASSET"
#     target_id = Column(Integer)
#     content = Column(Text)
#     created_at = Column(DateTime, default=datetime.datetime.utcnow)

# def _safe_add_column(conn, table, coldef):
#     cols = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
#     names = {c[1] for c in cols}
#     colname = coldef.split()[0]
#     if colname not in names:
#         conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {coldef}"))


# def init_db(seed=False):
#     Base.metadata.create_all(engine)

#     if not seed:
#         return

#     from werkzeug.security import generate_password_hash
#     with SessionLocal() as s:
#         # ---- Skip seeding if offices already exist ----
#         if s.query(Office).first():
#             print("Database already seeded — skipping.")
#             return

#         # --- Offices ---
#         cnel = Office(name="Cloud Nebula Enterprises Lucknow")
#         psace = Office(name="Prof. Shamim Ahmad AI Centre of Excellence")
#         s.add_all([cnel, psace])
#         s.flush()  # populate IDs

#         # --- Users (GM + OMs) ---
#         gm_faisal = User(
#             username="faisal",
#             password_hash=generate_password_hash("faisal@51020"),
#             role=Role.GM,
#             office_id=None
#         )
#         om_mahtab_cnel = User(
#             username="mahtab",
#             password_hash=generate_password_hash("mahtab@51020"),
#             role=Role.OM,
#             office_id=cnel.id
#         )
#         om_mahtab_psace = User(
#             username="mahtab_ai",
#             password_hash=generate_password_hash("mahtab@51020"),
#             role=Role.OM,
#             office_id=psace.id
#         )
#         s.add_all([gm_faisal, om_mahtab_cnel, om_mahtab_psace])
#         s.flush()

#         # --- Employees + corresponding Users ---
#         employees_cnel = [
#             {"name": "Mohd Rehbar", "username": "mohd_rehbar"},
#             {"name": "Mohd Yousuf Khan", "username": "mohd_yousuf"},
#             {"name": "Nawab Shahzeb Uddin", "username": "nawab_shahzeb"},
#             {"name": "Haider Ali", "username": "haider_ali"},
#         ]
#         employees_psace = [
#             {"name": "Mahtab Alam", "username": "mahtab_alam"},
#             {"name": "Vikalp Varshney", "username": "vikalp_varshney"},
#             {"name": "Imaad Hasan", "username": "imaad_hasan"},
#             {"name": "Ashish", "username": "ashish"},
#             {"name": "Waqarul Hasan", "username": "waqarul_hasan"},
#         ]

#         def _add_emp_with_user(emp_def, office_id):
#             uname = emp_def["username"]
#             emp = Employee(name=emp_def["name"], office_id=office_id, username=uname, role=Role.EMP)
#             s.add(emp)
#             pwd = f"{uname}@51020"
#             user = User(username=uname, password_hash=generate_password_hash(pwd),
#                         role=Role.EMP, office_id=office_id)
#             s.add(user)

#         for e in employees_cnel:
#             _add_emp_with_user(e, cnel.id)
#         for e in employees_psace:
#             _add_emp_with_user(e, psace.id)

#         s.commit()
#         print("✅ Seeded initial offices, users, and employees.")

