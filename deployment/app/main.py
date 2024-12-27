from haystack.document_stores import MongoDocumentStore
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize MongoDB document store
document_store = MongoDocumentStore(
    mongo_url=os.getenv("MONGODB_URI"),
    db_name=os.getenv("DB_NAME", "news_db"),
    collection_name=os.getenv("COLLECTION_NAME", "articles")
)

def init_document_store():
    """Initialize the document store with articles"""
    if document_store.get_document_count() == 0:
        archive_folder = "./archive_texts"
        documents = []
        
        for filename in os.listdir(archive_folder):
            if filename.endswith(".txt"):
                try:
                    with open(os.path.join(archive_folder, filename), "r", encoding="utf-8") as file:
                        content = file.read()
                        metadata, article_content = parse_article_content(content)
                        
                        # Extract date from filename
                        file_date = None
                        for part in filename.split('_'):
                            if len(part) == 8 and part.isdigit():
                                year = part[:4]
                                month = part[4:6]
                                day = part[6:]
                                file_date = f"{year}-{month}-{day}"
                                break
                        
                        documents.append({
                            "content": article_content,
                            "meta": {
                                "name": filename,
                                "title": metadata.get("title", os.path.splitext(filename)[0]),
                                "author": metadata.get("author", "Unknown"),
                                "publishDate": metadata.get("date", file_date),
                                "source": "archive"
                            }
                        })
                        print(f"Processed: {filename}")
                except Exception as e:
                    print(f"Error processing {filename}: {str(e)}")
        
        if documents:
            # Write documents in batches
            batch_size = 50
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                document_store.write_documents(batch)
                print(f"Indexed batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")

# Rest of your existing code remains the same