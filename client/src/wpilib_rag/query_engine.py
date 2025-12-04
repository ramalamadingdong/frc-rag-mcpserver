"""Query engine for WPILib documentation with version and language filtering."""

import json
import logging
from typing import Optional

from .config import (
    VOYAGE_API_KEY,
    DEFAULT_TOP_K,
    DEFAULT_VERSION,
    SUPPORTED_LANGUAGES,
    get_chroma_client,
    get_or_create_collection,
)
from .embedding_client import get_embedding_client

logger = logging.getLogger(__name__)


class WPILibQueryEngine:
    """Query engine for WPILib documentation with metadata filtering.
    
    This is a retrieval-only engine - it returns relevant documentation chunks
    with embeddings and metadata for the client to use for answer generation.
    """
    
    def __init__(self):
        """Initialize query engine."""
        # Initialize Chroma (works without API key for retrieval)
        self.chroma_client = get_chroma_client()
        self.collection = get_or_create_collection(self.chroma_client)
        
        # We query ChromaDB directly - no need for LlamaIndex wrapper
        # This avoids any OpenAI embedding model initialization
        logger.info("Using custom embedding_client with VOYAGE_API_KEY")
    
    def query(
        self,
        question: str,
        version: str,
        language: str,
        top_k: int = DEFAULT_TOP_K,
    ) -> str:
        """Retrieve relevant WPILib documentation chunks with version and language filtering.
        
        This method retrieves relevant documentation chunks and returns them as JSON
        for the client to use in generating answers. The client will handle all
        answer generation.
        
        Args:
            question: User's question (used for semantic search)
            version: WPILib version (e.g., "2025", "2024")
            language: Programming language (Java, Python, C++, cpp, or API Reference)
            top_k: Number of chunks to retrieve (default: 8)
        
        Returns:
            JSON string containing retrieved documentation chunks with metadata and embeddings
        """
        # Validate language
        if language not in SUPPORTED_LANGUAGES:
            raise ValueError(
                f"Unsupported language: {language}. "
                f"Supported languages: {', '.join(SUPPORTED_LANGUAGES)}"
            )
        
        # Map language for database query (database uses "C++" but config allows "cpp")
        db_language = "C++" if language == "cpp" else language
        
        # Generate query embedding FIRST using our custom embedding client
        query_embedding = None
        if VOYAGE_API_KEY:
            try:
                # Use embedding client with direct Voyage API
                embedding_client = get_embedding_client()
                query_embedding = embedding_client.embed(question)
                if not query_embedding:
                    raise ValueError("Embedding generation returned None")
            except Exception as e:
                # If embedding generation fails, we can't do semantic search
                logger.error(f"Could not generate query embedding: {e}")
                return json.dumps({
                    "error": f"Could not generate query embedding: {str(e)}",
                    "chunks": [],
                    "query_embedding": None,
                })
        else:
            # No API key available
            return json.dumps({
                "error": "No Voyage API key configured. Set VOYAGE_API_KEY environment variable.",
                "chunks": [],
                "query_embedding": None,
            })
        
        # Use the query embedding to retrieve similar documents from ChromaDB directly
        # We bypass LlamaIndex's retriever and query ChromaDB directly to avoid OpenAI dependency
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where={
                    "$and": [
                        {"version": {"$eq": version}},
                        {"language": {"$eq": db_language}},
                    ]
                },
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return json.dumps({
                "error": f"Database query failed: {str(e)}",
                "chunks": [],
                "query_embedding": query_embedding,
            })
        
        # Check if we got results
        if not results or not results.get("documents") or not results["documents"][0]:
            return json.dumps({
                "error": f"No documentation found for version {version} and language {language}",
                "chunks": [],
                "query_embedding": query_embedding,
            })
        
        # Format retrieved chunks as structured data
        chunks = []
        
        # ChromaDB returns results as lists
        documents = results["documents"][0] if results.get("documents") else []
        metadatas = results["metadatas"][0] if results.get("metadatas") else []
        
        for i, text in enumerate(documents):
            metadata = metadatas[i] if i < len(metadatas) else {}
            
            chunk_data = {
                "text": text,
                "metadata": {
                    "version": metadata.get("version", version),
                    "language": metadata.get("language", db_language),
                    "url": metadata.get("url", ""),
                    "last_updated": metadata.get("last_updated", ""),
                    "title": metadata.get("title", ""),
                    "component": metadata.get("component", ""),
                },
            }
            chunks.append(chunk_data)
        
        # Return as JSON for client to process
        result = {
            "chunks": chunks,
            "query_embedding": query_embedding,
            "version": version,
            "language": language,
            "count": len(chunks),
        }
        
        return json.dumps(result, indent=2)
    
    def get_available_versions(self) -> list[str]:
        """Get list of available versions in the database."""
        # Query collection for distinct versions
        all_data = self.collection.get()
        versions = set()
        
        if all_data.get("metadatas"):
            for metadata in all_data["metadatas"]:
                if "version" in metadata:
                    versions.add(metadata["version"])
        
        return sorted(list(versions), reverse=True)  # Most recent first
    
    def get_latest_version(self) -> str:
        """Return the latest version (configured default if DB empty)."""
        versions = self.get_available_versions()
        if versions:
            return versions[0]
        return DEFAULT_VERSION
    
    def get_available_languages(self, version: Optional[str] = None) -> list[str]:
        """Get list of available languages for a version (or all languages)."""
        if version:
            all_data = self.collection.get(where={"version": version})
        else:
            all_data = self.collection.get()
        
        languages = set()
        
        if all_data.get("metadatas"):
            for metadata in all_data["metadatas"]:
                if "language" in metadata:
                    languages.add(metadata["language"])
        
        return sorted(list(languages))
    
    def embed_query(self, query: str) -> str:
        """Generate embedding for a query using Voyage AI direct API.
        
        This method allows clients to get embeddings for their queries,
        which they can use for client-side processing or caching.
        
        Args:
            query: The text query to embed
        
        Returns:
            JSON string containing the embedding vector or error message
        """
        if not VOYAGE_API_KEY:
            return json.dumps({
                "error": "Voyage API key not configured. Set VOYAGE_API_KEY environment variable.",
            })
        
        try:
            # Use embedding client with direct Voyage API
            embedding_client = get_embedding_client()
            embedding = embedding_client.embed(query)
            
            if embedding:
                from .config import VOYAGE_MODEL
                return json.dumps({
                    "embedding": embedding,
                    "model": VOYAGE_MODEL,
                    "dimension": len(embedding),
                }, indent=2)
            else:
                return json.dumps({
                    "error": "No embedding generated",
                })
        except Exception as e:
            return json.dumps({
                "error": f"Failed to generate embedding: {str(e)}",
            })

