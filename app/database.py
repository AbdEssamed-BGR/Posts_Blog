import logging
from app.config import init_db_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the database client
db_client = init_db_client()

# Define your collections
users_collection = db_client["PostBlog"]["users"]
blacklist_collection = db_client["PostBlog"]["blacklist"]

# Test the connection
try:
    db_client.admin.command('ping')
    logger.info("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    logger.error("MongoDB connection error: %s", e)