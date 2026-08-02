"""
Analyzer.

Takes the raw ProjectContext gathered by the explorer and asks the LLM to
produce a structured understanding of the repository (architecture, DB,
routing, models, where to hook in new functionality).
"""
from __future__ import annotations

from agent.models import ProjectContext, ProjectSummary
from agent.prompts import EXPLORER_SYSTEM, EXPLORER_PROMPT_TEMPLATE
from agent.utils import LLMClient, get_logger

logger = get_logger("analysis")


def _build_context_blob(context: ProjectContext) -> str:
    """Formats directory tree and file snippets into a single text block for the LLM."""
    parts = [f"Directory tree:\n{context.file_tree}\n"]
    if context.detected_package_manager:
        parts.append(f"Detected package manager: {context.detected_package_manager}\n")
    # Append snippets of key project files (e.g. package.json, main entry points)
    for path, content in context.file_snippets.items():
        parts.append(f"--- {path} ---\n{content}\n")
    return "\n".join(parts)


def analyze_project(context: ProjectContext, llm: LLMClient) -> ProjectSummary:
    """Analyzes repository structure and snippets using LLM to generate high-level summary."""
    logger.info("Sending repository context to LLM for analysis")
    context_blob = _build_context_blob(context)
    prompt = EXPLORER_PROMPT_TEMPLATE.format(context=context_blob)

    # Prompt LLM with system prompt and formatted repository context
    response_text = llm.complete(system=EXPLORER_SYSTEM, prompt=prompt)
    logger.info("Received project analysis from LLM")

    return ProjectSummary(raw_text=response_text)

