import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient as MotorAsyncIOMotorClient

# Load environment variables from a .env file if needed
from dotenv import load_dotenv
load_dotenv()

# Configuration using environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")  # Default if not found
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Default to HS256 if not set
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # Default to 30 minutes if not set

def init_db_client():
    db_uri = os.getenv('MONGODB_URI')
    if not db_uri:
        raise ValueError("MONGODB_URI environment variable not set")
    return MotorAsyncIOMotorClient(
        db_uri,
        uuidRepresentation="standard",
    )

# ...existing code...