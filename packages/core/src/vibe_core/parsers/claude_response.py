"""Claude response parser for VIBE Core."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class FileObject:
    """Represents a file parsed from Claude's output."""

    path: str
    content: str

    def __post_init__(self):
        """Validate the file object."""
        if not self.path:
            raise ValueError("File path cannot be empty")


class ClaudeResponseParser:
    """Parser for Claude response text containing file definitions."""

    def __init__(self, file_marker: str = "Fichier:"):
        """Initialize the parser.
        
        Args:
            file_marker: The marker that indicates a new file definition
        """
        self.file_marker = file_marker

    def parse(self, text: str) -> List[FileObject]:
        """Parse Claude response text into file objects.

        Lines beginning with ``Fichier:`` signal a new file. The following lines
        until the next ``Fichier:`` are considered the file content.

        Args:
            text: Raw response text from Claude.

        Returns:
            List of FileObject instances representing parsed files.
        """
        files: List[FileObject] = []
        current_path: str | None = None
        buffer: list[str] = []
        stray: list[str] = []

        for line_no, line in enumerate(text.splitlines(), 1):
            if line.startswith(self.file_marker):
                if stray:
                    logger.warning(
                        "Ignoring %d stray lines before header at line %d", 
                        len(stray), line_no
                    )
                    stray = []
                
                if current_path is not None:
                    files.append(FileObject(current_path, "\n".join(buffer).rstrip()))
                    buffer = []
                
                path = line.split(":", 1)[1].strip()
                if not path:
                    logger.warning("Missing file path at line %d", line_no)
                    current_path = None
                else:
                    current_path = path
            else:
                if current_path is None:
                    stray.append(line)
                else:
                    buffer.append(line)

        if stray:
            logger.warning("Ignoring %d stray lines at end of response", len(stray))
        
        if current_path is not None:
            files.append(FileObject(current_path, "\n".join(buffer).rstrip()))
        elif buffer:
            logger.warning("Ignoring %d trailing lines without file header", len(buffer))

        return files

    def parse_response_file(
        self, 
        source: Path, 
        out_dir: Path, 
        dry_run: bool = False
    ) -> List[FileObject]:
        """Parse a response file and optionally write files to output directory.
        
        Args:
            source: Path to the response file
            out_dir: Directory to write parsed files
            dry_run: If True, only log what would be done
            
        Returns:
            List of parsed FileObject instances
        """
        if not source.exists():
            raise FileNotFoundError(f"Response file not found: {source}")
            
        text = source.read_text(encoding='utf-8')
        files = self.parse(text)
        
        if not dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
            
        for file_obj in files:
            target = out_dir / file_obj.path
            if dry_run:
                logger.info("[dry-run] Would write %s", target)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(file_obj.content, encoding='utf-8')
                logger.info("Wrote %s", target)
                
        return files


# Convenience function for backwards compatibility
def parse_claude_response(text: str) -> List[FileObject]:
    """Parse Claude response text into file objects.
    
    This is a convenience function that maintains backwards compatibility
    with the original VIBE-CODING-INIT implementation.
    
    Args:
        text: Raw response text from Claude
        
    Returns:
        List of FileObject instances
    """
    parser = ClaudeResponseParser()
    return parser.parse(text)


def create_parser(file_marker: str = "Fichier:") -> ClaudeResponseParser:
    """Create a Claude response parser instance.
    
    Args:
        file_marker: The marker that indicates a new file definition
        
    Returns:
        ClaudeResponseParser instance
    """
    return ClaudeResponseParser(file_marker=file_marker)
