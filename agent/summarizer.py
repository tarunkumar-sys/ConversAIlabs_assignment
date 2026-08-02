"""
Summarizer.

Produces output/SUMMARY.md describing what was analyzed, planned, changed,
and verified — written like a PR description.
"""
from __future__ import annotations

from agent.models import ProjectSummary, ExecutionPlan, EditResult, VerificationResult
from agent.prompts import SUMMARY_SYSTEM, SUMMARY_PROMPT_TEMPLATE
from agent.utils import LLMClient, get_logger
import config

logger = get_logger("summary")


def _format_files_modified(results: list[EditResult]) -> str:
    lines = []
    for r in results:
        status = "modified" if r.changed else ("unchanged" if not r.error else f"ERROR: {r.error}")
        lines.append(f"- `{r.file_path}` — {status}")
    return "\n".join(lines) if lines else "(no files modified)"


def _format_verification(result: VerificationResult) -> str:
    status = "PASSED" if result.success else "FAILED"
    return (
        f"Status: {status} (after {result.attempts} attempt(s))\n\n"
        f"```\n{result.log_excerpt}\n```"
    )


def generate_summary(
    repo_url: str,
    user_task: str,
    project_summary: ProjectSummary,
    plan: ExecutionPlan,
    edit_results: list[EditResult],
    verification_result: VerificationResult,
    llm: LLMClient,
) -> str:
    logger.info("Generating final summary")

    prompt = SUMMARY_PROMPT_TEMPLATE.format(
        repo_url=repo_url,
        user_task=user_task,
        project_summary=project_summary.raw_text,
        execution_plan=plan.raw_text,
        files_modified=_format_files_modified(edit_results),
        verification_result=_format_verification(verification_result),
    )

    summary_md = llm.complete(system=SUMMARY_SYSTEM, prompt=prompt)

    output_path = config.OUTPUT_DIR / config.SUMMARY_FILENAME
    output_path.write_text(summary_md)
    logger.info(f"Summary written to {output_path}")

    return summary_md
