import threading
from typing import Dict, List, Optional, Tuple

from .schemas import User, UserCreate, UserUpdate, Report, ReportCreate, ReportUpdate
from .security import hash_password
from .config import get_settings

_settings = get_settings()


class _IdGen:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._next = 1

    def next(self) -> int:
        with self._lock:
            nid = self._next
            self._next += 1
            return nid


class UsersRepository:
    """Thread-safe in-memory users repository (for demo)."""
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._id_gen = _IdGen()
        self._by_id: Dict[int, User] = {}
        self._by_email: Dict[str, int] = {}
        self._seed_admin()

    def _seed_admin(self) -> None:
        # Normalize email to lowercase for consistent indexing
        email = _settings.DEMO_ADMIN_EMAIL.lower()
        if email in self._by_email:
            return
        password_hash = _settings.DEMO_ADMIN_PASSWORD_HASH or hash_password("Admin@12345")
        user = User(id=self._id_gen.next(), email=email, full_name="Administrator", is_active=True)
        with self._lock:
            self._by_id[user.id] = user
            self._by_email[email] = user.id
        # store password hash separately
        setattr(self, "_passwords", getattr(self, "_passwords", {}))
        self._passwords[user.id] = password_hash

    def get_password_hash(self, user_id: int) -> Optional[str]:
        return getattr(self, "_passwords", {}).get(user_id)

    def get_by_email(self, email: str) -> Optional[User]:
        with self._lock:
            uid = self._by_email.get(email.lower())
            return self._by_id.get(uid) if uid else None

    def get(self, user_id: int) -> Optional[User]:
        with self._lock:
            return self._by_id.get(user_id)

    def list(self, page: int, size: int, search: Optional[str]) -> Tuple[List[User], int]:
        with self._lock:
            users = list(self._by_id.values())
        if search:
            s = search.lower()
            users = [u for u in users if s in u.email.lower() or (u.full_name or "").lower().find(s) >= 0]
        total = len(users)
        start = (page - 1) * size
        end = start + size
        return users[start:end], total

    def create(self, data: UserCreate) -> User:
        with self._lock:
            if data.email.lower() in self._by_email:
                raise ValueError("Email already exists")
            user = User(
                id=self._id_gen.next(),
                email=data.email.lower(),
                full_name=data.full_name,
                is_active=True,
            )
            self._by_id[user.id] = user
            self._by_email[user.email] = user.id
            setattr(self, "_passwords", getattr(self, "_passwords", {}))
            self._passwords[user.id] = hash_password(data.password)
            return user

    def update(self, user_id: int, data: UserUpdate) -> Optional[User]:
        with self._lock:
            user = self._by_id.get(user_id)
            if not user:
                return None
            if data.email and data.email.lower() != user.email:
                if data.email.lower() in self._by_email:
                    raise ValueError("Email already exists")
                # update indices
                del self._by_email[user.email]
                user.email = data.email.lower()
                self._by_email[user.email] = user.id
            if data.full_name is not None:
                user.full_name = data.full_name
            if data.password:
                setattr(self, "_passwords", getattr(self, "_passwords", {}))
                self._passwords[user.id] = hash_password(data.password)
            self._by_id[user.id] = user
            return user

    def delete(self, user_id: int) -> bool:
        with self._lock:
            user = self._by_id.pop(user_id, None)
            if not user:
                return False
            self._by_email.pop(user.email, None)
            getattr(self, "_passwords", {}).pop(user_id, None)
            return True


class ReportsRepository:
    """Thread-safe in-memory reports repository (for demo)."""
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._id_gen = _IdGen()
        self._by_id: Dict[int, Report] = {}

        # Seed some sample reports
        self.create(ReportCreate(title="Monthly Sales", description="Sales performance summary"))
        self.create(ReportCreate(title="Website Traffic", description="Traffic sources and trends"))

    def get(self, report_id: int) -> Optional[Report]:
        with self._lock:
            return self._by_id.get(report_id)

    def list(self, page: int, size: int, search: Optional[str]) -> Tuple[List[Report], int]:
        with self._lock:
            items = list(self._by_id.values())
        if search:
            s = search.lower()
            items = [r for r in items if s in r.title.lower() or (r.description or "").lower().find(s) >= 0]
        total = len(items)
        start = (page - 1) * size
        end = start + size
        return items[start:end], total

    def create(self, data: ReportCreate) -> Report:
        with self._lock:
            report = Report(id=self._id_gen.next(), title=data.title, description=data.description)
            self._by_id[report.id] = report
            return report

    def update(self, report_id: int, data: ReportUpdate) -> Optional[Report]:
        with self._lock:
            report = self._by_id.get(report_id)
            if not report:
                return None
            if data.title is not None:
                report.title = data.title
            if data.description is not None:
                report.description = data.description
            self._by_id[report.id] = report
            return report

    def delete(self, report_id: int) -> bool:
        with self._lock:
            r = self._by_id.pop(report_id, None)
            return r is not None


# Singletons for simple DI
users_repo = UsersRepository()
reports_repo = ReportsRepository()
