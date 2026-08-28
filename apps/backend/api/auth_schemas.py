"""Pydantic schemas for authentication endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class AuthUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    display_name: str
    role: str
    status: str
    must_change_password: bool


class SessionResponse(BaseModel):
    status: str = "success"
    session_token: str
    token_type: str = "Bearer"
    expires_at: datetime
    user: AuthUser


class MeResponse(BaseModel):
    status: str = "success"
    user: AuthUser


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=256)
    new_password: str = Field(min_length=1, max_length=256)


class MessageResponse(BaseModel):
    status: str = "success"
    message: str
