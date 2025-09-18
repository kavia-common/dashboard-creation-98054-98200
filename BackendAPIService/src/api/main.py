import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import bcrypt
import jwt
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    Security,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)
from pydantic import BaseModel, EmailStr, Field
from pydantic_settings import BaseSettings
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, relationship, sessionmaker

# ------------------------------------------------------------------------------
# Configuration and Settings
# ------------------------------------------------------------------------------


class Settings(BaseSettings):
    """Application settings sourced from environment variables.

    Notes:
    - In production, set DATABASE_URL and JWT_SECRET_KEY via env/Compose/Secrets.
    - For local/dev containers, we default to SQLite and a generated dev secret
      so the service can boot and pass healthchecks even if envs are not provided.
    """

    APP_NAME: str = "Dashboard Backend API"
    APP_DESCRIPTION: str = (
        "FastAPI backend providing JWT authentication, CRUD operations for users and reports, "
        "and chart/dashboard endpoints. Uses SQLAlchemy with PostgreSQL, "
        "bcrypt for password hashing."
    )
    APP_VERSION: str = "1.0.0"

    # Database URL, e.g. postgresql+psycopg2://user:pass@host:5432/dbname
    # Default to local SQLite in container for dev to avoid crash when env is missing.
    DATABASE_URL: str = Field(
        default="sqlite:///./app.db",
        description="SQLAlchemy database URL (PostgreSQL recommended in production).",
    )

    # JWT settings
    # WARNING: Default key is for development only; override via env in production.
    JWT_SECRET_KEY: str = Field(
        default=os.getenv("JWT_SECRET_KEY", "insecure-dev-secret-change-me"),
        description="Secret key for signing JWTs",
    )
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRES_MINUTES: int = 60

    # CORS
    CORS_ALLOW_ORIGINS: List[str] = ["*"]
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()  # Reads from environment and uses safe dev defaults

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------

logger = logging.getLogger("backend")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# ------------------------------------------------------------------------------
# Database setup (SQLAlchemy)
# ------------------------------------------------------------------------------

Base = declarative_base()

# Create engine
# If using SQLite, set check_same_thread for SQLAlchemy+SQLite in single-threaded context.
engine_kwargs: Dict[str, Any] = {"pool_pre_ping": True, "future": True}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs.update({"connect_args": {"check_same_thread": False}})

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Log minimal non-sensitive startup info
try:
    from sqlalchemy.engine.url import make_url
    _url = make_url(settings.DATABASE_URL)
    logger.info(
        "Starting BackendAPIService v%s using DB dialect=%s",
        settings.APP_VERSION,
        _url.get_dialect().name,
    )
except Exception:
    logger.info("Starting BackendAPIService (database URL parsing failed).")


def get_db():
    """Yield a database session and ensure closing."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ------------------------------------------------------------------------------
# Models
# ------------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(320), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    reports = relationship("Report", back_populates="owner", cascade="all, delete-orphan")


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User", back_populates="reports")


# ------------------------------------------------------------------------------
# Security Helpers (bcrypt + JWT)
# ------------------------------------------------------------------------------

def hash_password(plain_password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(plain_password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        # Do not reveal details
        return False


def create_access_token(subject: Dict[str, Any], expires_minutes: Optional[int] = None) -> str:
    """Create a JWT access token."""
    expire = datetime.utcnow() + timedelta(
        minutes=expires_minutes if expires_minutes is not None else settings.JWT_EXPIRES_MINUTES
    )
    to_encode = {"exp": expire, "sub": subject}
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload  # contains "sub" and "exp"
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")


bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Dependency to retrieve the current authenticated user.

    Expects a Bearer token and validates it. Raises 401 on failure.
    """
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated.")
    token = credentials.credentials
    payload = decode_access_token(token)
    sub = payload.get("sub") or {}
    email = sub.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token.")
    return user


# ------------------------------------------------------------------------------
# Schemas (Pydantic)
# ------------------------------------------------------------------------------

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="Unique user email")
    full_name: Optional[str] = Field(None, description="Full name")
    password: str = Field(..., min_length=6, description="Password")
    role: str = Field(default="user", description="User role")


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, description="Full name")
    password: Optional[str] = Field(None, min_length=6, description="New password")
    role: Optional[str] = Field(None, description="User role")


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: Optional[str]
    role: str
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class ReportCreate(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = Field(None)
    owner_id: Optional[int] = Field(None, description="Owner user ID (admin may set)")


class ReportUpdate(BaseModel):
    title: Optional[str] = Field(None)
    description: Optional[str] = Field(None)


class ReportOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    owner_id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# ------------------------------------------------------------------------------
# FastAPI App and Middleware
# ------------------------------------------------------------------------------

openapi_tags = [
    {"name": "auth", "description": "Authentication and token management"},
    {"name": "users", "description": "User management CRUD operations"},
    {"name": "reports", "description": "Report management CRUD operations"},
    {"name": "charts", "description": "Chart data"},
    {"name": "dashboard", "description": "Dashboard data"},
    {"name": "health", "description": "Health checks"},
]

app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    openapi_tags=openapi_tags,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)


# ------------------------------------------------------------------------------
# Startup: create tables and seed admin if missing
# ------------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    """
    Initialize database tables and create a default admin if no users exist.

    Uses environment variables:
    - ADMIN_EMAIL (optional, default admin@example.com)
    - ADMIN_PASSWORD (optional, default 'admin123!')
    """
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        any_user = db.query(User).first()
        if not any_user:
            admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com")
            admin_password = os.getenv("ADMIN_PASSWORD", "admin123!")
            admin = User(
                email=admin_email,
                full_name="Administrator",
                password_hash=hash_password(admin_password),
                role="admin",
            )
            db.add(admin)
            db.commit()
            logger.info("Seeded initial admin user.")
    except Exception:
        # Do not expose sensitive details
        logger.error("Startup initialization failed.")
    finally:
        db.close()


# ------------------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------------------

@app.get("/", tags=["health"], summary="Health Check")
def health_check():
    """Simple health check endpoint."""
    return {"message": "Healthy"}


# PUBLIC_INTERFACE
@app.post(
    "/login",
    response_model=TokenResponse,
    tags=["auth"],
    summary="Login",
    responses={
        200: {"description": "Authenticated"},
        401: {"description": "Invalid credentials"},
    },
)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    """
    Authenticate a user with email and password and return a JWT token.

    Request body:
    - email: user's email
    - password: user's password

    Returns:
    - access_token: JWT token with subject containing user email and id
    - token_type: 'bearer'

    Security: No token required.
    """
    # Avoid leaking which part failed
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        # Always same error to avoid info leakage
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")
    token = create_access_token({"id": user.id, "email": user.email, "role": user.role})
    return TokenResponse(access_token=token, token_type="bearer")


# ----------------------------- Users CRUD -------------------------------------

# PUBLIC_INTERFACE
@app.get(
    "/users",
    response_model=List[UserOut],
    tags=["users"],
    summary="List users",
)
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """List users with optional search query on email or full_name."""
    query = db.query(User)
    if q:
        like = f"%{q}%"
        query = query.filter((User.email.ilike(like)) | (User.full_name.ilike(like)))
    users = query.order_by(User.created_at.desc()).offset(skip).limit(min(limit, 200)).all()
    return users


# PUBLIC_INTERFACE
@app.post(
    "/users",
    response_model=UserOut,
    tags=["users"],
    summary="Create user",
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new user. Only admins can set role different from 'user'."""
    # Basic role control; can be extended to full RBAC later
    role_to_set = payload.role if current_user.role == "admin" else "user"
    new_user = User(
        email=payload.email,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=role_to_set,
    )
    db.add(new_user)
    try:
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email already exists.")
    return new_user


# PUBLIC_INTERFACE
@app.put(
    "/users/{user_id}",
    response_model=UserOut,
    tags=["users"],
    summary="Update user",
)
def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a user's information. Allow password change and role by admin."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.password:
        user.password_hash = hash_password(payload.password)
    if payload.role and current_user.role == "admin":
        user.role = payload.role

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Update failed.")
    return user


# PUBLIC_INTERFACE
@app.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["users"],
    summary="Delete user",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a user by ID. Only admins or self can delete account."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Forbidden.")
    db.delete(user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------- Reports CRUD -----------------------------------

# PUBLIC_INTERFACE
@app.get(
    "/reports",
    response_model=List[ReportOut],
    tags=["reports"],
    summary="List reports",
)
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    owner_id: Optional[int] = None,
    q: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
):
    """List reports, optionally filtering by owner_id or search query."""
    query = db.query(Report)
    if owner_id:
        query = query.filter(Report.owner_id == owner_id)
    if q:
        like = f"%{q}%"
        query = query.filter((Report.title.ilike(like)) | (Report.description.ilike(like)))
    items = query.order_by(Report.created_at.desc()).offset(skip).limit(min(limit, 200)).all()
    return items


# PUBLIC_INTERFACE
@app.post(
    "/reports",
    response_model=ReportOut,
    tags=["reports"],
    summary="Create report",
    status_code=status.HTTP_201_CREATED,
)
def create_report(
    payload: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new report. Default owner is current user unless admin sets owner_id."""
    owner_id = (
        payload.owner_id
        if (payload.owner_id and current_user.role == "admin")
        else current_user.id
    )
    new_item = Report(title=payload.title, description=payload.description, owner_id=owner_id)
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    return new_item


# PUBLIC_INTERFACE
@app.put(
    "/reports/{report_id}",
    response_model=ReportOut,
    tags=["reports"],
    summary="Update report",
)
def update_report(
    report_id: int,
    payload: ReportUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a report. Only owners or admins can update."""
    item = db.query(Report).filter(Report.id == report_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Report not found.")
    if current_user.role != "admin" and item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden.")

    if payload.title is not None:
        item.title = payload.title
    if payload.description is not None:
        item.description = payload.description

    db.commit()
    db.refresh(item)
    return item


# PUBLIC_INTERFACE
@app.delete(
    "/reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["reports"],
    summary="Delete report",
)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a report. Only owners or admins can delete."""
    item = db.query(Report).filter(Report.id == report_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Report not found.")
    if current_user.role != "admin" and item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden.")
    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ----------------------------- Chart & Dashboard -------------------------------

class ChartDataResponse(BaseModel):
    line: Dict[str, Any]
    bar: Dict[str, Any]
    pie: Dict[str, Any]


# PUBLIC_INTERFACE
@app.get(
    "/charts/data",
    response_model=ChartDataResponse,
    tags=["charts"],
    summary="Get chart data",
    description=(
        "Returns sample data for Line, Bar, and Pie charts suitable for "
        "Chart.js or Recharts."
    ),
)
def get_chart_data(current_user: User = Depends(get_current_user)) -> ChartDataResponse:
    """
    Provide dummy chart data. Protected by JWT.

    Returns datasets with labels and values.
    """
    line = {
        "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "datasets": [
            {"label": "Visitors", "data": [120, 150, 170, 160, 180, 220, 200]},
            {"label": "Signups", "data": [12, 18, 15, 20, 22, 30, 25]},
        ],
    }
    bar = {
        "labels": ["Q1", "Q2", "Q3", "Q4"],
        "datasets": [{"label": "Revenue", "data": [30000, 45000, 50000, 65000]}],
    }
    pie = {
        "labels": ["Product A", "Product B", "Product C"],
        "datasets": [{"data": [45, 30, 25]}],
    }
    return ChartDataResponse(line=line, bar=bar, pie=pie)


class DashboardResponse(BaseModel):
    users_count: int
    reports_count: int
    recent_reports: List[ReportOut]


# PUBLIC_INTERFACE
@app.get(
    "/dashboard",
    response_model=DashboardResponse,
    tags=["dashboard"],
    summary="Get dashboard overview",
)
def get_dashboard(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Return aggregated dashboard data. Protected by JWT.

    Provides simple counts and latest reports.
    """
    users_count = db.query(User).count()
    reports_count = db.query(Report).count()
    recent = db.query(Report).order_by(Report.created_at.desc()).limit(5).all()
    return DashboardResponse(
        users_count=users_count,
        reports_count=reports_count,
        recent_reports=recent,
    )


# ------------------------------------------------------------------------------
# Error Handling
# ------------------------------------------------------------------------------

@app.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    # Avoid logging sensitive details; log minimal info
    logger.warning(f"HTTP {exc.status_code} at {request.url.path}")
    return Response(
        content='{"detail":"%s"}' % exc.detail,
        status_code=exc.status_code,
        media_type="application/json",
    )


@app.exception_handler(Exception)
def unhandled_exception_handler(request: Request, exc: Exception):
    # Do not leak details; generic message
    logger.error(f"Unhandled error at {request.url.path}")
    return Response(
        content='{"detail":"Internal server error."}',
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        media_type="application/json",
    )
