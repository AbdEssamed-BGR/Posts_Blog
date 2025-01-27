from app.database import users_collection, blacklist_collection
from bson import ObjectId
from app.models import Post
from datetime import datetime

def create_user(user_data):
    users_collection.insert_one(user_data)

def get_user_by_username(username: str):
    return users_collection.find_one({"username": username})

def update_user_posts(username: str, post_data: dict):
    return users_collection.update_one(
        {"username": username},
        {"$push": {"posts": post_data}}
    )

def get_user_posts(username: str):
    user = users_collection.find_one({"username": username})
    return user.get("posts", []) if user else []

def update_post(username: str, post_id: str, update_data: dict):
    return users_collection.update_one(
        {"username": username, "posts.post_id": post_id},
        {"$set": {"posts.$": update_data}}
    )

def delete_post(username: str, post_id: str):
    return users_collection.update_one(
        {"username": username},
        {"$pull": {"posts": {"post_id": post_id}}}
    )