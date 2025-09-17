from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, constr


# Auth Schemas

class Token(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email")
    password: constr(min_length=6, max_length=128) = Field(..., description="User password")


# User Schemas

class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="Full name of the user")


class UserCreate(UserBase):
    password: constr(min_length=6, max_length=128) = Field(..., description="Password for the user")


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = Field(None, description="Updated email")
    full_name: Optional[str] = Field(None, description="Updated full name")
    password: Optional[constr(min_length=6, max_length=128)] = Field(None, description="New password")


class User(UserBase):
    id: int = Field(..., description="User identifier")
    is_active: bool = Field(default=True, description="Active status")


# Report Schemas

class ReportBase(BaseModel):
    title: constr(min_length=1, max_length=128) = Field(..., description="Report title")
    description: Optional[constr(max_length=1024)] = Field(None, description="Report description")


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseModel):
    title: Optional[constr(min_length=1, max_length=128)] = Field(None, description="Updated title")
    description: Optional[constr(max_length=1024)] = Field(None, description="Updated description")


class Report(ReportBase):
    id: int = Field(..., description="Report identifier")


# Pagination and List responses

class PaginatedUsers(BaseModel):
    items: List[User]
    total: int
    page: int
    size: int


class PaginatedReports(BaseModel):
    items: List[Report]
    total: int
    page: int
    size: int


# Chart data schemas

class LineChartPoint(BaseModel):
    x: str
    y: float


class PieChartSlice(BaseModel):
    label: str
    value: float


class BarChartBar(BaseModel):
    label: str
    value: float


class ChartsData(BaseModel):
    line: List[LineChartPoint]
    pie: List[PieChartSlice]
    bar: List[BarChartBar]
