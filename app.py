from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from haystack.document_stores import InMemoryDocumentStore
from haystack.nodes import BM25Retriever, TransformersReader
from haystack.pipelines import ExtractiveQAPipeline
from transformers import DistilBertTokenizer, DistilBertForQuestionAnswering
from haystack.document_stores import MongoDBDocumentStore
from dotenv import load_dotenv
import os

load_dotenv()

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

# Create pipeline - Move this up before the endpoints
pipeline = ExtractiveQAPipeline(reader=reader, retriever=retriever)
print("Pipeline initialized successfully")  # Debug print

# Test the pipeline with a simple query
test_query = "What is this about?"
try:
    test_result = pipeline.run(
        query=test_query,
        params={"Retriever": {"top_k": 1}, "Reader": {"top_k": 1}}
    )
    print("Pipeline test successful:", test_result)
except Exception as e:
    print("Pipeline test failed:", str(e))

@app.get("/articles")
async def get_articles(page: int = 1, limit: int = 10):
    documents = document_store.get_all_documents()
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_docs = documents[start_idx:end_idx]
    
    results = [{
        "id": doc.id,
        "title": doc.meta.get("title", "Untitled"),
        "content": doc.content[:2000],  # Increased from 500 to 2000 characters
        "publishDate": doc.meta.get("publishDate", None),
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
        "publishDate": document.meta.get("publishDate", None),
        "author": document.meta.get("author", "Unknown")
    }

# Add text search functionality
@app.get("/search")
def search_articles(query: str):
    try:
        print(f"Received search query: {query}")
        
        # Use BM25 retriever to find relevant documents
        retrieved_docs = retriever.retrieve(
            query=query,
            top_k=5,  # Retrieve top 5 most relevant documents
        )
        
        # Format the results
        search_results = []
        for doc in retrieved_docs:
            # Find the position of the query terms in the content for context
            content = doc.content.lower()
            query_terms = query.lower().split()
            
            # Find the first occurrence of any query term
            positions = []
            for term in query_terms:
                pos = content.find(term)
                if pos != -1:
                    positions.append(pos)
            
            # Get context around the first match
            if positions:
                start_pos = min(positions)
                # Get some context before and after the match
                start = max(0, start_pos - 100)
                end = min(len(content), start_pos + 300)
                context = content[start:end]
            else:
                # If no direct match, show the beginning of the content
                context = content[:400]
            
            search_results.append({
                "id": doc.id,
                "title": doc.meta.get("title", "Untitled"),
                "preview": f"...{context}...",
                "score": doc.score,
                "publishDate": doc.meta.get("publishDate", None),
                "author": doc.meta.get("author", "Unknown")
            })
        
        return {
            "results": search_results,
            "total": len(search_results),
            "query": query
        }
            
    except Exception as e:
        print(f"Error in search: {str(e)}")
        return {"error": str(e)}

# AI-powered question answering
@app.get("/query")
def query_pipeline(query: str):
    try:
        print(f"Received QA query: {query}")
        print(f"Document store has {document_store.get_document_count()} documents")
        
        # Run the full QA pipeline with corrected parameters
        result = pipeline.run(
            query=query,
            params={
                "Retriever": {
                    "top_k": 5  # Retrieve more documents
                },
                "Reader": {
                    "top_k": 3  # Get multiple answer candidates
                }
            }
        )
        
        print("Pipeline result:", result)
        print("Answers:", result.get("answers", []))
        
        if result["answers"]:
            # Get all answers and combine them for a more comprehensive response
            answers = result["answers"]
            main_answer = answers[0]
            
            # Combine the answers into a more detailed response
            combined_answer = main_answer.answer
            if len(answers) > 1:
                combined_answer += "\n\nAdditional context:\n" + "\n".join(
                    [f"• {ans.answer}" for ans in answers[1:]]
                )
            
            # Get the full document for context
            doc = document_store.get_document_by_id(main_answer.document_ids[0])
            
            return {
                "answer": combined_answer,
                "confidence": main_answer.score,
                "context": main_answer.context,
                "source": {
                    "id": doc.id if doc else None,
                    "title": doc.meta.get("title", "Untitled") if doc else None,
                    "author": doc.meta.get("author", "Unknown") if doc else None,
                    "publishDate": doc.meta.get("publishDate", None) if doc else None
                }
            }
        else:
            # If no specific answer found, return relevant documents
            retrieved_docs = retriever.retrieve(
                query=query,
                top_k=3
            )
            
            # Create a summary from the retrieved documents
            relevant_excerpts = []
            for doc in retrieved_docs:
                # Get a larger preview of each document
                preview = doc.content[:1000]
                relevant_excerpts.append({
                    "title": doc.meta.get("title", "Untitled"),
                    "excerpt": preview,
                    "author": doc.meta.get("author", "Unknown"),
                    "date": doc.meta.get("publishDate", None)
                })
            
            return {
                "answer": "I couldn't find a specific answer, but here are relevant passages from the articles:",
                "confidence": 0,
                "context": "\n\n".join([f"From '{exc['title']}':\n{exc['excerpt']}" for exc in relevant_excerpts]),
                "source": {
                    "id": retrieved_docs[0].id if retrieved_docs else None,
                    "title": retrieved_docs[0].meta.get("title", "Untitled") if retrieved_docs else None,
                    "author": retrieved_docs[0].meta.get("author", "Unknown") if retrieved_docs else None,
                    "publishDate": retrieved_docs[0].meta.get("publishDate", None) if retrieved_docs else None
                } if retrieved_docs else None,
                "additional_sources": relevant_excerpts[1:] if len(relevant_excerpts) > 1 else []
            }
            
    except Exception as e:
        print(f"Error in QA pipeline: {str(e)}")
        print(f"Full error details:", e.__class__.__name__)
        import traceback
        print(traceback.format_exc())
        return {
            "answer": "Sorry, I encountered an error while processing your question.",
            "confidence": 0,
            "context": str(e),
            "error": str(e)
        }

if __name__ == "__main__":
    # Initialize the model if not already downloaded
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
    
    # Run the FastAPI application
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
