"""Persistent memory using a JSON vector store.

This module provides a persistent memory system that stores text chunks with
embeddings in a JSON file, enabling semantic search and context management.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from openai import OpenAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class MemoryEntry(BaseModel):
    """A single memory entry with text, embedding, and metadata."""
    
    text: str = Field(..., description="The stored text content")
    embedding: List[float] = Field(..., description="Vector embedding of the text")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    author: str = Field(default="system", description="Author of the memory entry")
    context: str = Field(default="", description="Context information")


class MemorySearchResult(BaseModel):
    """Result from a memory search operation."""
    
    entry: MemoryEntry = Field(..., description="The matching memory entry")
    score: float = Field(..., description="Similarity score (0-1)")


class JsonVectorMemory:
    """Store text chunks with embeddings in a JSON file.
    
    This class provides persistent storage for text chunks with vector embeddings,
    enabling semantic search capabilities for context-aware AI interactions.
    
    Example:
        >>> memory = JsonVectorMemory("memory.json")
        >>> memory.add("Important project requirement", author="developer")
        >>> results = memory.search("project needs", top_k=3)
        >>> for result in results:
        ...     print(f"Score: {result.score:.3f}, Text: {result.entry.text}")
    """

    def __init__(
        self, 
        path: str | Path, 
        model: str = "text-embedding-3-small",
        client: Optional[OpenAI] = None
    ) -> None:
        """Initialize the memory store.
        
        Args:
            path: Path to the JSON file for persistent storage
            model: OpenAI embedding model to use
            client: Optional OpenAI client instance
        """
        self.path = Path(path)
        self.model = model
        self.client = client or OpenAI()
        self.entries: List[MemoryEntry] = []
        
        # Create parent directories if they don't exist
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.path.exists():
            self._load()

    def _load(self) -> None:
        """Load memory entries from the JSON file."""
        try:
            data = json.loads(self.path.read_text(encoding='utf-8'))
            self.entries = []
            
            for item in data:
                # Handle legacy format
                if "metadata" not in item:
                    item["metadata"] = {
                        "author": item.get("author", "system"),
                        "context": item.get("context", ""),
                        "timestamp": item.get("timestamp", datetime.now(timezone.utc).isoformat())
                    }
                
                # Create MemoryEntry from the data
                entry = MemoryEntry(
                    text=item["text"],
                    embedding=item["embedding"],
                    metadata=item.get("metadata", {}),
                    timestamp=item.get("timestamp", datetime.now(timezone.utc).isoformat()),
                    author=item.get("author", "system"),
                    context=item.get("context", "")
                )
                self.entries.append(entry)
                
            logger.info(f"Loaded {len(self.entries)} memory entries from {self.path}")
            
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.warning(f"Failed to parse memory store {self.path}: {e}. Starting fresh.")
            self.entries = []

    def _save(self) -> None:
        """Save memory entries to the JSON file."""
        try:
            # Convert to dictionary format for JSON serialization
            data = []
            for entry in self.entries:
                data.append({
                    "text": entry.text,
                    "embedding": entry.embedding,
                    "metadata": entry.metadata,
                    "timestamp": entry.timestamp,
                    "author": entry.author,
                    "context": entry.context
                })
            
            self.path.write_text(json.dumps(data, indent=2), encoding='utf-8')
            logger.debug(f"Saved {len(self.entries)} memory entries to {self.path}")
            
        except Exception as e:
            logger.error(f"Failed to save memory store to {self.path}: {e}")
            raise

    def _embed(self, text: str) -> List[float]:
        """Generate embedding for the given text.
        
        Args:
            text: Text to embed
            
        Returns:
            List of embedding values
            
        Raises:
            Exception: If embedding generation fails
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"Failed to generate embedding for text: {e}")
            raise

    def add(
        self,
        text: str,
        author: str = "system",
        context: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Add text to memory with versioning metadata.
        
        Args:
            text: The text content to store
            author: Author of the memory entry
            context: Context information for the entry
            metadata: Additional metadata to store
        """
        if not text.strip():
            logger.warning("Attempted to add empty text to memory")
            return
            
        try:
            embedding = self._embed(text)
            
            entry_metadata = metadata.copy() if metadata else {}
            
            entry = MemoryEntry(
                text=text,
                embedding=embedding,
                metadata=entry_metadata,
                author=author,
                context=context
            )
            
            self.entries.append(entry)
            self._save()
            
            logger.debug(f"Added memory entry with {len(embedding)} dimensions")
            
        except Exception as e:
            logger.error(f"Failed to add memory entry: {e}")
            raise

    def search(self, query: str, top_k: int = 3) -> List[MemorySearchResult]:
        """Search for similar entries using semantic similarity.
        
        Args:
            query: Search query text
            top_k: Maximum number of results to return
            
        Returns:
            List of search results sorted by similarity score (highest first)
        """
        if not self.entries:
            logger.debug("No entries in memory to search")
            return []
            
        if not query.strip():
            logger.warning("Empty query provided for memory search")
            return []
            
        try:
            query_embedding = self._embed(query)
            scored_results = []
            
            for entry in self.entries:
                score = self._cosine_similarity(query_embedding, entry.embedding)
                result = MemorySearchResult(entry=entry, score=score)
                scored_results.append(result)
            
            # Sort by score (highest first) and return top_k
            scored_results.sort(key=lambda x: x.score, reverse=True)
            results = scored_results[:top_k]
            
            logger.debug(f"Found {len(results)} memory results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search memory: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First vector
            vec2: Second vector
            
        Returns:
            Cosine similarity score between 0 and 1
        """
        if len(vec1) != len(vec2):
            logger.warning("Vector dimension mismatch in similarity calculation")
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = sum(a * a for a in vec1) ** 0.5
        norm2 = sum(a * a for a in vec2) ** 0.5
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
            
        return dot_product / (norm1 * norm2)

    def clear(self) -> None:
        """Clear all memory entries."""
        self.entries.clear()
        self._save()
        logger.info("Cleared all memory entries")

    def size(self) -> int:
        """Get the number of memory entries.
        
        Returns:
            Number of entries in memory
        """
        return len(self.entries)

    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """Get the most recent memory entries.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent memory entries, newest first
        """
        # Sort by timestamp (newest first)
        sorted_entries = sorted(
            self.entries, 
            key=lambda x: x.timestamp, 
            reverse=True
        )
        return sorted_entries[:limit]

    def filter_by_author(self, author: str) -> List[MemoryEntry]:
        """Get all entries by a specific author.
        
        Args:
            author: Author name to filter by
            
        Returns:
            List of memory entries by the specified author
        """
        return [entry for entry in self.entries if entry.author == author]

    def filter_by_context(self, context: str) -> List[MemoryEntry]:
        """Get all entries with a specific context.
        
        Args:
            context: Context string to filter by
            
        Returns:
            List of memory entries with the specified context
        """
        return [entry for entry in self.entries if context in entry.context]


# Backward compatibility function
def create_memory(path: str | Path, model: str = "text-embedding-3-small") -> JsonVectorMemory:
    """Create a JsonVectorMemory instance.
    
    Args:
        path: Path to the memory file
        model: OpenAI embedding model to use
        
    Returns:
        Configured JsonVectorMemory instance
    """
    return JsonVectorMemory(path, model)
