# models/address.py
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field


class Address(BaseModel):
    id: UUID = Field(..., description="Address ID(UUID)")
    user_id: UUID = Field(..., description="User ID(UUID)")
    country: str = Field(..., min_length=1, max_length=60, description="country")
    city: str = Field(..., min_length=1, max_length=60, description="city")
    street: str = Field(..., min_length=1, max_length=120, description="street")
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20, description="postal code")

    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "c6a0f6b1-63c0-48c5-8a0f-8a4c1d74b2a4",
                "user_id": "6f3e3c14-1e1d-46fd-9a77-7d6d85b3d2c3",
                "country": "US",
                "city": "Philadelphia",
                "street": "123 Main St Apt 4B",
                "postal_code": "19104"
            }
        }
    }


class AddressCreate(BaseModel):
    user_id: UUID = Field(..., description="User ID (UUID)")
    country: str = Field(..., min_length=1, max_length=60)
    city: str = Field(..., min_length=1, max_length=60)
    street: str = Field(..., min_length=1, max_length=120)
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20)

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": "6f3e3c14-1e1d-46fd-9a77-7d6d85b3d2c3",
                "country": "US",
                "city": "Philadelphia",
                "street": "123 Main St Apt 4B",
                "postal_code": "19104"
            }
        }
    }


class AddressUpdate(BaseModel):
    country: Optional[str] = Field(None, min_length=1, max_length=60)
    city: Optional[str] = Field(None, min_length=1, max_length=60)
    street: Optional[str] = Field(None, min_length=1, max_length=120)
    postal_code: Optional[str] = Field(None, min_length=3, max_length=20)

    model_config = {
        "json_schema_extra": {
            "example": {
                "city": "Boston"
            }
        }
    }
