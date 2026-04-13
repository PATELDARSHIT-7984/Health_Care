from pydantic import BaseModel, Field, field_validator, model_validator
from django.contrib.auth.models import User

class UserRegister(BaseModel):
    username : str = Field(min_length=3)
    password : str = Field(min_length=8)
    confirm_password : str = Field(min_length=8)
    
    @field_validator('username')
    def validate_username(cls, value):
        if not value.strip():
            raise ValueError('Username cannot be empty')
        return value

    @model_validator(mode='after')
    def check_passwords(self):
        if self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self
    
class UserLogin(BaseModel):
    username : str = Field(min_length=3)
    password : str = Field(min_length=8)

    @field_validator('username')
    def validate_username(cls, value):
        if not value.strip():
            raise ValueError('Username cannot be empty')
        
        return value