"""Context manager utilities for VIBE Core memory operations."""

from __future__ import annotations

from typing import Any, Iterable


class MemoryContext:
    """Context manager for memory search operations.
    
    Provides a context manager interface for searching and retrieving
    relevant memory chunks based on a query.
    """

    def __init__(self, memory: Any, query: str, top_k: int = 3) -> None:
        """Initialize the memory context.
        
        Args:
            memory: Memory store instance
            query: Search query string
            top_k: Number of top results to return
        """
        self.memory = memory
        self.query = query
        self.top_k = top_k
        self.results: Iterable[Any] = []

    def __enter__(self) -> Iterable[Any]:
        """Enter the context and perform the search.
        
        Returns:
            Search results from memory
        """
        self.results = self.memory.search(self.query, self.top_k)
        return self.results

    def __exit__(self, exc_type, exc, tb) -> bool:
        """Exit the context manager.
        
        Returns:
            False to propagate any exceptions
        """
        return False


class ContextManager:
    """Manage context retrieval from memory stores.
    
    Provides utilities for querying memory and hydrating memory
    from text content.
    """

    def __init__(self, memory: Any, top_k: int = 3) -> None:
        """Initialize the context manager.
        
        Args:
            memory: Memory store instance
            top_k: Default number of results to return
        """
        self.memory = memory
        self.top_k = top_k

    def for_query(self, query: str) -> MemoryContext:
        """Create a memory context for a specific query.
        
        Args:
            query: Search query string
            
        Returns:
            MemoryContext instance for the query
        """
        return MemoryContext(self.memory, query, self.top_k)

    def hydrate_from_text(
        self, text: str, author: str = "system", context: str = ""
    ) -> None:
        """Split text by lines and add to memory.
        
        Args:
            text: Text content to add to memory
            author: Author of the content
            context: Context category for the content
        """
        for line in filter(None, (l.strip() for l in text.splitlines())):
            if line:  # Skip empty lines
                self.memory.add(line, author=author, context=context)
