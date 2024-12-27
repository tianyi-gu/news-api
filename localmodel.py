from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional, List
from pydantic import BaseModel
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import BM25Retriever, TransformersReader
from haystack.pipelines import ExtractiveQAPipeline
from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering
import os

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_article_content(content):
    """Parse article content with metadata"""
    lines = content.split('\n')
    metadata = {}
    content_lines = []
    parsing_content = False
    
    for line in lines:
        if line.strip() == '---':
            parsing_content = True
            continue
        if not parsing_content:
            if ':' in line:
                key, value = line.split(':', 1)
                metadata[key.strip().lower()] = value.strip()
        else:
            content_lines.append(line)
    
    return metadata, '\n'.join(content_lines)

def init_document_store():
    archive_folder = "./archive_texts"
    
    # Check if directory exists
    if not os.path.exists(archive_folder):
        print(f"Error: Directory '{archive_folder}' does not exist")
        return
    
    # Get list of text files
    text_files = [f for f in os.listdir(archive_folder) if f.endswith(".txt")]
    if not text_files:
        print(f"Error: No .txt files found in '{archive_folder}'")
        return
    
    print(f"Found {len(text_files)} text files")
    
    if not document_store.get_document_count():
        documents = []
        for filename in text_files:
            try:
                with open(os.path.join(archive_folder, filename), "r", encoding="utf-8") as file:
                    content = file.read()
                    if not content.strip():
                        print(f"Warning: Empty file {filename}")
                        continue
                    
                    # Parse the metadata and content
                    metadata, article_content = parse_article_content(content)
                    
                    # Extract date from filename if it contains a date (e.g., 20061117)
                    file_date = None
                    for part in filename.split('_'):
                        if len(part) == 8 and part.isdigit():  # Format: YYYYMMDD
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
                            "publishDate": metadata.get("date", file_date)  # Use file date as fallback
                        }
                    })
                    print(f"Successfully processed: {filename}")
                    print(f"Title: {metadata.get('title', 'No title')}")
                    print(f"Author: {metadata.get('author', 'Unknown')}")
                    print(f"Date: {metadata.get('date', file_date)}")
                    print("---")
            
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
        
        print(f"Attempting to write {len(documents)} documents to store")
        if documents:
            document_store.write_documents(documents)
            print("Successfully wrote documents to store")
        else:
            print("No valid documents to write to store")

# Initialize Haystack components
model_dir = "./models/distilbert-base-uncased-distilled-squad"
document_store = InMemoryDocumentStore(use_bm25=True)
retriever = BM25Retriever(document_store, top_k=10)
reader = TransformersReader(
    model_name_or_path=model_dir,
    tokenizer=model_dir,
    context_window_size=500
)

# Initialize the document store with articles
init_document_store()

# Update the get_articles endpoint to use document store
@app.get("/articles")
async def get_articles(page: int = 1, limit: int = 10):
    documents = document_store.get_all_documents()
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_docs = documents[start_idx:end_idx]
    
    results = [{
        "id": doc.id,
        "title": doc.meta.get("title", "Untitled"),
        "content": doc.content[:500],  # Preview of first 500 chars
        "publishDate": "-".join(doc.meta.get("publishDate", [])) if doc.meta.get("publishDate") else None,
        "author": doc.meta.get("author", "Unknown")
    } for doc in paginated_docs]
    
    return {
        "results": results,
        "total": len(documents),
        "page": page,
        "limit": limit
    }

@app.get("/articles/{article_id}")
async def get_article(article_id: str):
    document = document_store.get_document_by_id(article_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Article not found")
    
    return {
        "id": document.id,
        "title": document.meta.get("title", "Untitled"),
        "content": document.content,
        "publishDate": "-".join(document.meta.get("publishDate", [])) if document.meta.get("publishDate") else None,
        "author": document.meta.get("author", "Unknown")
    }

def main():
    # Define the models folder
    model_dir = "./models/distilbert-base-uncased-distilled-squad"
    os.makedirs(model_dir, exist_ok=True)

    # Load model if not already downloaded
    if not os.path.exists(os.path.join(model_dir, "config.json")):
        print("Downloading and saving the model...")
        tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased-distilled-squad")
        model = DistilBertForQuestionAnswering.from_pretrained("distilbert-base-uncased-distilled-squad")
        tokenizer.save_pretrained(model_dir)
        model.save_pretrained(model_dir)
    else:
        print("Loading the model from local directory...")
        tokenizer = DistilBertTokenizer.from_pretrained(model_dir)
        model = DistilBertForQuestionAnswering.from_pretrained(model_dir)

    # Create pipeline
    pipeline = ExtractiveQAPipeline(reader=reader, retriever=retriever)

    # Test query
    query = "When was Tang Institute established?"
    result = pipeline.run(query=query, params={"Retriever": {"top_k": 5}, "Reader": {"top_k": 1}})

    if result["answers"]:
        print("Answer:", result["answers"][0].answer)
        print("Context:", result["answers"][0].context)
    else:
        print("No answer found.")

if __name__ == "__main__":
    main()
