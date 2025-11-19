# models/address.py
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field

class Address(BaseModel):
    id: UUID = Field(..., description="Address ID(UUID)")
    user_id: UUID = Field(..., description="user ID(UUID)")
    recipient: str = Field(..., min_length=1, max_length=50, description="recipient")
    phone: Optional[str] = Field(None, min_length=6, max_length=30)
    country: str = Field(..., min_length=1, max_length=60)
    city: str = Field(..., min_length=1, max_length=60)
    street: str = Field(..., min_length=1, max_length=120)
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20)
    is_default: bool = Field(False, description="is it defualt address")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "c6a0f6b1-63c0-48c5-8a0f-8a4c1d74b2a4",
                "user_id": "6f3e3c14-1e1d-46fd-9a77-7d6d85b3d2c3",
                "recipient": "Alice",
                "phone": "+1-215-000-0000",
                "country": "US",
                "city": "Philadelphia",
                "street": "123 Main St Apt 4B",
                "postal_code": "19104",
                "is_default": True
            }
        }
    }

class AddressCreate(BaseModel):
    user_id: UUID = Field(..., description="User ID (UUID)")
    recipient: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = Field(None, min_length=6, max_length=30)
    country: str = Field(..., min_length=1, max_length=60)
    city: str = Field(..., min_length=1, max_length=60)
    street: str = Field(..., min_length=1, max_length=120)
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20)
    is_default: bool = Field(False)

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "6f3e3c14-1e1d-46fd-9a77-7d6d85b3d2c3",
                "recipient": "Alice",
                "phone": "+1-215-000-0000",
                "country": "US",
                "city": "Philadelphia",
                "street": "123 Main St Apt 4B",
                "postal_code": "19104",
                "is_default": True
            }
        }
    }

class AddressUpdate(BaseModel):
    recipient: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, min_length=6, max_length=30)
    country: Optional[str] = Field(None, min_length=1, max_length=60)
    city: Optional[str] = Field(None, min_length=1, max_length=60)
    street: Optional[str] = Field(None, min_length=1, max_length=120)
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20)
    is_default: Optional[bool] = Field(None)

    model_config = {
        "json_schema_extra": {
            "example": { "city": "Boston", "is_default": False }
        }
    }
