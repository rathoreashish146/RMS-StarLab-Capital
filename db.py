from sqlalchemy import create_engine, Column, Integer, String, Float, Enum, ForeignKey, Boolean, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
import enum, os, datetime
from sqlalchemy import text

DB_PATH = os.environ.get("RMS_DB_PATH", "rms.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

class Role(str, enum.Enum):
    GM = "GM"        # General Manager
    OM = "OM"        # Office Manager
    EMP = "EMP"      # Employee

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
    # new fields (kept nullable for smooth migration)
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
    allocation_id = Column(Integer, nullable=True)  # employee_id or office_id depending on type
    returned = Column(Boolean, default=False)

class Request(Base):
    __tablename__ = "requests"
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employees.id"))
    office_id = Column(Integer, ForeignKey("offices.id"))
    asset_name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
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
    # SQLite: add column only if not exists
    cols = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
    names = {c[1] for c in cols}
    colname = coldef.split()[0]
    if colname not in names:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {coldef}"))

def init_db(seed=False):
    Base.metadata.create_all(engine)

    # lightweight migrations for old DBs
    try:
        with engine.begin() as conn:
            _safe_add_column(conn, "employees", "phone VARCHAR")
            # no UNIQUE here to avoid ALTER errors; SQLAlchemy model still marks unique=True
            _safe_add_column(conn, "employees", "username VARCHAR")
    except Exception:
        pass

    if seed:
        from werkzeug.security import generate_password_hash
        with SessionLocal() as s:
            if not s.query(Office).first():
                east = Office(name="East")
                west = Office(name="West")
                s.add_all([east, west]); s.flush()
                # Users
                admin = User(username="admin", password_hash=generate_password_hash("admin"), role=Role.GM)
                om_east = User(username="om_east", password_hash=generate_password_hash("om_east"), role=Role.OM, office_id=east.id)
                emp_user = User(username="alice", password_hash=generate_password_hash("alice"), role=Role.EMP, office_id=east.id)
                s.add_all([admin, om_east, emp_user])
                # Employees (link usernames)
                alice = Employee(name="Alice", office_id=east.id, username="alice", phone="9999999999")
                bob = Employee(name="Bob", office_id=west.id, username=None)
                s.add_all([alice, bob])
                # Assets
                laptop = Asset(name="Laptop", price=1200, quantity=5)
                chair = Asset(name="Chair", price=100, quantity=20, allocation_type=AllocationType.OFFICE, allocation_id=east.id)
                s.add_all([laptop, chair])
                # Request sample
                r1 = Request(employee_id=1, office_id=east.id, asset_name="Laptop", quantity=1)
                s.add(r1)
            s.commit()
