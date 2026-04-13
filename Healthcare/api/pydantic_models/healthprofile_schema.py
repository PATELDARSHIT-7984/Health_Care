from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

class HealthProfileSchema(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = Field(description="Phone Number must be a 10-digit number")  
    Email: EmailStr | None = None

    @field_validator('name')
    def validate_name(cls, value):
        if not value.strip():
            raise ValueError('Name cannot be empty')
        return value
    @field_validator('phone')
    def validate_phone(cls, value):

        if value is None:
            return value

        if not value.isdigit():
            raise ValueError('Phone number must be a 10-digit number')
        
        if len(value) != 10:
            raise ValueError('Phone number must be a 10-digit number')
        
        return value
    