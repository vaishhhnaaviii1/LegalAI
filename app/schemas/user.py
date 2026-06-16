from pydantic import BaseModel, Field, EmailStr, field_validator
import re


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    phone_no: str | None = None
    password: str = Field(min_length=6)

    @field_validator("phone_no")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return value

        pattern = r"^[6-9]\d{9}$"  # Indian mobile number
        if not re.match(pattern, value):
            raise ValueError("Invalid phone number")

        return value


class UserUpdate(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    phone_no: str | None = None
    is_active: bool | None = None

    @field_validator("phone_no")
    @classmethod
    def validate_phone(cls, value):
        if value is None:
            return value

        pattern = r"^[6-9]\d{9}$"
        if not re.match(pattern, value):
            raise ValueError("Invalid phone number")

        return value