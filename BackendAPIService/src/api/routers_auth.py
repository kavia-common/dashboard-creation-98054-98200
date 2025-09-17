from datetime import timedelta

from fastapi import APIRouter, HTTPException, status
from .schemas import LoginRequest, Token
from .repositories import users_repo
from .security import verify_password, create_access_token
from .config import get_settings

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


@router.post(
    "/login",
    response_model=Token,
    summary="Login",
    description="Validate user credentials and return a JWT access token.",
    responses={
        200: {"description": "Authenticated. Returns JWT token."},
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"},
    },
)
# PUBLIC_INTERFACE
def login(data: LoginRequest):
    """Authenticate a user using email and password and return a JWT token on success."""
    user = users_repo.get_by_email(data.email.lower())
    # Use generic error message to avoid user enumeration
    auth_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid email or password",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not user:
        raise auth_error
    pwd_hash = users_repo.get_password_hash(user.id)
    if not pwd_hash or not verify_password(data.password, pwd_hash):
        raise auth_error
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")

    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(subject=user.email, expires_delta=expires)
    return Token(access_token=token, token_type="bearer")
