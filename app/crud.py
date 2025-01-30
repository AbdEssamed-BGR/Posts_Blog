from app.database import users_collection, blacklist_collection
from bson import ObjectId
from app.models import Post
from datetime import datetime

def create_user(user_data):
    """Create a new user in the database."""
    users_collection.insert_one(user_data)

def get_user_by_username(username: str):
    """Retrieve a user by username."""
    return users_collection.find_one({"username": username})

def update_user_posts(username: str, post_data: dict):
    """Add a new post to a user's posts."""
    return users_collection.update_one(
        {"username": username},
        {"$push": {"posts": post_data}}
    )

def get_user_posts(username: str):
    """Retrieve all posts for a user."""
    user = users_collection.find_one({"username": username})
    return user.get("posts", []) if user else []

def update_post(username: str, post_id: str, update_data: dict):
    """Update a specific post for a user."""
    return users_collection.update_one(
        {"username": username, "posts.post_id": post_id},
        {"$set": {"posts.$": update_data}}
    )

def delete_post(username: str, post_id: str):
    """Delete a specific post for a user."""
    return users_collection.update_one(
        {"username": username},
        {"$pull": {"posts": {"post_id": post_id}}}
    )