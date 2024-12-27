from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="News API",
    description="API for searching and querying news articles",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
client = MongoClient(os.getenv("MONGODB_URI"))
db = client[os.getenv("DB_NAME", "news_db")]
collection = db[os.getenv("COLLECTION_NAME", "articles")]

# API endpoints
@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "News API is running"}

@app.get("/articles")
async def get_articles(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=50)):
    """Get paginated list of articles"""
    try:
        skip = (page - 1) * limit
        total = collection.count_documents({})
        
        articles = list(collection.find({})
                       .sort("publish_date", -1)
                       .skip(skip)
                       .limit(limit))
        
        # Convert ObjectId to string for JSON serialization
        for article in articles:
            article["_id"] = str(article["_id"])
        
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "articles": articles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search")
async def search_articles(query: str):
    """Search articles by keyword"""
    try:
        # Text search using MongoDB
        results = list(collection.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})])
        .limit(10))
        
        # Convert ObjectId to string
        for result in results:
            result["_id"] = str(result["_id"])
        
        return {
            "results": results,
            "count": len(results),
            "query": query
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/query")
async def query_articles(query: str):
    """AI-powered article querying"""
    try:
        # First, find relevant documents
        relevant_docs = list(collection.find(
            {"$text": {"$search": query}},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})])
        .limit(3))
        
        if not relevant_docs:
            return {
                "answer": "I couldn't find any relevant information for your query.",
                "confidence": 0,
                "context": None
            }
        
        # Convert ObjectId to string
        for doc in relevant_docs:
            doc["_id"] = str(doc["_id"])
        
        # For now, return the most relevant document
        best_match = relevant_docs[0]
        
        return {
            "answer": best_match["content"][:500],  # First 500 characters as answer
            "confidence": best_match.get("score", 0),
            "context": best_match["content"],
            "source": {
                "id": best_match["_id"],
                "title": best_match.get("title", "Untitled"),
                "author": best_match.get("author", "Unknown"),
                "publish_date": best_match.get("publish_date")
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Only run the server directly in development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)