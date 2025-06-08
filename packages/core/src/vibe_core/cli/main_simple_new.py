"""Simplified main CLI entry point for VIBE Core."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path


class VibeCLI:
    """Main CLI interface for VIBE Core."""
    
    def __init__(self):
        """Initialize CLI."""
        self.logger = logging.getLogger(__name__)
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create and configure argument parser."""
        parser = argparse.ArgumentParser(
            prog="vibe",
            description="VIBE - AI-powered project generation and coding assistant",
            epilog="For more information, visit: https://github.com/your-org/vibe"
        )
        
        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Enable verbose output"
        )
        
        parser.add_argument(
            "--version",
            action="version",
            version="VIBE Core 0.1.0"
        )
        
        # Subcommands
        subparsers = parser.add_subparsers(dest="command", help="Available commands")
        
        # Generate command
        generate_parser = subparsers.add_parser("generate", help="Generate a new project")
        generate_parser.add_argument("name", help="Project name")
        generate_parser.add_argument("--dry-run", action="store_true", help="Show what would be generated without creating files")
        
        # Status command
        status_parser = subparsers.add_parser("status", help="Show VIBE status")
        
        return parser
    
    def run(self, args=None):
        """Run the CLI with given arguments."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)
        
        # Configure logging
        level = logging.DEBUG if parsed_args.verbose else logging.INFO
        logging.basicConfig(level=level, format='%(levelname)s: %(message)s')
        
        # Handle commands
        if parsed_args.command == "generate":
            return self.handle_generate(parsed_args)
        elif parsed_args.command == "status":
            return self.handle_status(parsed_args)
        else:
            parser.print_help()
            return 0
    
    def handle_generate(self, args):
        """Handle the generate command."""
        print(f"Generating project: {args.name}")
        if args.dry_run:
            print("(Dry run mode - no files will be created)")
        
        try:
            # Import here to avoid circular imports during CLI initialization
            from ..workflows.generate import GenerationWorkflow, WorkflowOptions
            from ..models import ProjectConfig
            
            # Create a basic project config from the command line arguments
            config_data = {
                "project_name": args.name,
                "project_description": f"Generated project: {args.name}",
                "architecture_style": "monolith",  # Default value
                "cloud_provider": "aws"  # Default value
            }
            
            # Create workflow options
            workflow_options = WorkflowOptions(
                config_json=json.dumps(config_data),
                dry_run=args.dry_run,
                verbose=args.verbose if hasattr(args, 'verbose') else False
            )
            
            # Initialize and run workflow
            workflow = GenerationWorkflow()
            result = workflow.run(workflow_options)
            
            if result.success:
                print("✓ Project generation completed successfully!")
                if not args.dry_run and result.generation_result:
                    if result.generation_result.project_path:
                        print(f"Project created at: {result.generation_result.project_path}")
                    if result.generation_result.archive_path:
                        print(f"Archive created at: {result.generation_result.archive_path}")
                return 0
            else:
                print("✗ Project generation failed:")
                for error in result.errors:
                    print(f"  - {error}")
                return 1
                
        except Exception as e:
            print(f"Error during generation: {e}")
            if args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def handle_status(self, args):
        """Handle the status command."""
        print("VIBE Core Status:")
        print("✓ CLI is working")
        print("✓ Basic functionality available")
        print("⚠ Full generation workflow in development")
        return 0


def main():
    """Main entry point for CLI."""
    cli = VibeCLI()
    try:
        return cli.run()
    except KeyboardInterrupt:
        print("\nAborted by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
