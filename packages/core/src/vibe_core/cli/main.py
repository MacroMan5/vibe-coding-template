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
        
        # Parse command
        parse_parser = subparsers.add_parser("parse", help="Parse a Claude response file")
        parse_parser.add_argument("source", type=Path, help="Path to text response from Claude")
        parse_parser.add_argument("out_dir", type=Path, help="Directory to write files")
        parse_parser.add_argument("--dry-run", action="store_true", help="Preview actions without writing")
        
        # Verify command
        verify_parser = subparsers.add_parser("verify", help="Verify generated files against response")
        verify_parser.add_argument("response", type=Path, help="Path to Claude response file")
        verify_parser.add_argument("project_dir", type=Path, help="Path to project directory")
        
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
        elif parsed_args.command == "parse":
            return self.handle_parse(parsed_args)
        elif parsed_args.command == "verify":
            return self.handle_verify(parsed_args)
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
    
    def handle_parse(self, args):
        """Handle the parse command."""
        try:
            from ..parsers import ClaudeResponseParser
            
            parser = ClaudeResponseParser()
            files = parser.parse_response_file(args.source, args.out_dir, args.dry_run)
            
            if args.dry_run:
                print(f"✓ Found {len(files)} files in response (dry run)")
            else:
                print(f"✓ Successfully parsed {len(files)} files to {args.out_dir}")
            
            return 0
        except Exception as e:
            print(f"Error parsing response: {e}")
            if hasattr(args, 'verbose') and args.verbose:
                import traceback
                traceback.print_exc()
            return 1
    
    def handle_verify(self, args):
        """Handle the verify command."""
        try:
            from ..parsers import parse_claude_response
            
            # Read the Claude response
            response_text = args.response.read_text()
            parsed_files = parse_claude_response(response_text)
            
            # Check if files exist in project directory
            missing_files = []
            content_mismatches = []
            
            for file_obj in parsed_files:
                file_path = args.project_dir / file_obj.path
                if not file_path.exists():
                    missing_files.append(file_obj.path)
                else:
                    actual_content = file_path.read_text().strip()
                    expected_content = file_obj.content.strip()
                    if actual_content != expected_content:
                        content_mismatches.append(file_obj.path)
            
            # Report results
            if not missing_files and not content_mismatches:
                print("✓ Verification succeeded - all files match")
                return 0
            else:
                print("✗ Verification failed:")
                if missing_files:
                    print(f"  Missing files ({len(missing_files)}):")
                    for path in missing_files:
                        print(f"    - {path}")
                if content_mismatches:
                    print(f"  Content mismatches ({len(content_mismatches)}):")
                    for path in content_mismatches:
                        print(f"    - {path}")
                return 1
                
        except Exception as e:
            print(f"Error during verification: {e}")
            if hasattr(args, 'verbose') and args.verbose:
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
