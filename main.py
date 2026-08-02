"""
AI Coding Agent — CLI entry point (Standard Console I/O).

Usage:
    python main.py --repo <github_url> --task "<natural language task>" [options]
"""
from __future__ import annotations

import argparse
import sys
import time

import config
from agent.explorer import clone_repo, collect_project_context
from agent.analyzer import analyze_project
from agent.planner import create_plan, save_plan_to_file
from agent.editor import apply_edits
from agent.verifier import verify_and_fix
from agent.summarizer import generate_summary
from agent.utils import LLMClient, get_logger, configure_logging

logger = get_logger("agent")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI Coding Agent CLI")
    parser.add_argument("--repo", required=True, help="GitHub repository URL to clone")
    parser.add_argument("--task", required=True, help="Natural language description of the change to make")
    parser.add_argument("--skip-verify", action="store_true", help="Skip the build/run verification step")
    parser.add_argument("--force-clone", action="store_true", help="Force re-cloning the repository")
    parser.add_argument("--verbose", action="store_true", help="Enable detailed logging output in terminal")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    start_time = time.time()

    configure_logging(args.verbose)

    print("=" * 60)
    print("AI Coding Agent (LangChain Powered)")
    print(f"Repo: {args.repo}")
    print(f"Task: {args.task}")
    print("=" * 60)

    modified_files = []

    try:
        print("\n[1/6] Initializing LangChain LLM Client...")
        llm = LLMClient()
        print(f"Using Model: {llm.model_name}")

        print("\n[2/6] Cloning repository...")
        repo_path = clone_repo(args.repo, force_reclone=args.force_clone)

        print("\n[3/6] Exploring repository structure...")
        context = collect_project_context(repo_path)
        print(f"Explored {len(context.file_snippets)} key files.")

        print("\n[4/6] Analyzing codebase with LLM...")
        project_summary = analyze_project(context, llm)

        print("\n[5/6] Generating execution plan...")
        plan = create_plan(project_summary, args.task, llm)
        plan_path = save_plan_to_file(plan, args.task)
        print(f"Execution plan written to: {plan_path}")
        if not plan.files_to_modify:
            print("Error: Planner did not return any files to modify.")
            return 1
        print(f"Files to modify: {', '.join(plan.files_to_modify)}")

        print("\n[6/6] Applying edits...")
        edit_results = apply_edits(repo_path, plan, args.task, llm)

        for r in edit_results:
            if r.error:
                print(f"  [ERROR] {r.file_path}: {r.error}")
            elif r.changed:
                modified_files.append(r.file_path)
                print(f"  [MODIFIED] {r.file_path}")
            else:
                print(f"  [UNCHANGED] {r.file_path}")

        if args.skip_verify:
            print("\nSkipping verification (--skip-verify set).")
            from agent.models import VerificationResult
            verification_result = VerificationResult(success=True, attempts=0, log_excerpt="Skipped by user.")
        else:
            print("\nVerifying build & project tests...")
            verification_result = verify_and_fix(repo_path, plan, llm)
            if verification_result.success:
                print(f"Verification PASSED after {verification_result.attempts} attempt(s).")
            else:
                print(f"Verification FAILED after {verification_result.attempts} attempt(s).")

        print("\nGenerating final summary report...")
        generate_summary(
            repo_url=args.repo,
            user_task=args.task,
            project_summary=project_summary,
            plan=plan,
            edit_results=edit_results,
            verification_result=verification_result,
            llm=llm,
        )

        execution_time = time.time() - start_time
        print("\n" + "=" * 60)
        print("Execution Completed Successfully")
        print(f"Total Modified Files : {len(modified_files)}")
        print(f"Total Execution Time: {execution_time:.2f}s")
        print(f"Summary Report Path : {config.OUTPUT_DIR / config.SUMMARY_FILENAME}")
        print("=" * 60)

        return 0 if verification_result.success else 2

    except Exception as exc:
        print(f"\n[FATAL ERROR] {exc}")
        logger.error(f"Execution failed: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
