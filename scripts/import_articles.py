import os
from pymongo import MongoClient
from datetime import datetime
import sys
from dotenv import load_dotenv

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.text_utils import parse_article_content

load_dotenv()

def import_articles():
    # Connect to MongoDB
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client[os.getenv("DB_NAME", "news_db")]
    collection = db[os.getenv("COLLECTION_NAME", "articles")]
    
    # Create an index on filename to make lookups faster
    collection.create_index("filename", unique=True)
    
    # Path to articles
    archive_folder = "./archive_texts"
    
    # Track statistics
    stats = {
        "processed": 0,
        "skipped": 0,
        "updated": 0,
        "errors": 0
    }
    
    # Process each file
    for filename in os.listdir(archive_folder):
        if filename.endswith(".txt"):
            try:
                # Check if article already exists
                existing_article = collection.find_one({"filename": filename})
                
                with open(os.path.join(archive_folder, filename), "r", encoding="utf-8") as file:
                    content = file.read()
                    metadata, article_content = parse_article_content(content)
                    
                    # Extract date from filename (e.g., 20061117)
                    file_date = None
                    for part in filename.split('_'):
                        if len(part) == 8 and part.isdigit():
                            year = part[:4]
                            month = part[4:6]
                            day = part[6:]
                            file_date = f"{year}-{month}-{day}"
                            break
                    
                    # Create document
                    document = {
                        "title": metadata.get("title", os.path.splitext(filename)[0]),
                        "content": article_content,
                        "author": metadata.get("author", "Unknown"),
                        "publish_date": datetime.strptime(file_date, "%Y-%m-%d") if file_date else None,
                        "filename": filename,
                        "last_updated": datetime.utcnow()
                    }
                    
                    if existing_article:
                        # Update existing article if content has changed
                        if existing_article.get("content") != article_content:
                            collection.update_one(
                                {"filename": filename},
                                {"$set": document}
                            )
                            print(f"Updated {filename}")
                            stats["updated"] += 1
                        else:
                            print(f"Skipped {filename} (no changes)")
                            stats["skipped"] += 1
                    else:
                        # Insert new article
                        document["created_at"] = datetime.utcnow()
                        collection.insert_one(document)
                        print(f"Imported {filename}")
                        stats["processed"] += 1
                    
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
                stats["errors"] += 1

    return stats

if __name__ == "__main__":
    print("Starting article import...")
    stats = import_articles()
    print("\nImport completed!")
    print(f"Articles processed: {stats['processed']}")
    print(f"Articles skipped (no changes): {stats['skipped']}")
    print(f"Articles updated: {stats['updated']}")
    print(f"Errors encountered: {stats['errors']}")