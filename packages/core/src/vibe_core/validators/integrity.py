"""Project integrity validation for VIBE Core."""

from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass
from enum import Enum

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Types of integrity issues."""
    EMPTY_DIRECTORY = "empty_directory"
    DUPLICATE_FILE = "duplicate_file"
    MISSING_IMPORT = "missing_import"
    BROKEN_REFERENCE = "broken_reference"
    SYNTAX_ERROR = "syntax_error"


@dataclass
class IntegrityIssue:
    """Represents an integrity issue found during validation."""
    type: IssueType
    message: str
    file_path: Path | None = None
    line_number: int | None = None
    severity: str = "warning"  # error, warning, info


class ValidationReport(BaseModel):
    """Report of project integrity validation."""
    project_path: str
    total_files: int
    total_directories: int
    issues: List[Dict[str, str]]  # Serializable version of issues
    success: bool
    
    @classmethod
    def from_issues(cls, project_path: Path, issues: List[IntegrityIssue]) -> "ValidationReport":
        """Create report from list of issues."""
        # Count files and directories
        total_files = sum(1 for _ in project_path.rglob("*") if _.is_file())
        total_dirs = sum(1 for _ in project_path.rglob("*") if _.is_dir())
        
        # Convert issues to serializable format
        issue_dicts = []
        for issue in issues:
            issue_dict = {
                "type": issue.type.value,
                "message": issue.message,
                "severity": issue.severity,
            }
            if issue.file_path:
                issue_dict["file_path"] = str(issue.file_path)
            if issue.line_number:
                issue_dict["line_number"] = issue.line_number
            issue_dicts.append(issue_dict)
        
        return cls(
            project_path=str(project_path),
            total_files=total_files,
            total_directories=total_dirs,
            issues=issue_dicts,
            success=len([i for i in issues if i.severity == "error"]) == 0
        )


class ProjectIntegrityValidator:
    """Validates project structure and integrity."""
    
    def __init__(self, project_path: Path):
        """Initialize validator.
        
        Args:
            project_path: Path to project directory to validate
        """
        self.project_path = project_path.resolve()
        self.issues: List[IntegrityIssue] = []
        
    def validate(self) -> ValidationReport:
        """Run full validation and return report.
        
        Returns:
            ValidationReport with all found issues
        """
        if not self.project_path.exists():
            self.issues.append(IntegrityIssue(
                type=IssueType.BROKEN_REFERENCE,
                message=f"Project path does not exist: {self.project_path}",
                severity="error"
            ))
            return ValidationReport.from_issues(self.project_path, self.issues)
        
        logger.info(f"Validating project integrity: {self.project_path}")
        
        # Run all validation checks
        self._check_empty_directories()
        self._check_duplicate_files()
        self._check_imports()
        self._check_syntax()
        
        logger.info(f"Validation complete. Found {len(self.issues)} issues")
        return ValidationReport.from_issues(self.project_path, self.issues)
    
    def _check_empty_directories(self) -> None:
        """Check for empty directories."""
        for dir_path in self.project_path.rglob("*"):
            if dir_path.is_dir() and not any(dir_path.iterdir()):
                # Skip common empty directories that are intentional
                if dir_path.name in {".git", "__pycache__", "node_modules", ".pytest_cache"}:
                    continue
                    
                self.issues.append(IntegrityIssue(
                    type=IssueType.EMPTY_DIRECTORY,
                    message=f"Empty directory: {dir_path.relative_to(self.project_path)}",
                    file_path=dir_path,
                    severity="warning"
                ))
    
    def _check_duplicate_files(self) -> None:
        """Check for duplicate files based on name and content."""
        seen_files: Dict[Tuple[str, str], Path] = {}
        
        for file_path in self.project_path.rglob("*"):
            if not file_path.is_file():
                continue
                
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as e:
                logger.debug(f"Could not read file {file_path}: {e}")
                content = ""
            
            # Create key from filename and content hash
            key = (file_path.name, hash(content))
            
            if key in seen_files:
                other_path = seen_files[key]
                self.issues.append(IntegrityIssue(
                    type=IssueType.DUPLICATE_FILE,
                    message=f"Duplicate file: {file_path.relative_to(self.project_path)} "
                           f"same as {other_path.relative_to(self.project_path)}",
                    file_path=file_path,
                    severity="warning"
                ))
            else:
                seen_files[key] = file_path
    
    def _check_imports(self) -> None:
        """Check for broken imports in Python and JavaScript files."""
        # Check Python files
        for py_file in self.project_path.rglob("*.py"):
            self._check_python_imports(py_file)
        
        # Check JavaScript/TypeScript files
        for js_file in list(self.project_path.rglob("*.js")) + list(self.project_path.rglob("*.ts")):
            self._check_js_imports(js_file)
    
    def _check_python_imports(self, file_path: Path) -> None:
        """Check Python imports in a file."""
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except SyntaxError as e:
            self.issues.append(IntegrityIssue(
                type=IssueType.SYNTAX_ERROR,
                message=f"Python syntax error: {e}",
                file_path=file_path,
                line_number=e.lineno,
                severity="error"
            ))
            return
        except Exception as e:
            logger.debug(f"Could not parse Python file {file_path}: {e}")
            return
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self._verify_python_module(alias.name, file_path, node.lineno)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    self._verify_python_module(node.module, file_path, node.lineno)
    
    def _verify_python_module(self, module_name: str, file_path: Path, line_number: int) -> None:
        """Verify a Python module exists."""
        # Skip built-in and third-party modules
        if "." not in module_name or module_name.split(".")[0] in {
            "os", "sys", "json", "re", "pathlib", "typing", "dataclasses", 
            "logging", "argparse", "ast", "collections", "enum", "functools",
            "pydantic", "fastapi", "anthropic", "openai", "dotenv"
        }:
            return
        
        # Check if it's a relative import within the project
        module_path = self.project_path / Path(module_name.replace(".", "/")).with_suffix(".py")
        
        if not module_path.exists():
            # Also check for __init__.py in package
            package_path = self.project_path / Path(module_name.replace(".", "/")) / "__init__.py"
            if not package_path.exists():
                self.issues.append(IntegrityIssue(
                    type=IssueType.MISSING_IMPORT,
                    message=f"Missing module '{module_name}' referenced in {file_path.relative_to(self.project_path)}",
                    file_path=file_path,
                    line_number=line_number,
                    severity="error"
                ))
    
    def _check_js_imports(self, file_path: Path) -> None:
        """Check JavaScript/TypeScript imports."""
        try:
            content = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.debug(f"Could not read JS file {file_path}: {e}")
            return
        
        # Patterns for different import styles
        patterns = [
            r"from ['\"](.+?)['\"]",  # ES6 imports
            r"require\(['\"](.+?)['\"]\)",  # CommonJS requires
            r"import.*?from ['\"](.+?)['\"]",  # Alternative ES6 syntax
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, content):
                module_name = match.group(1)
                line_number = content[:match.start()].count('\n') + 1
                
                # Only check relative imports (starting with . or /)
                if module_name.startswith(".") or module_name.startswith("/"):
                    self._verify_js_module(module_name, file_path, line_number)
    
    def _verify_js_module(self, module_name: str, file_path: Path, line_number: int) -> None:
        """Verify a JavaScript module exists."""
        if module_name.startswith("."):
            # Relative import
            target_path = (file_path.parent / module_name).resolve()
            
            # Check various extensions
            possible_paths = [
                target_path,
                target_path.with_suffix(".js"),
                target_path.with_suffix(".ts"),
                target_path.with_suffix(".tsx"),
                target_path.with_suffix(".jsx"),
                target_path / "index.js",
                target_path / "index.ts",
            ]
            
            if not any(p.exists() for p in possible_paths):
                self.issues.append(IntegrityIssue(
                    type=IssueType.MISSING_IMPORT,
                    message=f"Missing module '{module_name}' referenced in {file_path.relative_to(self.project_path)}",
                    file_path=file_path,
                    line_number=line_number,
                    severity="error"
                ))
    
    def _check_syntax(self) -> None:
        """Check for basic syntax errors."""
        # Python syntax checking is done in _check_python_imports
        pass
    
    def format_report(self, report: ValidationReport) -> str:
        """Format validation report as markdown.
        
        Args:
            report: ValidationReport to format
            
        Returns:
            Formatted markdown report
        """
        if not report.issues:
            return "# Project Integrity Report\n\n✅ No issues detected. Project looks good!"
        
        lines = [
            "# Project Integrity Report",
            "",
            f"**Project:** {report.project_path}",
            f"**Files:** {report.total_files}",
            f"**Directories:** {report.total_directories}",
            f"**Issues found:** {len(report.issues)}",
            ""
        ]
        
        # Group issues by type
        issues_by_type = {}
        for issue in report.issues:
            issue_type = issue["type"]
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        # Add sections for each issue type
        for issue_type, issues in issues_by_type.items():
            lines.append(f"## {issue_type.replace('_', ' ').title()}")
            lines.append("")
            
            for issue in issues:
                severity_icon = "🔴" if issue["severity"] == "error" else "⚠️" if issue["severity"] == "warning" else "ℹ️"
                line = f"{severity_icon} {issue['message']}"
                
                if issue.get("file_path") and issue.get("line_number"):
                    line += f" (line {issue['line_number']})"
                
                lines.append(f"- {line}")
            
            lines.append("")
        
        return "\n".join(lines)
    
    def write_report(self, report: ValidationReport, output_path: Path) -> None:
        """Write report to file.
        
        Args:
            report: ValidationReport to write
            output_path: Path to write report to
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        content = self.format_report(report)
        output_path.write_text(content, encoding="utf-8")
        logger.info(f"Validation report written to {output_path}")


def validate_project(project_path: Path, output_path: Path | None = None) -> ValidationReport:
    """Validate a project and optionally write report.
    
    Args:
        project_path: Path to project to validate
        output_path: Optional path to write report
        
    Returns:
        ValidationReport
    """
    validator = ProjectIntegrityValidator(project_path)
    report = validator.validate()
    
    if output_path:
        validator.write_report(report, output_path)
    
    return report
