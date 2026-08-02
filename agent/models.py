"""Shared data structures passed between pipeline stages."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProjectContext:
    """Raw facts collected by the explorer, before any LLM reasoning."""
    repo_path: str
    file_tree: str
    file_snippets: dict[str, str] = field(default_factory=dict)  # path -> content
    detected_package_manager: str | None = None


@dataclass
class ProjectSummary:
    """LLM-generated understanding of the repository."""
    raw_text: str


@dataclass
class ExecutionPlan:
    """LLM-generated plan for satisfying the user's request."""
    raw_text: str
    files_to_modify: list[str]


@dataclass
class EditResult:
    """Result of attempting to apply an LLM-generated code edit to a file."""
    file_path: str
    changed: bool
    error: str | None = None


@dataclass
class VerificationResult:
    """Result of running verification steps (tests/builds) on the codebase."""
    success: bool
    attempts: int
    log_excerpt: str

