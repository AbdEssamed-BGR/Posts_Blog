import os
import socket
from motor.motor_asyncio import AsyncIOMotorClient as MotorAsyncIOMotorClient
from dotenv import load_dotenv
import dns.resolver

# Load environment variables from a .env file if needed
load_dotenv()

# Configuration using environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")  # Default if not found
ALGORITHM = os.getenv("ALGORITHM", "HS256")  # Default to HS256 if not set
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))  # Default to 30 minutes if not set

# Set DNS resolver to use Google DNS
dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ['8.8.8.8', '8.8.4.4']

def test_dns_resolution(hostname):
    try:
        socket.gethostbyname(hostname)
        print(f"DNS resolution for {hostname} succeeded.")
    except socket.error as err:
        print(f"DNS resolution for {hostname} failed: {err}")

def init_db_client():
    db_uri = os.getenv('MONGODB_URI')
    if not db_uri:
        raise ValueError("MONGODB_URI environment variable not set")
    
    # Extract hostname from URI and test DNS resolution
    hostname = db_uri.split('@')[1].split('/')[0]
    test_dns_resolution(hostname)
    
    return MotorAsyncIOMotorClient(
        db_uri,
        uuidRepresentation="standard",
        serverSelectionTimeoutMS=10000  # Increase timeout to 10 seconds
    )

# ...existing code...