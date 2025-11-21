# models/user.py
from uuid import UUID
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, HttpUrl


class UserBrief(BaseModel):
    id: UUID = Field(..., description="User ID (UUID)")
    username: str = Field(..., min_length=3, max_length=30, description="username")
    avatar_url: Optional[HttpUrl] = Field(None, description="avatar URL")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "6f3e3c14-1e1d-46fd-9a77-7d6d85b3d2c3",
                "username": "alice_shop",
                "avatar_url": "https://cdn.example.com/avatars/alice.png"
            }
        }
    }


class UserRead(BaseModel):
    id: UUID = Field(..., description="User ID (UUID)")
    email: EmailStr = Field(..., description="email address")
    username: str = Field(..., min_length=3, max_length=30, description="username")
    full_name: Optional[str] = Field(None, min_length=1, max_length=50, description="full name")
    avatar_url: Optional[HttpUrl] = Field(None, description="avatar URL")
    phone: Optional[str] = Field(None, min_length=6, max_length=30, description="phone number")
    created_at: datetime = Field(..., description="created time")
    updated_at: datetime = Field(..., description="updated time")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "6f3e3c14-1e1d-46fd-9a77-7d6d85b3d2c3",
                "email": "alice@example.com",
                "username": "alice_shop",
                "full_name": "Alice Zhou",
                "avatar_url": "https://cdn.example.com/avatars/alice.png",
                "phone": "+1-215-000-0000",
                "created_at": "2025-10-17T12:00:00Z",
                "updated_at": "2025-10-17T12:10:00Z"
            }
        }
    }


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="email address")
    username: str = Field(..., min_length=3, max_length=30, description="username")
    password: str = Field(..., min_length=8, max_length=72, description="password")
    full_name: Optional[str] = Field(None, min_length=1, max_length=50, description="full name")
    avatar_url: Optional[HttpUrl] = Field(None, description="avatar URL")
    phone: Optional[str] = Field(None, min_length=6, max_length=30, description="phone number")

    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "alice@example.com",
                "username": "alice_shop",
                "password": "S3cureP@ssw0rd",
                "full_name": "Alice Zhou",
                "avatar_url": "https://cdn.example.com/avatars/alice.png",
                "phone": "+1-215-000-0000"
            }
        }
    }


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=30, description="username")
    full_name: Optional[str] = Field(None, min_length=1, max_length=50, description="full name")
    avatar_url: Optional[HttpUrl] = Field(None, description="avatar URL")
    phone: Optional[str] = Field(None, min_length=6, max_length=30, description="phone number")

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "alice_updated",
                "full_name": "Alice Z.",
                "avatar_url": "https://cdn.example.com/avatars/alice-new.png",
                "phone": "+1-215-000-0000"
            }
        }
    }
