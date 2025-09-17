from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .security import decode_and_verify_token
from .repositories import users_repo

bearer_scheme = HTTPBearer(auto_error=False)


# PUBLIC_INTERFACE
def get_current_user(creds: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)):
    """Dependency to parse and verify JWT bearer token and return the current user object."""
    if creds is None or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_and_verify_token(creds.credentials)
    user_sub = payload.get("sub")
    if not user_sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")
    # sub will be email for this demo
    user = users_repo.get_by_email(user_sub) or users_repo.get(int(user_sub))  # accept id or email
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is inactive")
    return user


openapi_tags = [
    {"name": "Auth", "description": "Authentication endpoints"},
    {"name": "Users", "description": "CRUD operations for users"},
    {"name": "Reports", "description": "CRUD operations for reports"},
    {"name": "Charts", "description": "Chart data endpoints"},
    {"name": "Health", "description": "Health and diagnostics"},
]
