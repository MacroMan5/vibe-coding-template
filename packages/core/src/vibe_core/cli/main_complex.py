"""Main CLI entry point for VIBE Core."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..workflows.generate import GenerationWorkflow, WorkflowOptions
from ..validators.integrity import validate_project
from ..parsers.claude import parse_claude_response
from ..generators.architect import CodeArchitect
from ..utils.env import load_api_keys

logger = logging.getLogger(__name__)


class VibeCLI:
    """Main CLI interface for VIBE Core."""
    
    def __init__(self):
        """Initialize CLI."""
        self.workflow = GenerationWorkflow()
        self.setup_logging()
    
    def setup_logging(self, level: int = logging.INFO) -> None:
        """Setup logging configuration.
        
        Args:
            level: Logging level
        """
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser with all subcommands.
        
        Returns:
            Configured ArgumentParser
        """
        parser = argparse.ArgumentParser(
            description="VIBE Coding Template CLI",
            prog="vibe"
        )
        
        parser.add_argument(
            "--verbose", "-v",
            action="store_true",
            help="Enable verbose logging"
        )
        
        # Create subparsers
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Generate command
        self._add_generate_parser(subparsers)
        
        # Parse command  
        self._add_parse_parser(subparsers)
        
        # Validate command
        self._add_validate_parser(subparsers)
        
        # Merge command
        self._add_merge_parser(subparsers)
        
        # Verify command
        self._add_verify_parser(subparsers)
        
        return parser
    
    def _add_generate_parser(self, subparsers) -> None:
        """Add generate subcommand parser."""
        gen_parser = subparsers.add_parser(
            "generate",
            help="Generate project architecture using Claude AI"
        )
        
        # Config options (mutually exclusive)
        config_group = gen_parser.add_mutually_exclusive_group(required=True)
        config_group.add_argument(
            "--config", "-c",
            type=Path,
            help="Path to JSON configuration file"
        )
        config_group.add_argument(
            "--json", "-j",
            type=str,
            help="Configuration as JSON string"
        )
        
        # Generation options
        gen_parser.add_argument(
            "--model", "-m",
            default="claude-3-5-sonnet-20241022",
            help="Claude model to use (default: claude-3-5-sonnet-20241022)"
        )
        gen_parser.add_argument(
            "--output", "-o",
            type=Path,
            help="Output directory (default: ./build)"
        )
        gen_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview actions without generating files"
        )
        gen_parser.add_argument(
            "--json-output",
            action="store_true", 
            help="Return JSON output for dry runs"
        )
        
        gen_parser.set_defaults(func=self.cmd_generate)
    
    def _add_parse_parser(self, subparsers) -> None:
        """Add parse subcommand parser."""
        parse_parser = subparsers.add_parser(
            "parse",
            help="Parse Claude response file into project files"
        )
        
        parse_parser.add_argument(
            "source",
            type=Path,
            help="Path to Claude response text file"
        )
        parse_parser.add_argument(
            "output_dir",
            type=Path,
            help="Directory to write parsed files"
        )
        parse_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview actions without writing files"
        )
        
        parse_parser.set_defaults(func=self.cmd_parse)
    
    def _add_validate_parser(self, subparsers) -> None:
        """Add validate subcommand parser."""
        validate_parser = subparsers.add_parser(
            "validate",
            help="Validate project integrity and structure"
        )
        
        validate_parser.add_argument(
            "project_dir",
            type=Path,
            help="Path to project directory to validate"
        )
        validate_parser.add_argument(
            "--report", "-r",
            type=Path,
            help="Path to write validation report (markdown)"
        )
        
        validate_parser.set_defaults(func=self.cmd_validate)
    
    def _add_merge_parser(self, subparsers) -> None:
        """Add merge subcommand parser."""
        merge_parser = subparsers.add_parser(
            "merge",
            help="Merge prompt templates with configuration"
        )
        
        # Config options (mutually exclusive)
        config_group = merge_parser.add_mutually_exclusive_group(required=True)
        config_group.add_argument(
            "--config", "-c",
            type=Path,
            help="Path to JSON configuration file"
        )
        config_group.add_argument(
            "--json", "-j",
            type=str,
            help="Configuration as JSON string"
        )
        
        merge_parser.add_argument(
            "--templates", "-t",
            type=Path,
            help="Path to templates directory"
        )
        merge_parser.add_argument(
            "--output", "-o",
            type=Path,
            help="Output file for merged prompt"
        )
        
        merge_parser.set_defaults(func=self.cmd_merge)
    
    def _add_verify_parser(self, subparsers) -> None:
        """Add verify subcommand parser."""
        verify_parser = subparsers.add_parser(
            "verify",
            help="Verify generated files against Claude response"
        )
        
        verify_parser.add_argument(
            "response_file",
            type=Path,
            help="Path to Claude response file"
        )
        verify_parser.add_argument(
            "project_dir",
            type=Path,
            help="Path to generated project directory"
        )
        
        verify_parser.set_defaults(func=self.cmd_verify)
    
    def cmd_generate(self, args) -> None:
        """Handle generate command.
        
        Args:
            args: Parsed command arguments
        """
        try:
            # Setup options
            options = WorkflowOptions(
                config_file=args.config,
                config_json=args.json,
                dry_run=args.dry_run,
                json_output=args.json_output,
                verbose=args.verbose,
                model=args.model,
                output_dir=args.output
            )
            
            # Run workflow
            result = self.workflow.run(options)
            
            if args.dry_run and args.json_output and result.output_data:
                print(json.dumps(result.output_data, indent=2))
            elif result.success:
                if result.generation_result and result.generation_result.archive_path:
                    print(result.generation_result.archive_path)
                else:
                    print("Generation completed successfully")
            else:
                print("Generation failed:")
                for error in result.errors:
                    print(f"  - {error}")
                sys.exit(1)
                
        except Exception as e:
            logger.error(f"Generate command failed: {e}")
            print(f"Error: {e}")
            sys.exit(1)
    
    def cmd_parse(self, args) -> None:
        """Handle parse command.
        
        Args:
            args: Parsed command arguments
        """
        try:
            if not args.source.exists():
                print(f"Error: Source file not found: {args.source}")
                sys.exit(1)
            
            # Parse response
            content = args.source.read_text(encoding="utf-8")
            files = parse_claude_response(content)
            
            if args.dry_run:
                print(f"Would parse {len(files)} files:")
                for file in files:
                    print(f"  {file.path}")
            else:
                # Write files
                args.output_dir.mkdir(parents=True, exist_ok=True)
                for file in files:
                    target = args.output_dir / file.path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_text(file.content, encoding="utf-8")
                    
                print(f"Parsed {len(files)} files to {args.output_dir}")
                
        except Exception as e:
            logger.error(f"Parse command failed: {e}")
            print(f"Error: {e}")
            sys.exit(1)
    
    def cmd_validate(self, args) -> None:
        """Handle validate command.
        
        Args:
            args: Parsed command arguments
        """
        try:
            if not args.project_dir.exists():
                print(f"Error: Project directory not found: {args.project_dir}")
                sys.exit(1)
            
            # Run validation
            report = validate_project(args.project_dir, args.report)
            
            if args.report:
                print(f"Validation report written to: {args.report}")
            else:
                # Print summary
                print(f"Project: {report.project_path}")
                print(f"Files: {report.total_files}")
                print(f"Issues: {len(report.issues)}")
                
                if report.success:
                    print("✅ Validation passed")
                else:
                    print("❌ Validation failed")
                    for issue in report.issues[:5]:  # Show first 5 issues
                        print(f"  - {issue['message']}")
                    if len(report.issues) > 5:
                        print(f"  ... and {len(report.issues) - 5} more issues")
                
        except Exception as e:
            logger.error(f"Validate command failed: {e}")
            print(f"Error: {e}")
            sys.exit(1)
    
    def cmd_merge(self, args) -> None:
        """Handle merge command.
        
        Args:
            args: Parsed command arguments
        """
        try:
            # Load configuration
            if args.config:
                config_data = json.loads(args.config.read_text())
            else:
                config_data = json.loads(args.json)
            
            # Setup merge configuration
            merge_config = config_data.copy()
            if args.templates:
                merge_config["templates_dir"] = str(args.templates)
            if args.output:
                merge_config["output_file"] = str(args.output)
            
            # Perform merge
            from ..generators.merger import PromptMerger
            merger = PromptMerger()
            result = merger.merge_from_config(merge_config)
            
            output_file = result.get("output_file", "merged_prompt.md")
            print(f"Merged prompt written to: {output_file}")
            
        except Exception as e:
            logger.error(f"Merge command failed: {e}")
            print(f"Error: {e}")
            sys.exit(1)
    
    def cmd_verify(self, args) -> None:
        """Handle verify command.
        
        Args:
            args: Parsed command arguments
        """
        try:
            if not args.response_file.exists():
                print(f"Error: Response file not found: {args.response_file}")
                sys.exit(1)
                
            if not args.project_dir.exists():
                print(f"Error: Project directory not found: {args.project_dir}")
                sys.exit(1)
            
            # Parse response and verify files
            content = args.response_file.read_text(encoding="utf-8")
            files = parse_claude_response(content)
            
            missing_files = []
            for file in files:
                file_path = args.project_dir / file.path
                if not file_path.exists():
                    missing_files.append(file.path)
            
            if missing_files:
                print("❌ Verification failed")
                print(f"Missing {len(missing_files)} files:")
                for path in missing_files[:10]:  # Show first 10
                    print(f"  - {path}")
                if len(missing_files) > 10:
                    print(f"  ... and {len(missing_files) - 10} more")
                sys.exit(1)
            else:
                print("✅ Verification passed")
                print(f"All {len(files)} files found")
                
        except Exception as e:
            logger.error(f"Verify command failed: {e}")
            print(f"Error: {e}")
            sys.exit(1)
    
    def run(self, argv: Optional[List[str]] = None) -> None:
        """Run CLI with given arguments.
        
        Args:
            argv: Command line arguments (uses sys.argv if None)
        """
        parser = self.create_parser()
        args = parser.parse_args(argv)
        
        # Setup verbose logging if requested
        if args.verbose:
            self.setup_logging(logging.DEBUG)
            logger.debug("Verbose logging enabled")
        
        # Check for API keys early
        try:
            load_api_keys()
        except ValueError as e:
            print(f"Error: {e}")
            print("Please ensure your API keys are set in environment variables or .env file")
            sys.exit(1)
        
        # Run command
        if hasattr(args, 'func'):
            args.func(args)
        else:
            parser.print_help()


def main(argv: Optional[List[str]] = None) -> None:
    """Main CLI entry point.
    
    Args:
        argv: Command line arguments
    """
    cli = VibeCLI()
    cli.run(argv)


if __name__ == "__main__":
    main()
