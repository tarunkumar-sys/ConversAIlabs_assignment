"""
Editor.

For each file in the ExecutionPlan, reads its current contents, asks the LLM
for a complete updated version implementing the relevant piece of the plan,
and overwrites the file on disk. Also supports targeted fix-up edits during
verification retries.
"""
from __future__ import annotations

from pathlib import Path

from agent.models import ExecutionPlan, EditResult
from agent.prompts import EDITOR_SYSTEM, EDITOR_PROMPT_TEMPLATE, FIX_PROMPT_TEMPLATE
from agent.utils import LLMClient, get_logger, strip_code_fence

logger = get_logger("editing")


def apply_edits(repo_path: Path, plan: ExecutionPlan, user_task: str, llm: LLMClient) -> list[EditResult]:
    """Applies planned code changes across specified files using the LLM.

    Args:
        repo_path: Root directory of the repository under edit.
        plan: Execution plan containing files to modify and step-by-step instructions.
        user_task: The original task requested by the user.
        llm: Initialized LLM client.

    Returns:
        A list of EditResult objects tracking modified files and status.
    """
    results: list[EditResult] = []

    for rel_path in plan.files_to_modify:
        file_path = repo_path / rel_path
        logger.info(f"Editing {rel_path}")

        # Read original contents or prepare for creation if new file
        if not file_path.exists():
            logger.warning(f"{rel_path} does not exist yet — creating new file")
            file_path.parent.mkdir(parents=True, exist_ok=True)
            original_contents = ""
        else:
            original_contents = file_path.read_text(encoding="utf-8", errors="ignore")

        # Format prompt with current file content and instructions
        prompt = EDITOR_PROMPT_TEMPLATE.format(
            file_path=rel_path,
            file_contents=original_contents or "(empty / new file)",
            user_task=user_task,
            file_instructions=plan.raw_text,
        )

        try:
            # Query LLM for updated code and strip markdown fences
            updated_contents = llm.complete(system=EDITOR_SYSTEM, prompt=prompt)
            updated_contents = strip_code_fence(updated_contents)
            file_path.write_text(updated_contents, encoding="utf-8")
            
            # Record whether content actually changed
            changed = updated_contents.strip() != original_contents.strip()
            results.append(EditResult(file_path=rel_path, changed=changed))
            logger.info(f"Wrote updated contents for {rel_path} (changed={changed})")
        except Exception as e:
            logger.error(f"Failed to edit {rel_path}: {e}")
            results.append(EditResult(file_path=rel_path, changed=False, error=str(e)))

    return results


def apply_fix(repo_path: Path, rel_path: str, logs: str, llm: LLMClient) -> EditResult:
    """Used by the verifier's retry loop: re-edit a single file to fix a build error.

    Args:
        repo_path: Root directory of the repository.
        rel_path: Relative path of the file to fix.
        logs: Error output or stack trace from failed verification.
        llm: Initialized LLM client.

    Returns:
        An EditResult tracking whether the fix was applied successfully.
    """
    file_path = repo_path / rel_path
    logger.info(f"Applying fix to {rel_path} based on verification logs")

    if not file_path.exists():
        return EditResult(file_path=rel_path, changed=False, error="file not found")

    original_contents = file_path.read_text(encoding="utf-8", errors="ignore")
    prompt = FIX_PROMPT_TEMPLATE.format(
        file_path=rel_path,
        file_contents=original_contents,
        logs=logs,
    )

    try:
        # Ask LLM for fixed code using error logs
        updated_contents = llm.complete(system=EDITOR_SYSTEM, prompt=prompt)
        updated_contents = strip_code_fence(updated_contents)
        file_path.write_text(updated_contents, encoding="utf-8")
        changed = updated_contents.strip() != original_contents.strip()
        return EditResult(file_path=rel_path, changed=changed)
    except Exception as e:
        logger.error(f"Failed to apply fix to {rel_path}: {e}")
        return EditResult(file_path=rel_path, changed=False, error=str(e))

