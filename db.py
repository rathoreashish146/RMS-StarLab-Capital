# db.py
from sqlalchemy import create_engine, Column, Integer, String, Float, Enum, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import text
import enum, os, datetime

DB_PATH = os.environ.get("RMS_DB_PATH", "rms.db")
# Safer for threaded servers if needed:
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True, connect_args={"check_same_thread": False})
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
    office_id = Column(Integer, ForeignKey("offices.id"))
    office = relationship("Office", back_populates="employees")
    phone = Column(String, nullable=True)
    username = Column(String, unique=True, nullable=True)  # links to users.username

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
    cols = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    names = {c[1] for c in cols}
    colname = coldef.split()[0]
    if colname not in names:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {coldef}"))

# def init_db(seed=False):
#     Base.metadata.create_all(engine)
#     # lightweight migrations for old DBs
#     try:
#         with engine.begin() as conn:
#             _safe_add_column(conn, "employees", "phone VARCHAR")
#             _safe_add_column(conn, "employees", "username VARCHAR")
#             _safe_add_column(conn, "requests", "price FLOAT")
#             _safe_add_column(conn, "requests", "bill_path VARCHAR")
#     except Exception:
#         pass

#     if seed:
#         from werkzeug.security import generate_password_hash
#         with SessionLocal() as s:
#             if not s.query(Office).first():
#                 east = Office(name="East")
#                 west = Office(name="West")
#                 s.add_all([east, west]); s.flush()
#                 # Users
#                 admin = User(username="admin", password_hash=generate_password_hash("admin"), role=Role.GM)
#                 om_east = User(username="om_east", password_hash=generate_password_hash("om_east"), role=Role.OM, office_id=east.id)
#                 emp_user = User(username="alice", password_hash=generate_password_hash("alice"), role=Role.EMP, office_id=east.id)
#                 s.add_all([admin, om_east, emp_user])
#                 # Employees
#                 alice = Employee(name="Alice", office_id=east.id, username="alice", phone="9999999999")
#                 bob = Employee(name="Bob", office_id=west.id, username=None)
#                 s.add_all([alice, bob])
#                 # Assets
#                 laptop = Asset(name="Laptop", price=1200, quantity=5)
#                 chair = Asset(name="Chair", price=100, quantity=20, allocation_type=AllocationType.OFFICE, allocation_id=east.id)
#                 s.add_all([laptop, chair])
#                 # Sample Request with price
#                 r1 = Request(employee_id=1, office_id=east.id, asset_name="Laptop", quantity=1, price=1200)
#                 s.add(r1)
#             s.commit()
def init_db(seed=False):
    Base.metadata.create_all(engine)
    # lightweight migrations for old DBs
    try:
        with engine.begin() as conn:
            _safe_add_column(conn, "employees", "phone VARCHAR")
            _safe_add_column(conn, "employees", "username VARCHAR")
            _safe_add_column(conn, "requests", "price FLOAT")
            _safe_add_column(conn, "requests", "bill_path VARCHAR")
    except Exception:
        pass

    if seed:
        from werkzeug.security import generate_password_hash
        with SessionLocal() as s:
            # --- Offices ---
            cnel = Office(name="Cloud Nebula Enterprises Lucknow")
            psace = Office(name="Prof. Shamim Ahmad AI Centre of Excellence")
            s.add_all([cnel, psace])
            s.flush()  # populate IDs

            # --- Users (GM + OMs) ---
            # GM
            gm_faisal = User(
                username="faisal",
                password_hash=generate_password_hash("faisal@51020"),
                role=Role.GM,
                office_id=None
            )

            # OM for CNEL
            om_mahtab_cnel = User(
                username="mahtab",
                password_hash=generate_password_hash("mahtab@51020"),
                role=Role.OM,
                office_id=cnel.id
            )

            # OM for PSACE (same person, separate account due to schema limits)
            om_mahtab_psace = User(
                username="mahtab_ai",
                password_hash=generate_password_hash("mahtab@51020"),
                role=Role.OM,
                office_id=psace.id
            )

            s.add_all([gm_faisal, om_mahtab_cnel, om_mahtab_psace])
            s.flush()

            # --- Employees + corresponding User accounts ---
            # Cloud Nebula Enterprises Lucknow employees
            employees_cnel = [
                {"name": "Mohd Rehbar", "username": "mohd_rehbar"},
                {"name": "Mohd Yousuf Khan", "username": "mohd_yousuf"},
                {"name": "Nawab Shahzeb Uddin", "username": "nawab_shahzeb"},
                {"name": "Haider Ali", "username": "haider_ali"},
            ]

            # Prof. Shamim Ahmad AI Centre of Excellence employees
            employees_psace = [
                {"name": "Mahtab Alam", "username": "mahtab_alam"},  # avoids collision with OM 'mahtab'
                {"name": "Vikalp Varshney", "username": "vikalp_varshney"},
                {"name": "Imaad Hasan", "username": "imaad_hasan"},
                {"name": "Ashish", "username": "ashish"},
                {"name": "Waqarul Hasan", "username": "waqarul_hasan"},
            ]

            # Helper: add employee + matching user account
            def _add_emp_with_user(emp_def, office_id):
                uname = emp_def["username"]
                # create Employee
                emp = Employee(name=emp_def["name"], office_id=office_id, username=uname)
                s.add(emp)
                # create User for that employee (role=EMP) with password "<username>@51020"
                pwd = f"{uname}@51020"
                user = User(username=uname, password_hash=generate_password_hash(pwd), role=Role.EMP, office_id=office_id)
                s.add(user)

            for e in employees_cnel:
                _add_emp_with_user(e, cnel.id)

            for e in employees_psace:
                _add_emp_with_user(e, psace.id)

            # Commit seeded data
            s.commit()
