from fastapi import FastAPI, HTTPException, Depends, status, Response, Cookie
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import ObjectId
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
uri = "mongodb+srv://PostBlog:k58TC3AswWpaVel4@postblog.nlj46.mongodb.net/?retryWrites=true&w=majority&appName=PostBlog"
client = MongoClient(uri, server_api=ServerApi('1'), tlsAllowInvalidCertificates=True)

# Test the connection
try:
    client.admin.command('ping')
    logger.info("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    logger.error("MongoDB connection error: %s", e)

# Use the database
db = client["blog_db"]
users_collection = db["users"]
blacklist_collection = db["blacklist"]

# FastAPI app
app = FastAPI()

# JWT settings
SECRET_KEY = "hashcode(^_^)"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Pydantic models
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
    title: Optional[str] = None  # Make title optional
    description: Optional[str] = None  # Make description optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenBlacklist(BaseModel):
    token: str
    expires_at: datetime

class LoginRequest(BaseModel):
    username: str
    password: str

# Utility functions
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> str:
    try:
        if blacklist_collection.find_one({"token": token}):
            raise HTTPException(status_code=401, detail="Token revoked")
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise JWTError
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Get current user from cookies
def get_current_user(token: str = Cookie(None)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    logger.info("Received token: %s", token)
    username = decode_token(token)
    logger.info("Decoded username: %s", username)
    user = users_collection.find_one({"username": username})
    if not user:
        logger.error("User not found in database")
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

@app.post("/register/", response_model=Token)
async def register(user: User, response: Response):
    logger.info("Received registration request: %s", user.dict())
    
    existing_user = users_collection.find_one({"username": user.username})
    if existing_user:
        logger.error("Username already exists: %s", user.username)
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = get_password_hash(user.password)
    
    user_dict = {
        "username": user.username,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "posts": []
    }
    
    logger.info("Inserting user into database: %s", user_dict)
    users_collection.insert_one(user_dict)
    
    access_token = create_access_token(data={"sub": user.username})
    
    response.set_cookie(key="token", value=access_token, httponly=True)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/login/", response_model=Token)
async def login(login_request: LoginRequest, response: Response):
    user = users_collection.find_one({"username": login_request.username})
    if not user or not verify_password(login_request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(
        data={"sub": user["username"]},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    response.set_cookie(key="token", value=access_token, httponly=True)
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.post("/logout/")
async def logout(response: Response):
    response.delete_cookie(key="token")
    return {"message": "Logged out successfully"}

@app.post("/posts/")
async def create_post(post: Post, user: dict = Depends(get_current_user)):
    post_dict = post.dict()
    post_dict["post_id"] = str(ObjectId())
    post_dict["author"] = user["username"]
    
    result = users_collection.update_one(
        {"username": user["username"]},
        {"$push": {"posts": post_dict}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to create post")
    
    return {"message": "Post created successfully"}

@app.get("/posts/")
async def get_posts():
    users = users_collection.find({}, {"posts": 1})
    posts = []
    for user in users:
        posts.extend(user.get("posts", []))
    return posts

@app.get("/my-posts/")
async def get_my_posts(user: dict = Depends(get_current_user)):
    user_data = users_collection.find_one({"username": user["username"]}, {"posts": 1})
    return user_data.get("posts", [])

@app.patch("/posts/{post_id}")
async def update_post(post_id: str, post: Post, user: dict = Depends(get_current_user)):
    update_data = post.dict(exclude_unset=True)  # Only include fields that are provided
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Build the update query dynamically
    update_query = {}
    if "title" in update_data:
        update_query["posts.$.title"] = update_data["title"]
    if "description" in update_data:
        update_query["posts.$.description"] = update_data["description"]
    
    result = users_collection.update_one(
        {"username": user["username"], "posts.post_id": post_id},
        {"$set": update_query}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found or unauthorized")
    return {"message": "Post updated"}

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, user: dict = Depends(get_current_user)):
    result = users_collection.update_one(
        {"username": user["username"]},
        {"$pull": {"posts": {"post_id": post_id}}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Post not found or unauthorized")
    return {"message": "Post deleted"}

@app.get("/posts/{post_id}/author")
async def get_post_author(post_id: str):
    user = users_collection.find_one({"posts.post_id": post_id}, {"username": 1, "full_name": 1})
    if not user:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return {"full_name": user.get("full_name")}