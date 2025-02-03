from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class User(BaseModel):
    """Model for user registration."""
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None

class UserInDB(BaseModel):
    """Model for user data stored in the database."""
    username: str
    hashed_password: str
    full_name: Optional[str] = None
    posts: List[dict] = []

class Post(BaseModel):
    """Model for a blog post."""
    title: Optional[str] = None
    description: Optional[str] = None


class Token(BaseModel):
    """Model for JWT token response."""
    access_token: str
    token_type: str

class TokenBlacklist(BaseModel):
    """Model for blacklisted tokens."""
    token: str
    expires_at: datetime

class LoginRequest(BaseModel):
    """Model for login request."""
    username: str
    password: str