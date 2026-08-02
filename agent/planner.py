"""
Planner.

Takes the ProjectSummary and the user's natural-language task and asks the
LLM to choose the smallest useful implementation, returning an ExecutionPlan
with a concrete list of files to modify.
"""
from __future__ import annotations

import re
from pathlib import Path

import config
from agent.models import ProjectSummary, ExecutionPlan
from agent.prompts import PLANNER_SYSTEM, PLANNER_PROMPT_TEMPLATE
from agent.utils import LLMClient, get_logger

logger = get_logger("planning")


def _extract_files_to_modify(plan_text: str) -> list[str]:
    """Extracts targeted file paths from the planner's LLM output.

    Handles text formats like:
    - "Files to modify: app/models/note.model.js, app/controllers/note.controller.js"
    - Markdown bullet points or inline code blocks.
    """
    match = re.search(r"Files to modify:\s*(.+)", plan_text, re.IGNORECASE)
    if not match:
        # Fallback regex search for any relative paths ending in common file extensions
        files = re.findall(r"([a-zA-Z0-9_\-/]+\.(?:js|ts|py|jsx|tsx|html|css|json|ejs))", plan_text)
        # Deduplicate preserving order
        return list(dict.fromkeys(files))
    
    raw = match.group(1).strip()
    raw = raw.splitlines()[0]
    # Clean up whitespace, backticks, and list markdown symbols
    files = [f.strip().strip("`* -") for f in raw.split(",") if f.strip()]
    return files


def create_plan(project_summary: ProjectSummary, user_task: str, llm: LLMClient) -> ExecutionPlan:
    """Queries the LLM to generate an execution plan for a user task based on project summary."""
    logger.info(f"Planning implementation for task: {user_task!r}")
    prompt = PLANNER_PROMPT_TEMPLATE.format(
        user_task=user_task,
        project_summary=project_summary.raw_text,
    )
    # Query LLM with planner system prompt
    response_text = llm.complete(system=PLANNER_SYSTEM, prompt=prompt)

    # Parse out target files to edit
    files = _extract_files_to_modify(response_text)
    logger.info(f"Plan proposes modifying: {files}")

    return ExecutionPlan(raw_text=response_text, files_to_modify=files)


def save_plan_to_file(plan: ExecutionPlan, user_task: str) -> Path:
    """Persists the execution plan to output/execution_plan.md as a standalone artifact of the run."""
    output_path = config.OUTPUT_DIR / config.EXECUTION_PLAN_FILENAME
    content = (
        f"# Execution Plan\n\n"
        f"**User request:** {user_task}\n\n"
        f"```\n{plan.raw_text.strip()}\n```\n"
    )
    output_path.write_text(content)
    logger.info(f"Execution plan written to {output_path}")
    return output_path

