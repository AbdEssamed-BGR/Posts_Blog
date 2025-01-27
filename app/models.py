from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class UserInDB(BaseModel):
    username: str
    hashed_password: str
    full_name: Optional[str] = None
    posts: List[dict] = []

class Post(BaseModel):
    title: str
    description: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenBlacklist(BaseModel):
    token: str
    expires_at: datetime

class LoginRequest(BaseModel):
    username: str
    password: str