from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    mongodb_uri: str = os.getenv("MONGODB_URI")
    db_name: str = os.getenv("DB_NAME", "news_db")
    collection_name: str = os.getenv("COLLECTION_NAME", "articles")

settings = Settings()