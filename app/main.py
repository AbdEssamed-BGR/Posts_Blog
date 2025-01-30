import logging
from fastapi import FastAPI, HTTPException, Depends, Response, Request, Query
from app.models import User, LoginRequest, Post, Token
from app.crud import create_user, get_user_by_username, update_user_posts, get_user_posts, update_post, delete_post, get_all_users
from app.utils import get_password_hash, verify_password, create_access_token, get_current_user
from datetime import timedelta
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application with MongoDB"}

@app.post("/register", response_model=Token)
async def register(user: User, response: Response):
    logger.info(f"Attempting to register user: {user.username}")
    existing_user = await get_user_by_username(user.username)
    if existing_user:
        logger.warning(f"Username already exists: {user.username}")
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = get_password_hash(user.password)
    
    user_dict = {
        "username": user.username,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "posts": []
    }
    
    await create_user(user_dict)
    access_token = create_access_token(data={"sub": user.username})
    response.set_cookie(key="token", value=access_token, httponly=True)
    
    logger.info(f"User registered successfully: {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
async def login(login_request: LoginRequest, response: Response):
    user = await get_user_by_username(login_request.username)
    if not user or not verify_password(login_request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=timedelta(minutes=30))
    response.set_cookie(key="token", value=access_token, httponly=True)
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/logout")
async def logout(response: Response):
    response.delete_cookie(key="token")
    return {"message": "Logged out successfully"}

@app.post("/posts")
async def create_post(post: Post, request: Request, token: str = Query(...)):
    user = await get_current_user(request, token)
    post_dict = post.dict()
    post_dict["post_id"] = str(ObjectId())
    post_dict["author"] = user["username"]
    
    result = await update_user_posts(user["username"], post_dict)
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to create post")
    
    return {"message": "Post created successfully"}

@app.get("/posts/")
async def get_posts():
    posts = await get_user_posts("")
    return posts

@app.get("/my-posts/")
async def get_my_posts(request: Request, token: str = Query(...)):
    user = await get_current_user(request, token)
    user_data = await get_user_posts(user["username"])
    return user_data

@app.patch("/posts/{post_id}")
async def update_post(post_id: str, post: Post, request: Request, token: str = Query(...)):
    user = await get_current_user(request, token)
    update_data = post.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = await update_post(user["username"], post_id, update_data)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found or unauthorized")
    
    return {"message": "Post updated"}

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, request: Request, token: str = Query(...)):
    user = await get_current_user(request, token)
    result = await delete_post(user["username"], post_id)
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Post not found or unauthorized")
    
    return {"message": "Post deleted"}

@app.get("/users/")
async def list_users():
    users = await get_all_users()
    return users