"""Memory snapshot utilities for VIBE code generation debugging.

This module provides utilities for capturing and analyzing memory snapshots
during the code generation process, helping with debugging and optimization.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .memory import JsonVectorMemory, MemoryEntry

logger = logging.getLogger(__name__)


class MemorySnapshot(BaseModel):
    """Represents a snapshot of memory state at a specific point in time."""
    
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stage: str = Field(..., description="The generation stage when snapshot was taken")
    entry_count: int = Field(..., description="Number of memory entries")
    entries: List[Dict[str, Any]] = Field(..., description="Memory entries data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    

class SnapshotManager:
    """Manages memory snapshots for debugging and analysis.
    
    This class provides functionality to capture, store, and analyze memory
    snapshots during the VIBE code generation process.
    
    Example:
        >>> snapshot_mgr = SnapshotManager("./snapshots")
        >>> snapshot_mgr.capture_snapshot(memory, "pre_generation")
        >>> snapshot_mgr.capture_snapshot(memory, "post_generation")
        >>> analysis = snapshot_mgr.analyze_snapshots()
    """

    def __init__(self, snapshot_dir: Union[str, Path]) -> None:
        """Initialize the snapshot manager.
        
        Args:
            snapshot_dir: Directory to store snapshot files
        """
        self.snapshot_dir = Path(snapshot_dir)
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots: List[MemorySnapshot] = []
        logger.info(f"SnapshotManager initialized with directory: {self.snapshot_dir}")

    def capture_snapshot(
        self, 
        memory: JsonVectorMemory, 
        stage: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Capture a snapshot of the current memory state.
        
        Args:
            memory: The memory instance to snapshot
            stage: Description of the current generation stage
            metadata: Additional metadata to include
            
        Returns:
            Path to the created snapshot file
        """
        try:
            # Create snapshot data
            entries_data = []
            for entry in memory.entries:
                entry_dict = {
                    "text": entry.text,
                    "author": entry.author,
                    "context": entry.context,
                    "timestamp": entry.timestamp,
                    "metadata": entry.metadata,
                    "embedding_dims": len(entry.embedding) if entry.embedding else 0
                }
                entries_data.append(entry_dict)
            
            snapshot = MemorySnapshot(
                stage=stage,
                entry_count=len(memory.entries),
                entries=entries_data,
                metadata=metadata or {}
            )
            
            # Save to file
            snapshot_file = self._save_snapshot(snapshot)
            self.snapshots.append(snapshot)
            
            logger.info(f"Captured memory snapshot for stage '{stage}' with {snapshot.entry_count} entries")
            return snapshot_file
            
        except Exception as e:
            logger.error(f"Failed to capture memory snapshot for stage '{stage}': {e}")
            raise

    def capture_legacy_snapshot(
        self, 
        memory: Any, 
        stage: str, 
        build_dir: Optional[Path] = None
    ) -> Path:
        """Capture snapshot from legacy memory format (backward compatibility).
        
        Args:
            memory: Legacy memory object with .data attribute
            stage: Description of the generation stage
            build_dir: Build directory (uses snapshot_dir if None)
            
        Returns:
            Path to the created snapshot file
        """
        snapshot_dir = Path(build_dir) / "memory_snapshots" if build_dir else self.snapshot_dir
        snapshot_dir.mkdir(parents=True, exist_ok=True)
        
        slug = stage.replace(" ", "_").replace("/", "_")
        file_path = snapshot_dir / f"step_{slug}.json"
        
        snapshot_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stage": stage,
            "memory_chunks": getattr(memory, "data", []),
            "entry_count": len(getattr(memory, "data", [])),
            "format": "legacy"
        }
        
        file_path.write_text(json.dumps(snapshot_data, indent=2), encoding='utf-8')
        logger.info(f"Captured legacy memory snapshot: {file_path}")
        
        return file_path

    def _save_snapshot(self, snapshot: MemorySnapshot) -> Path:
        """Save a snapshot to disk.
        
        Args:
            snapshot: The snapshot to save
            
        Returns:
            Path to the saved snapshot file
        """
        # Create filename from timestamp and stage
        timestamp = datetime.fromisoformat(snapshot.timestamp.replace('Z', '+00:00'))
        timestamp_str = timestamp.strftime("%Y%m%d_%H%M%S")
        stage_slug = snapshot.stage.replace(" ", "_").replace("/", "_")
        filename = f"{timestamp_str}_{stage_slug}.json"
        
        file_path = self.snapshot_dir / filename
        
        # Convert to dictionary for JSON serialization
        snapshot_dict = snapshot.dict()
        
        file_path.write_text(json.dumps(snapshot_dict, indent=2), encoding='utf-8')
        return file_path

    def load_snapshots(self) -> List[MemorySnapshot]:
        """Load all snapshots from the snapshot directory.
        
        Returns:
            List of loaded snapshots sorted by timestamp
        """
        snapshots = []
        
        try:
            for snapshot_file in self.snapshot_dir.glob("*.json"):
                try:
                    data = json.loads(snapshot_file.read_text(encoding='utf-8'))
                    
                    # Handle legacy format
                    if data.get("format") == "legacy":
                        continue  # Skip legacy snapshots for now
                        
                    snapshot = MemorySnapshot(**data)
                    snapshots.append(snapshot)
                    
                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to load snapshot {snapshot_file}: {e}")
                    continue
            
            # Sort by timestamp
            snapshots.sort(key=lambda s: s.timestamp)
            self.snapshots = snapshots
            
            logger.info(f"Loaded {len(snapshots)} snapshots from {self.snapshot_dir}")
            return snapshots
            
        except Exception as e:
            logger.error(f"Failed to load snapshots: {e}")
            return []

    def analyze_snapshots(self) -> Dict[str, Any]:
        """Analyze captured snapshots to identify patterns and changes.
        
        Returns:
            Analysis results including growth patterns, stage comparisons, etc.
        """
        if not self.snapshots:
            self.load_snapshots()
            
        if not self.snapshots:
            return {"error": "No snapshots available for analysis"}
        
        analysis = {
            "total_snapshots": len(self.snapshots),
            "time_range": {
                "start": self.snapshots[0].timestamp,
                "end": self.snapshots[-1].timestamp
            },
            "stages": [],
            "memory_growth": [],
            "author_distribution": {},
            "context_distribution": {}
        }
        
        # Analyze each snapshot
        for i, snapshot in enumerate(self.snapshots):
            stage_info = {
                "stage": snapshot.stage,
                "timestamp": snapshot.timestamp,
                "entry_count": snapshot.entry_count,
                "growth": 0 if i == 0 else snapshot.entry_count - self.snapshots[i-1].entry_count
            }
            analysis["stages"].append(stage_info)
            analysis["memory_growth"].append(snapshot.entry_count)
            
            # Analyze author and context distribution
            for entry in snapshot.entries:
                author = entry.get("author", "unknown")
                context = entry.get("context", "unknown")
                
                analysis["author_distribution"][author] = analysis["author_distribution"].get(author, 0) + 1
                analysis["context_distribution"][context] = analysis["context_distribution"].get(context, 0) + 1
        
        # Calculate growth rate
        if len(analysis["memory_growth"]) > 1:
            total_growth = analysis["memory_growth"][-1] - analysis["memory_growth"][0]
            analysis["average_growth_rate"] = total_growth / (len(analysis["memory_growth"]) - 1)
        else:
            analysis["average_growth_rate"] = 0
            
        return analysis

    def export_analysis(self, output_file: Optional[Path] = None) -> Path:
        """Export snapshot analysis to a JSON file.
        
        Args:
            output_file: Output file path (defaults to analysis.json in snapshot dir)
            
        Returns:
            Path to the exported analysis file
        """
        if output_file is None:
            output_file = self.snapshot_dir / "analysis.json"
        
        analysis = self.analyze_snapshots()
        
        output_file.write_text(json.dumps(analysis, indent=2), encoding='utf-8')
        logger.info(f"Exported snapshot analysis to: {output_file}")
        
        return output_file

    def clear_snapshots(self) -> None:
        """Clear all snapshots from memory and optionally from disk.
        
        Args:
            delete_files: Whether to delete snapshot files from disk
        """
        self.snapshots.clear()
        logger.info("Cleared snapshots from memory")

    def get_snapshot_by_stage(self, stage: str) -> Optional[MemorySnapshot]:
        """Get the most recent snapshot for a specific stage.
        
        Args:
            stage: The stage name to search for
            
        Returns:
            The most recent snapshot for the stage, or None if not found
        """
        matching_snapshots = [s for s in self.snapshots if s.stage == stage]
        return matching_snapshots[-1] if matching_snapshots else None

    def compare_stages(self, stage1: str, stage2: str) -> Dict[str, Any]:
        """Compare memory state between two stages.
        
        Args:
            stage1: First stage to compare
            stage2: Second stage to compare
            
        Returns:
            Comparison analysis
        """
        snapshot1 = self.get_snapshot_by_stage(stage1)
        snapshot2 = self.get_snapshot_by_stage(stage2)
        
        if not snapshot1 or not snapshot2:
            return {"error": f"Could not find snapshots for stages '{stage1}' and/or '{stage2}'"}
        
        comparison = {
            "stage1": {
                "name": stage1,
                "timestamp": snapshot1.timestamp,
                "entry_count": snapshot1.entry_count
            },
            "stage2": {
                "name": stage2,
                "timestamp": snapshot2.timestamp,
                "entry_count": snapshot2.entry_count
            },
            "difference": {
                "entry_count_change": snapshot2.entry_count - snapshot1.entry_count,
                "time_elapsed": snapshot2.timestamp  # Could calculate actual time difference
            }
        }
        
        return comparison


# Backward compatibility function
def dump_memory_snapshot(memory: Any, stage: str, build_dir: Path) -> Path:
    """Write a snapshot of memory to build_dir/memory_snapshots (legacy function).
    
    Args:
        memory: Memory object to snapshot
        stage: Current generation stage
        build_dir: Build directory for the project
        
    Returns:
        Path to the created snapshot file
    """
    snapshot_manager = SnapshotManager(build_dir / "memory_snapshots")
    return snapshot_manager.capture_legacy_snapshot(memory, stage, build_dir)


# Factory function
def create_snapshot_manager(snapshot_dir: Union[str, Path]) -> SnapshotManager:
    """Create a SnapshotManager instance.
    
    Args:
        snapshot_dir: Directory for storing snapshots
        
    Returns:
        Configured SnapshotManager instance
    """
    return SnapshotManager(snapshot_dir)
