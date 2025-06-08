"""Prompt merging functionality for VIBE Core."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml

logger = logging.getLogger(__name__)

# Pattern for variable replacement in templates
VARIABLE_PATTERN = re.compile(r"{{\s*([\w\.]+)\s*}}")


class PromptMerger:
    """Handles merging of prompt templates with configuration data."""

    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        """Initialize the prompt merger.

        Args:
            base_dir: Base directory containing templates and prompts
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.templates_dir = self.base_dir / "templates"
        self.agent_prompts_dir = self.base_dir / "agent_prompts"

    def flatten_config(self, data: Any, parent: str = "") -> Dict[str, Any]:
        """Return a flattened representation of data using dot notation.

        Supports nested dictionaries and lists. List indices become part of the
        key path, e.g. ``services.0.name``.

        Args:
            data: Configuration data to flatten
            parent: Parent key path

        Returns:
            Flattened configuration dictionary
        """
        items: Dict[str, Any] = {}

        if isinstance(data, Mapping):
            for key, value in data.items():
                path = f"{parent}.{key}" if parent else key
                if isinstance(value, (Mapping, list)):
                    items.update(self.flatten_config(value, path))
                else:
                    items[path] = value
                    if not parent:  # maintain top level keys for compatibility
                        items.setdefault(key, value)
        elif isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
            for idx, value in enumerate(data):
                path = f"{parent}.{idx}" if parent else str(idx)
                if isinstance(value, (Mapping, list)):
                    items.update(self.flatten_config(value, path))
                else:
                    items[path] = value
        return items

    def parse_prompt_meta(self, filepath: Path) -> Tuple[Dict[str, Any], str]:
        """Return metadata dict and content without front matter.

        Args:
            filepath: Path to prompt file

        Returns:
            Tuple of (metadata, content)
        """
        try:
            text = filepath.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read prompt file {filepath}: {e}")
            return {}, ""

        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                _, meta_text, content = parts
                try:
                    meta = yaml.safe_load(meta_text) or {}
                    return meta, content.lstrip()
                except yaml.YAMLError as e:
                    logger.warning(
                        f"Failed to parse YAML frontmatter in {filepath}: {e}"
                    )
                    return {}, text
        return {}, text

    def replace_vars(self, text: str, config: Dict[str, Any]) -> str:
        """Replace {{var}} placeholders in text using config.

        Args:
            text: Template text with variables
            config: Configuration data

        Returns:
            Text with variables replaced
        """
        flat = self.flatten_config(config)

        def repl(match):
            key = match.group(1)
            value = flat.get(key, "")
            return str(value) if value is not None else ""

        return VARIABLE_PATTERN.sub(repl, text)

    def _cfg_value(self, cfg: Dict[str, Any], *keys: str, default: str = "") -> str:
        """Return the first present key from cfg.

        Args:
            cfg: Configuration dictionary
            keys: Keys to try in order
            default: Default value if no keys found

        Returns:
            First found value or default
        """
        for k in keys:
            if k in cfg:
                return str(cfg[k])
        return default

    def should_include_prompt(
        self, meta: Dict[str, Any], config: Dict[str, Any]
    ) -> bool:
        """Determine if prompt should be included based on metadata and config.

        Args:
            meta: Prompt metadata
            config: Flattened configuration

        Returns:
            True if prompt should be included
        """
        # Check stack requirements
        stack = self._cfg_value(config, "backend.stack", "backend_stack").lower()
        if meta.get("stack"):
            allowed = [s.lower() for s in meta["stack"]]
            if stack and stack not in allowed:
                return False

        # Check auth requirements
        auth = self._cfg_value(config, "auth.type", "auth_type", default="none").lower()
        if meta.get("auth_required") and auth == "none":
            return False

        # Check database requirements
        db = self._cfg_value(
            config, "database.type", "database_type", default="none"
        ).lower()
        if meta.get("database_required") and db == "none":
            return False

        return True

    def select_prompts(self, prompt_dir: Path, config: Dict[str, Any]) -> List[Path]:
        """Select prompt files to include based on metadata.

        Args:
            prompt_dir: Directory containing prompt files
            config: Configuration data

        Returns:
            List of selected prompt file paths
        """
        if not prompt_dir.exists():
            logger.warning(f"Prompt directory does not exist: {prompt_dir}")
            return []

        selected = []
        flat_config = self.flatten_config(config)

        for path in sorted(prompt_dir.glob("*.md")):
            try:
                meta, _ = self.parse_prompt_meta(path)
                if self.should_include_prompt(meta, flat_config):
                    selected.append(path)
                    logger.debug(f"Selected prompt: {path.name}")
                else:
                    logger.debug(f"Skipped prompt: {path.name}")
            except Exception as e:
                logger.warning(f"Error processing prompt {path}: {e}")

        return selected

    def merge_prompts(self, prompt_paths: List[Path], config: Dict[str, Any]) -> str:
        """Merge prompt files with variable replacement.

        Args:
            prompt_paths: List of prompt file paths
            config: Configuration data

        Returns:
            Merged prompt content
        """
        sections = []
        for path in prompt_paths:
            try:
                _, content = self.parse_prompt_meta(path)
                processed = self.replace_vars(content, config)
                sections.append(processed.strip())
            except Exception as e:
                logger.warning(f"Error processing prompt {path}: {e}")

        return "\n\n".join(sections)

    def generate_plan(self, config: Dict[str, Any]) -> str:
        """Create a simple generation plan section.

        Args:
            config: Configuration data

        Returns:
            Generated plan text
        """
        get = lambda *k, d=None: self._cfg_value(config, *k, default=d or "")

        steps = [
            "Create the project structure",
            f"Add the ORM and schema for {get('database.type', 'database_type', d='the database')}",
            "Generate REST endpoints",
            f"Integrate authentication using {get('auth.type', 'auth_type', d='the auth system')}",
            "Add CI/CD, tests and monitoring",
        ]

        return "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))

    def merge_from_config(self, config: Dict[str, Any]) -> Path:
        """Merge templates using config dict and return the prompt path.

        Args:
            config: Configuration dictionary

        Returns:
            Path to merged prompt file
        """
        logger.info("Starting prompt merge process")

        # Get flattened config for template processing
        cfg_flat = self.flatten_config(config)

        # Load master template
        template_path = self.templates_dir / "master_init_template.md"
        if not template_path.exists():
            # Create a basic template if none exists
            template_content = self._create_basic_template()
            logger.warning(
                f"Master template not found at {template_path}, using basic template"
            )
        else:
            template_content = template_path.read_text(encoding="utf-8")

        # Replace variables in master template
        merged = self.replace_vars(template_content, cfg_flat)

        # Add extra prompts from agent_prompts directory
        extra_prompts = self.select_prompts(self.agent_prompts_dir, cfg_flat)
        if extra_prompts:
            logger.info(f"Including {len(extra_prompts)} additional prompts")
            merged_extra = self.merge_prompts(extra_prompts, cfg_flat)
            merged = f"{merged}\n\n{merged_extra}".strip()

        # Add generation plan
        plan = self.generate_plan(cfg_flat)
        merged = f"{merged}\n\n## Generation Plan\n\n{plan}".strip()

        # Write output
        out_dir = self.base_dir / "build"
        out_dir.mkdir(exist_ok=True)
        out_file = out_dir / "merged_prompt.md"
        out_file.write_text(merged, encoding="utf-8")

        logger.info(f"Combined prompt written to {out_file}")
        return out_file

    def _create_basic_template(self) -> str:
        """Create a basic template when master template is missing.

        Returns:
            Basic template content
        """
        return """# Project: {{project_name}}

{{#if description}}
## Description
{{description}}
{{/if}}

## Technology Stack
- Backend: {{backend.stack}}
- Frontend: {{frontend.stack}}
- Database: {{database.type}}

## Requirements
{{#if requirements}}
{{requirements}}
{{/if}}

This project will be structured following modern development practices with proper separation of concerns.
"""


def create_merger(base_dir: Optional[Path] = None) -> PromptMerger:
    """Create a PromptMerger instance.

    Args:
        base_dir: Base directory for templates and prompts

    Returns:
        PromptMerger instance
    """
    return PromptMerger(base_dir=base_dir)
