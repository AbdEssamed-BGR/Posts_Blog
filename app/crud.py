import logging
from app.database import users_collection, blacklist_collection
from bson import ObjectId
from app.models import Post
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def create_user(user_data):
    """Create a new user in the database."""
    logger.info(f"Creating user: {user_data['username']}")
    result = await users_collection.insert_one(user_data)
    if result.inserted_id:
        logger.info(f"User created successfully: {user_data['username']}")
    else:
        logger.error(f"Failed to create user: {user_data['username']}")

async def get_user_by_username(username: str):
    """Retrieve a user by username."""
    logger.info(f"Searching for user by username: {username}")
    user = await users_collection.find_one({"username": username})
    if user:
        logger.info(f"User found: {username}")
    else:
        logger.info(f"User not found: {username}")
    return user

async def update_user_posts(username: str, post_data: dict):
    """Add a new post to a user's posts."""
    return await users_collection.update_one(
        {"username": username},
        {"$push": {"posts": post_data}}
    )

async def get_user_posts(username: str):
    """Retrieve all posts for a user."""
    user = await users_collection.find_one({"username": username})
    return user.get("posts", []) if user else []

async def get_all_users():
    """Retrieve all users."""
    users = []
    async for user in users_collection.find():
        user["_id"] = str(user["_id"])  # Convert ObjectId to string
        users.append(user)
    return users

async def update_post(username: str, post_id: str, update_data: dict):
    """Update a specific post for a user."""
    return await users_collection.update_one(
        {"username": username, "posts.post_id": post_id},
        {"$set": {"posts.$": update_data}}
    )

async def delete_post(username: str, post_id: str):
    """Delete a specific post for a user."""
    return await users_collection.update_one(
        {"username": username},
        {"$pull": {"posts": {"post_id": post_id}}}
    )