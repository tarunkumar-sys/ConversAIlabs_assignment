"""
Repository Explorer.

Responsible for:
- cloning the target repo into workspace/
- walking the directory tree
- collecting a small set of high-value files (package.json, README, models,
  controllers, routes, etc.) as context for the analyzer

Deliberately does NOT send every file to the LLM — it curates a bounded,
representative subset so the analyzer prompt stays cheap and fast.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import git

import config
from agent.models import ProjectContext
from agent.utils import get_logger

logger = get_logger("explorer")


def clone_repo(repo_url: str, dest_name: str | None = None, force_reclone: bool = False) -> Path:
    """Clone repo_url into workspace/<dest_name>, reusing existing clone unless force_reclone=True."""
    dest_name = dest_name or repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    dest_path = config.WORKSPACE_DIR / dest_name

    if dest_path.exists():
        if force_reclone:
            logger.info(f"Removing existing clone at {dest_path}")
            shutil.rmtree(dest_path, ignore_errors=True)
        else:
            logger.info(f"Using existing repository at {dest_path} (skipping clone)")
            return dest_path

    # Clean destination path if leftover partial/locked directory exists
    if dest_path.exists():
        shutil.rmtree(dest_path, ignore_errors=True)

    logger.info(f"Cloning {repo_url} -> {dest_path}")
    git.Repo.clone_from(repo_url, dest_path, depth=1)
    logger.info("Clone complete")
    return dest_path


def scan_tree(repo_path: Path, max_entries: int = 400) -> str:
    """Returns a text directory tree representation, skipping ignored directories and files."""
    lines: list[str] = []

    def walk(dir_path: Path, prefix: str = ""):
        if len(lines) >= max_entries:
            return
        try:
            entries = sorted(dir_path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return
        for entry in entries:
            if len(lines) >= max_entries:
                lines.append(f"{prefix}... (truncated)")
                return
            if entry.name in config.IGNORE_DIRS:
                continue
            if entry.is_dir():
                lines.append(f"{prefix}{entry.name}/")
                walk(entry, prefix + "  ")
            else:
                if entry.suffix.lower() in config.IGNORE_FILE_EXTENSIONS:
                    continue
                lines.append(f"{prefix}{entry.name}")

    walk(repo_path)
    return "\n".join(lines)


def _is_probably_source_file(path: Path) -> bool:
    """Checks if a file extension matches common source code or configuration files."""
    return path.suffix.lower() in {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".go", ".rb", ".php",
        ".ejs", ".html", ".json", ".md", ".yml", ".yaml", ".toml", ".cfg",
    }


def collect_project_context(repo_path: Path) -> ProjectContext:
    """Curates a bounded set of high-value files as initial context for LLM analysis.

    Collects:
    - package.json / requirements.txt / etc. (project manifests)
    - README files
    - key application files (models, controllers, routes, schemas)
    - source file samples capped by MAX_FILES_TO_SUMMARIZE
    """
    logger.info(f"Collecting project context from {repo_path}")

    # Generate repository tree representation
    file_tree = scan_tree(repo_path)

    interesting_dir_hints = {"model", "controller", "route", "view", "schema", "api", "src"}
    snippets: dict[str, str] = {}

    # List all non-ignored files in the target repository
    all_files = [
        p for p in repo_path.rglob("*")
        if p.is_file()
        and not any(part in config.IGNORE_DIRS for part in p.parts)
        and p.suffix.lower() not in config.IGNORE_FILE_EXTENSIONS
    ]

    # Prioritize key files: manifests (0), architecture files (1), source files (2), other (3)
    def priority(p: Path) -> int:
        if p.name in config.HIGH_VALUE_FILENAMES:
            return 0
        if any(hint in str(p.relative_to(repo_path)).lower() for hint in interesting_dir_hints):
            return 1
        if _is_probably_source_file(p):
            return 2
        return 3

    all_files.sort(key=priority)

    # Read top prioritized file snippets up to configured limits
    for p in all_files[: config.MAX_FILES_TO_SUMMARIZE]:
        try:
            content = p.read_text(errors="ignore")
        except Exception as e:
            logger.warning(f"Could not read {p}: {e}")
            continue
        if len(content) > config.MAX_FILE_BYTES_FOR_CONTEXT:
            content = content[: config.MAX_FILE_BYTES_FOR_CONTEXT] + "\n... (truncated)"
        snippets[str(p.relative_to(repo_path))] = content

    # Detect package manager / build tool
    package_manager = None
    if (repo_path / "package.json").exists():
        package_manager = "npm"
    elif (repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists():
        package_manager = "pip"
    elif (repo_path / "Cargo.toml").exists():
        package_manager = "cargo"
    elif (repo_path / "go.mod").exists():
        package_manager = "go"

    logger.info(f"Collected {len(snippets)} files, package manager: {package_manager}")

    return ProjectContext(
        repo_path=str(repo_path),
        file_tree=file_tree,
        file_snippets=snippets,
        detected_package_manager=package_manager,
    )

