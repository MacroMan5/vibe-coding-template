"""Task executor for managing files and directories in VIBE projects.

This module provides utilities for executing file operations with proper error
handling, logging, and validation for VIBE code generation workflows.
"""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class FileOperation(BaseModel):
    """Represents a file operation to be executed."""
    
    operation: str = Field(..., description="Type of operation: create, modify, delete, copy, move")
    path: str = Field(..., description="Target file path relative to base directory")
    content: Optional[str] = Field(None, description="File content for create/modify operations")
    source: Optional[str] = Field(None, description="Source path for copy/move operations")
    backup: bool = Field(default=True, description="Whether to create backup before modifying")
    
    @validator('operation')
    def validate_operation(cls, v):
        valid_ops = {'create', 'modify', 'delete', 'copy', 'move'}
        if v not in valid_ops:
            raise ValueError(f"Operation must be one of: {valid_ops}")
        return v


class TaskExecutionResult(BaseModel):
    """Result of a task execution."""
    
    success: bool = Field(..., description="Whether the task completed successfully")
    operation: str = Field(..., description="The operation that was performed")
    path: str = Field(..., description="The file path that was operated on")
    message: str = Field(..., description="Human-readable status message")
    backup_path: Optional[str] = Field(None, description="Path to backup file if created")
    error: Optional[str] = Field(None, description="Error message if operation failed")


class TaskExecutor:
    """Execute file operations with proper error handling and logging.
    
    This class provides a safe way to execute file operations for VIBE code
    generation, with support for backups, validation, and rollback capabilities.
    
    Example:
        >>> executor = TaskExecutor("/path/to/project")
        >>> result = executor.create_file("src/main.py", "print('Hello, World!')")
        >>> if result.success:
        ...     print(f"Created file: {result.path}")
    """

    def __init__(self, base_dir: Union[str, Path], create_backups: bool = True) -> None:
        """Initialize the task executor.
        
        Args:
            base_dir: Base directory for all file operations
            create_backups: Whether to create backups before modifying files
        """
        self.base_dir = Path(base_dir).resolve()
        self.create_backups = create_backups
        self.executed_operations: List[TaskExecutionResult] = []
        
        # Ensure base directory exists
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"TaskExecutor initialized with base directory: {self.base_dir}")

    def execute_operation(self, operation: FileOperation) -> TaskExecutionResult:
        """Execute a single file operation.
        
        Args:
            operation: The file operation to execute
            
        Returns:
            Result of the operation execution
        """
        try:
            if operation.operation == "create":
                return self._create_file(operation)
            elif operation.operation == "modify":
                return self._modify_file(operation)
            elif operation.operation == "delete":
                return self._delete_file(operation)
            elif operation.operation == "copy":
                return self._copy_file(operation)
            elif operation.operation == "move":
                return self._move_file(operation)
            else:
                return TaskExecutionResult(
                    success=False,
                    operation=operation.operation,
                    path=operation.path,
                    message=f"Unknown operation: {operation.operation}",
                    error=f"Unsupported operation type: {operation.operation}"
                )
                
        except Exception as e:
            logger.error(f"Failed to execute {operation.operation} on {operation.path}: {e}")
            return TaskExecutionResult(
                success=False,
                operation=operation.operation,
                path=operation.path,
                message=f"Operation failed: {str(e)}",
                error=str(e)
            )
        finally:
            # Store the result for potential rollback
            if hasattr(self, '_last_result'):
                self.executed_operations.append(self._last_result)

    def create_file(self, path: str, content: str, overwrite: bool = False) -> TaskExecutionResult:
        """Create a new file with the specified content.
        
        Args:
            path: File path relative to base directory
            content: File content
            overwrite: Whether to overwrite existing files
            
        Returns:
            Result of the create operation
        """
        operation = FileOperation(
            operation="create",
            path=path,
            content=content
        )
        
        # Check if file already exists
        target_path = self.base_dir / path
        if target_path.exists() and not overwrite:
            return TaskExecutionResult(
                success=False,
                operation="create",
                path=path,
                message=f"File already exists: {path}",
                error="File exists and overwrite=False"
            )
            
        return self.execute_operation(operation)

    def modify_file(
        self, 
        path: str, 
        content: str, 
        create_backup: Optional[bool] = None
    ) -> TaskExecutionResult:
        """Modify an existing file with new content.
        
        Args:
            path: File path relative to base directory
            content: New file content
            create_backup: Whether to create backup (overrides instance setting)
            
        Returns:
            Result of the modify operation
        """
        operation = FileOperation(
            operation="modify",
            path=path,
            content=content,
            backup=create_backup if create_backup is not None else self.create_backups
        )
        return self.execute_operation(operation)

    def delete_file(self, path: str, create_backup: Optional[bool] = None) -> TaskExecutionResult:
        """Delete a file.
        
        Args:
            path: File path relative to base directory
            create_backup: Whether to create backup before deletion
            
        Returns:
            Result of the delete operation
        """
        operation = FileOperation(
            operation="delete",
            path=path,
            backup=create_backup if create_backup is not None else self.create_backups
        )
        return self.execute_operation(operation)

    def copy_file(self, source: str, destination: str) -> TaskExecutionResult:
        """Copy a file from source to destination.
        
        Args:
            source: Source file path relative to base directory
            destination: Destination file path relative to base directory
            
        Returns:
            Result of the copy operation
        """
        operation = FileOperation(
            operation="copy",
            path=destination,
            source=source
        )
        return self.execute_operation(operation)

    def move_file(self, source: str, destination: str) -> TaskExecutionResult:
        """Move a file from source to destination.
        
        Args:
            source: Source file path relative to base directory
            destination: Destination file path relative to base directory
            
        Returns:
            Result of the move operation
        """
        operation = FileOperation(
            operation="move",
            path=destination,
            source=source
        )
        return self.execute_operation(operation)

    def _create_file(self, operation: FileOperation) -> TaskExecutionResult:
        """Internal method to create a file."""
        target_path = self.base_dir / operation.path
        
        # Create parent directories if they don't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write content to file
        target_path.write_text(operation.content or "", encoding='utf-8')
        
        result = TaskExecutionResult(
            success=True,
            operation="create",
            path=operation.path,
            message=f"Created file: {operation.path}"
        )
        
        self._last_result = result
        logger.info(f"Created file: {target_path}")
        return result

    def _modify_file(self, operation: FileOperation) -> TaskExecutionResult:
        """Internal method to modify a file."""
        target_path = self.base_dir / operation.path
        
        if not target_path.exists():
            return TaskExecutionResult(
                success=False,
                operation="modify",
                path=operation.path,
                message=f"File not found: {operation.path}",
                error="File does not exist"
            )
        
        backup_path = None
        if operation.backup:
            backup_path = self._create_backup(target_path)
        
        # Write new content
        target_path.write_text(operation.content or "", encoding='utf-8')
        
        result = TaskExecutionResult(
            success=True,
            operation="modify",
            path=operation.path,
            message=f"Modified file: {operation.path}",
            backup_path=str(backup_path) if backup_path else None
        )
        
        self._last_result = result
        logger.info(f"Modified file: {target_path}")
        return result

    def _delete_file(self, operation: FileOperation) -> TaskExecutionResult:
        """Internal method to delete a file."""
        target_path = self.base_dir / operation.path
        
        if not target_path.exists():
            return TaskExecutionResult(
                success=False,
                operation="delete",
                path=operation.path,
                message=f"File not found: {operation.path}",
                error="File does not exist"
            )
        
        backup_path = None
        if operation.backup:
            backup_path = self._create_backup(target_path)
        
        # Delete the file
        target_path.unlink()
        
        result = TaskExecutionResult(
            success=True,
            operation="delete",
            path=operation.path,
            message=f"Deleted file: {operation.path}",
            backup_path=str(backup_path) if backup_path else None
        )
        
        self._last_result = result
        logger.info(f"Deleted file: {target_path}")
        return result

    def _copy_file(self, operation: FileOperation) -> TaskExecutionResult:
        """Internal method to copy a file."""
        source_path = self.base_dir / operation.source
        target_path = self.base_dir / operation.path
        
        if not source_path.exists():
            return TaskExecutionResult(
                success=False,
                operation="copy",
                path=operation.path,
                message=f"Source file not found: {operation.source}",
                error="Source file does not exist"
            )
        
        # Create parent directories if they don't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Copy the file
        shutil.copy2(source_path, target_path)
        
        result = TaskExecutionResult(
            success=True,
            operation="copy",
            path=operation.path,
            message=f"Copied {operation.source} to {operation.path}"
        )
        
        self._last_result = result
        logger.info(f"Copied {source_path} to {target_path}")
        return result

    def _move_file(self, operation: FileOperation) -> TaskExecutionResult:
        """Internal method to move a file."""
        source_path = self.base_dir / operation.source
        target_path = self.base_dir / operation.path
        
        if not source_path.exists():
            return TaskExecutionResult(
                success=False,
                operation="move",
                path=operation.path,
                message=f"Source file not found: {operation.source}",
                error="Source file does not exist"
            )
        
        # Create parent directories if they don't exist
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move the file
        shutil.move(str(source_path), str(target_path))
        
        result = TaskExecutionResult(
            success=True,
            operation="move",
            path=operation.path,
            message=f"Moved {operation.source} to {operation.path}"
        )
        
        self._last_result = result
        logger.info(f"Moved {source_path} to {target_path}")
        return result

    def _create_backup(self, file_path: Path) -> Path:
        """Create a backup of the specified file."""
        backup_dir = self.base_dir / ".vibe_backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Create backup filename with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.name}.{timestamp}.backup"
        backup_path = backup_dir / backup_name
        
        # Copy the file to backup location
        shutil.copy2(file_path, backup_path)
        logger.debug(f"Created backup: {backup_path}")
        
        return backup_path

    def get_operation_history(self) -> List[TaskExecutionResult]:
        """Get the history of executed operations.
        
        Returns:
            List of execution results in chronological order
        """
        return self.executed_operations.copy()

    def clear_history(self) -> None:
        """Clear the operation history."""
        self.executed_operations.clear()
        logger.info("Cleared operation history")

    def validate_path(self, path: str) -> bool:
        """Validate that a path is safe and within the base directory.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is valid and safe
        """
        try:
            full_path = (self.base_dir / path).resolve()
            return full_path.is_relative_to(self.base_dir)
        except (ValueError, OSError):
            return False


# Backward compatibility function
def create_executor(base_dir: Union[str, Path], create_backups: bool = True) -> TaskExecutor:
    """Create a TaskExecutor instance.
    
    Args:
        base_dir: Base directory for file operations
        create_backups: Whether to create backups by default
        
    Returns:
        Configured TaskExecutor instance
    """
    return TaskExecutor(base_dir, create_backups)
