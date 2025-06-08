"""Claude response parser for VIBE Core.

This module provides utilities for parsing Claude API responses
that contain file generation instructions in the format:

Fichier: path/to/file
<file content>
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class FileObject:
    """Represents a file parsed from Claude's output.
    
    Attributes:
        path: Relative path for the file
        content: File content as string
    """

    path: str
    content: str
    
    def write_to(self, base_dir: Path, dry_run: bool = False) -> Path:
        """Write the file to the specified base directory.
        
        Args:
            base_dir: Base directory to write the file to
            dry_run: If True, don't actually write the file
            
        Returns:
            Path where the file was (or would be) written
        """
        target = base_dir / self.path
        
        if dry_run:
            logging.info("[DRY RUN] Would write %s", target)
            return target
            
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.content)
        logging.info("Wrote %s", target)
        return target


class ClaudeResponseParser:
    """Parser for Claude API responses containing file generation instructions."""
    
    def __init__(self) -> None:
        """Initialize the parser."""
        self.logger = logging.getLogger(__name__)
    
    def parse(self, text: str) -> List[FileObject]:
        """Parse Claude response text into file objects.

        Lines beginning with ``Fichier:`` signal a new file. The following lines
        until the next ``Fichier:`` are considered the file content.

        Args:
            text: Raw response text from Claude

        Returns:
            List of FileObject instances
        """
        files: List[FileObject] = []
        current_path: str | None = None
        buffer: List[str] = []
        stray: List[str] = []

        for line_no, line in enumerate(text.splitlines(), 1):
            if line.startswith("Fichier:"):
                if stray:
                    self.logger.warning(
                        "Ignoring %d stray lines before header at line %d", 
                        len(stray), line_no
                    )
                    stray = []
                    
                if current_path is not None:
                    files.append(FileObject(current_path, "\n".join(buffer).rstrip()))
                    buffer = []
                    
                path = line.split(":", 1)[1].strip()
                if not path:
                    self.logger.warning("Missing file path at line %d", line_no)
                    current_path = None
                else:
                    current_path = path
            else:
                if current_path is None:
                    stray.append(line)
                else:
                    buffer.append(line)

        if stray:
            self.logger.warning("Ignoring %d stray lines at end of response", len(stray))
            
        if current_path is not None:
            files.append(FileObject(current_path, "\n".join(buffer).rstrip()))
        elif buffer:
            self.logger.warning(
                "Ignoring %d trailing lines without file header", len(buffer)
            )

        return files
    
    def parse_and_write(
        self, text: str, output_dir: Path, dry_run: bool = False
    ) -> List[FileObject]:
        """Parse response and write files to output directory.
        
        Args:
            text: Raw response text from Claude
            output_dir: Directory to write files to
            dry_run: If True, don't actually write files
            
        Returns:
            List of FileObject instances that were processed
        """
        files = self.parse(text)
        
        for file_obj in files:
            file_obj.write_to(output_dir, dry_run)
            
        return files


# Backward compatibility functions
def parse_claude_response(text: str) -> List[FileObject]:
    """Parse Claude response text into file objects.
    
    This is a backward compatibility function that uses the new parser.
    
    Args:
        text: Raw response text from Claude
        
    Returns:
        List of FileObject instances
    """
    parser = ClaudeResponseParser()
    return parser.parse(text)


def parse_response_file(source: Path, out_dir: Path, dry_run: bool = False) -> None:
    """Parse source text file and write files to out_dir.
    
    Args:
        source: Path to text response file from Claude
        out_dir: Directory to write files to
        dry_run: If True, preview actions without writing
    """
    text = source.read_text()
    parser = ClaudeResponseParser()
    parser.parse_and_write(text, out_dir, dry_run)
