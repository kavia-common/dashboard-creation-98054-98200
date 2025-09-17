from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .deps import get_current_user
from .schemas import User, UserCreate, UserUpdate, PaginatedUsers
from .repositories import users_repo
from .config import get_settings

router = APIRouter(prefix="/users", tags=["Users"])
settings = get_settings()


@router.get(
    "",
    response_model=PaginatedUsers,
    summary="List users",
    description="List users with pagination and optional search.",
    responses={200: {"description": "List of users"}, 401: {"description": "Unauthorized"}},
)
# PUBLIC_INTERFACE
def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(default_factory=lambda: settings.DEFAULT_PAGE_SIZE, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search query"),
    _=Depends(get_current_user),
):
    """List users with pagination and search."""
    items, total = users_repo.list(page=page, size=size, search=search)
    return PaginatedUsers(items=items, total=total, page=page, size=size)


@router.post(
    "",
    response_model=User,
    status_code=201,
    summary="Create user",
    description="Create a new user.",
    responses={201: {"description": "User created"}, 400: {"description": "Email exists"}, 401: {"description": "Unauthorized"}},
)
# PUBLIC_INTERFACE
def create_user(data: UserCreate, _=Depends(get_current_user)):
    """Create a new user with validation."""
    try:
        user = users_repo.create(data)
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put(
    "/{user_id}",
    response_model=User,
    summary="Update user",
    description="Update an existing user.",
    responses={200: {"description": "User updated"}, 404: {"description": "Not found"}, 401: {"description": "Unauthorized"}},
)
# PUBLIC_INTERFACE
def update_user(user_id: int, data: UserUpdate, _=Depends(get_current_user)):
    """Update user fields."""
    try:
        user = users_repo.update(user_id, data)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete(
    "/{user_id}",
    status_code=204,
    summary="Delete user",
    description="Delete a user by id.",
    responses={204: {"description": "Deleted"}, 404: {"description": "Not found"}, 401: {"description": "Unauthorized"}},
)
# PUBLIC_INTERFACE
def delete_user(user_id: int, _=Depends(get_current_user)):
    """Delete a user."""
    ok = users_repo.delete(user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return None
