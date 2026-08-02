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
    """
    Pull the comma-separated or list-formatted file paths out of the planner response.
    Handles formats like:
    - "Files to modify: app/models/note.model.js, app/controllers/note.controller.js"
    - Markdown bullet points or inline code blocks.
    """
    match = re.search(r"Files to modify:\s*(.+)", plan_text, re.IGNORECASE)
    if not match:
        # Fallback regex search for any relative paths ending in common extensions
        files = re.findall(r"([a-zA-Z0-9_\-/]+\.(?:js|ts|py|jsx|tsx|html|css|json|ejs))", plan_text)
        # Deduplicate preserving order
        return list(dict.fromkeys(files))
    
    raw = match.group(1).strip()
    raw = raw.splitlines()[0]
    files = [f.strip().strip("`* -") for f in raw.split(",") if f.strip()]
    return files


def create_plan(project_summary: ProjectSummary, user_task: str, llm: LLMClient) -> ExecutionPlan:
    logger.info(f"Planning implementation for task: {user_task!r}")
    prompt = PLANNER_PROMPT_TEMPLATE.format(
        user_task=user_task,
        project_summary=project_summary.raw_text,
    )
    response_text = llm.complete(system=PLANNER_SYSTEM, prompt=prompt)

    files = _extract_files_to_modify(response_text)
    logger.info(f"Plan proposes modifying: {files}")

    return ExecutionPlan(raw_text=response_text, files_to_modify=files)


def save_plan_to_file(plan: ExecutionPlan, user_task: str) -> Path:
    """
    Persist the execution plan to output/execution_plan.md so it is visible
    as a standalone artifact of the run, independent of the final SUMMARY.md.
    """
    output_path = config.OUTPUT_DIR / config.EXECUTION_PLAN_FILENAME
    content = (
        f"# Execution Plan\n\n"
        f"**User request:** {user_task}\n\n"
        f"```\n{plan.raw_text.strip()}\n```\n"
    )
    output_path.write_text(content)
    logger.info(f"Execution plan written to {output_path}")
    return output_path
