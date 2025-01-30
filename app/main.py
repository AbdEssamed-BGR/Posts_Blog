from fastapi import FastAPI, HTTPException, Depends, Response
from app.models import User, LoginRequest, Post, Token
from app.crud import create_user, get_user_by_username, update_user_posts, get_user_posts, update_post, delete_post
from app.utils import get_password_hash, verify_password, create_access_token, get_current_user
from datetime import timedelta
from bson import ObjectId

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI application with MongoDB"}

@app.post("/register", response_model=Token)
async def register(user: User, response: Response):
    existing_user = get_user_by_username(user.username)
    if (existing_user):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    hashed_password = get_password_hash(user.password)
    
    user_dict = {
        "username": user.username,
        "hashed_password": hashed_password,
        "full_name": user.full_name,
        "posts": []
    }
    
    create_user(user_dict)
    access_token = create_access_token(data={"sub": user.username})
    response.set_cookie(key="token", value=access_token, httponly=True)
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/login", response_model=Token)
async def login(login_request: LoginRequest, response: Response):
    user = get_user_by_username(login_request.username)
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
async def create_post(post: Post, user: dict = Depends(get_current_user)):
    post_dict = post.dict()
    post_dict["post_id"] = str(ObjectId())
    post_dict["author"] = user["username"]
    
    result = update_user_posts(user["username"], post_dict)
    if result.modified_count == 0:
        raise HTTPException(status_code=500, detail="Failed to create post")
    
    return {"message": "Post created successfully"}

@app.get("/posts/")
async def get_posts():
    posts = get_user_posts("")
    return posts

@app.get("/my-posts/")
async def get_my_posts(user: dict = Depends(get_current_user)):
    user_data = get_user_posts(user["username"])
    return user_data

@app.patch("/posts/{post_id}")
async def update_post(post_id: str, post: Post, user: dict = Depends(get_current_user)):
    update_data = post.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    result = update_post(user["username"], post_id, update_data)
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Post not found or unauthorized")
    
    return {"message": "Post updated"}

@app.delete("/posts/{post_id}")
async def delete_post(post_id: str, user: dict = Depends(get_current_user)):
    result = delete_post(user["username"], post_id)
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Post not found or unauthorized")
    
    return {"message": "Post deleted"}