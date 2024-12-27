# this needs to run once to create the MongoDB text index
# to run this, make sure your .env file has the MongoDB connection details
# run the script python scripts/init_db.py 

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

def init_mongodb():
    try:
        # Connect to MongoDB
        client = MongoClient(os.getenv("MONGODB_URI"))
        db = client[os.getenv("DB_NAME", "news_db")]
        collection = db[os.getenv("COLLECTION_NAME", "articles")]
        
        # Create text index
        print("Creating text index on 'content' and 'title' fields...")
        collection.create_index(
            [("content", "text"), ("title", "text")],
            name="content_title_text_index"
        )
        
        # Create date index for sorting
        print("Creating index on 'publish_date' field...")
        collection.create_index("publish_date", name="publish_date_index")
        
        print("Indexes created successfully!")
        
        # Verify indexes
        indexes = collection.list_indexes()
        print("\nCurrent indexes:")
        for index in indexes:
            print(f"- {index['name']}: {index['key']}")
            
    except Exception as e:
        print(f"Error creating indexes: {str(e)}")
    finally:
        client.close()

if __name__ == "__main__":
    init_mongodb()