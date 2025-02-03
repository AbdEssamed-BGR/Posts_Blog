import os
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient as MotorAsyncIOMotorClient
from dotenv import load_dotenv
import dns.resolver

# Load environment variables from a .env file if needed
load_dotenv()

# Configuration using environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")  # Default if not found
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Default to HS256 if not set
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # Default to 30 minutes if not set
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")

# Set DNS resolver to use Google DNS
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4']

def init_db_client():
    db_uri = f"mongodb+srv://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}?retryWrites=true&w=majority"
    return MotorAsyncIOMotorClient(
        db_uri,
        io_loop=asyncio.get_running_loop(),
        uuidRepresentation="standard",
    )