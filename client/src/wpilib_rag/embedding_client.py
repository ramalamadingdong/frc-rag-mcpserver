"""Embedding client for Voyage AI direct API access.

NOTE: This module handles embedding generation only. Database downloads are handled
separately in database_loader.py and do NOT require any API key.
"""

import logging
from typing import Optional

import voyageai

from .config import VOYAGE_API_KEY, VOYAGE_MODEL

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """Client for generating embeddings via direct Voyage AI API.
    
    Requires VOYAGE_API_KEY to be set for embedding generation.
    
    Note: Database downloads are separate and don't use this client.
    """
    
    def __init__(self):
        """Initialize embedding client."""
        self.direct_api_key = VOYAGE_API_KEY
        self.model = VOYAGE_MODEL
        self._client: Optional[voyageai.Client] = None
        
        if self.direct_api_key:
            try:
                self._client = voyageai.Client(api_key=self.direct_api_key)
                logger.info("Using direct Voyage API with VOYAGE_API_KEY")
            except Exception as exc:
                logger.error(f"Failed to initialize Voyage AI client: {exc}")
        else:
            logger.error("No embedding service configured - VOYAGE_API_KEY is REQUIRED for embedding generation")
    
    def embed(self, query: str) -> Optional[list[float]]:
        """Generate embedding for a query.
        
        Args:
            query: Text to embed
        
        Returns:
            Embedding vector or None if generation failed
        """
        # Use direct API if key available
        if self._client:
            return self._embed_direct(query)
        
        logger.error("No embedding method available - VOYAGE_API_KEY is required")
        return None
    
    def _embed_direct(self, query: str) -> Optional[list[float]]:
        """Generate embedding via direct Voyage API."""
        try:
            result = self._client.embed([query], model=self.model)  # type: ignore[union-attr]
            
            if result.embeddings:
                return result.embeddings[0]
            else:
                logger.error("No embedding returned from Voyage API")
                return None
        except Exception as e:
            logger.error(f"Direct API call failed: {e}")
            return None


# Global client instance
_embedding_client: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """Get or create global embedding client."""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client

