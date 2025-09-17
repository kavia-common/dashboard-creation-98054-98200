from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from .deps import get_current_user
from .schemas import Report, ReportCreate, ReportUpdate, PaginatedReports
from .repositories import reports_repo
from .config import get_settings

router = APIRouter(prefix="/reports", tags=["Reports"])
settings = get_settings()


@router.get(
    "",
    response_model=PaginatedReports,
    summary="List reports",
    description="List reports with pagination and optional search.",
)
# PUBLIC_INTERFACE
def list_reports(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(default_factory=lambda: settings.DEFAULT_PAGE_SIZE, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search query"),
    _=Depends(get_current_user),
):
    """List reports with pagination and search."""
    items, total = reports_repo.list(page=page, size=size, search=search)
    return PaginatedReports(items=items, total=total, page=page, size=size)


@router.post(
    "",
    response_model=Report,
    status_code=201,
    summary="Create report",
    description="Create a new report.",
)
# PUBLIC_INTERFACE
def create_report(data: ReportCreate, _=Depends(get_current_user)):
    """Create a new report."""
    return reports_repo.create(data)


@router.put(
    "/{report_id}",
    response_model=Report,
    summary="Update report",
    description="Update an existing report.",
    responses={404: {"description": "Not found"}},
)
# PUBLIC_INTERFACE
def update_report(report_id: int, data: ReportUpdate, _=Depends(get_current_user)):
    """Update a report by id."""
    r = reports_repo.update(report_id, data)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return r


@router.delete(
    "/{report_id}",
    status_code=204,
    summary="Delete report",
    description="Delete report by id.",
    responses={404: {"description": "Not found"}},
)
# PUBLIC_INTERFACE
def delete_report(report_id: int, _=Depends(get_current_user)):
    """Delete a report by id."""
    ok = reports_repo.delete(report_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return None
