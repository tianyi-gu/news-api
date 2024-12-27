from typing import List, Dict, Any
from datetime import datetime

def update_document(document_store, doc_id: str, updates: Dict[str, Any]):
    """Update an existing document"""
    try:
        document = document_store.get_document_by_id(doc_id)
        if document:
            document.meta.update(updates)
            document_store.write_documents([document])
            return True
    except Exception as e:
        print(f"Error updating document {doc_id}: {str(e)}")
    return False

def delete_document(document_store, doc_id: str):
    """Delete a document"""
    try:
        document_store.delete_documents([doc_id])
        return True
    except Exception as e:
        print(f"Error deleting document {doc_id}: {str(e)}")
    return False

def search_documents(document_store, query: str, filters: Dict = None):
    """Search documents with optional filters"""
    try:
        return document_store.query(
            query=query,
            filters=filters,
            top_k=10
        )
    except Exception as e:
        print(f"Error searching documents: {str(e)}")
        return []