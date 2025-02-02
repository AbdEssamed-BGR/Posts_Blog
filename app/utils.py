from datetime import datetime, timedelta
import logging
from typing import Optional  # Add this import
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.database import blacklist_collection, users_collection
from app.models import TokenBlacklist
from fastapi import HTTPException, Depends, status, Request, Query
from fastapi.security import OAuth2PasswordBearer

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def decode_token(token: str) -> str:
    """Decode a JWT token and return the username."""
    try:
        logger.info(f"Decoding token: {token}")
        blacklisted_token = await blacklist_collection.find_one({"token": token})
        if blacklisted_token:
            logger.warning(f"Token revoked: {blacklisted_token}")
            raise HTTPException(status_code=401, detail="Token revoked")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("Username not found in token payload")
            raise JWTError
        logger.info(f"Token decoded successfully, username: {username}")
        return username
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError as e:
        logger.warning(f"Invalid token: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_user_by_username(username: str):
    """Retrieve a user by username."""
    logger.info(f"Searching for user by username: {username}")
    user = await users_collection.find_one({"username": username})
    if user:
        logger.info(f"User found: {username}")
    else:
        logger.info(f"User not found: {username}")
    return user

async def get_current_user(request: Request, token: Optional[str] = None):
    """Get the current user from the JWT token in cookies or query parameter."""
    if token is None:
        token = request.cookies.get("token")
    if token is None:
        logger.warning("No token found in cookies or query parameter")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    logger.info(f"Decoding token: {token}")
    username = await decode_token(token)
    if not username:
        logger.warning("Invalid authentication credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await get_user_by_username(username)
    if not user:
        logger.warning(f"User not found: {username}")
        raise HTTPException(status_code=404, detail="User not found")
    logger.info(f"Authenticated user: {username}")
    return user