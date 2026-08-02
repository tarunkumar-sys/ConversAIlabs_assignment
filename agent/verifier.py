"""
Verifier.

Installs dependencies and attempts to build/run the project after edits are
applied. If it fails, feeds the logs back to the editor for a targeted fix,
up to config.MAX_VERIFICATION_RETRIES times.

Handles the common case of `npm start` launching a long-running dev server:
a command that is still running after a short grace period is treated as a
successful start rather than a failure, since a real crash surfaces almost
immediately in stdout/stderr.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from agent.models import ExecutionPlan, VerificationResult
from agent.utils import LLMClient, get_logger, run_command
from agent.editor import apply_fix
import config

logger = get_logger("verification")

SERVER_START_GRACE_SECONDS = 15


def _npm_scripts(repo_path: Path) -> dict:
    """Reads scripts dictionary from package.json if present."""
    pkg = repo_path / "package.json"
    if not pkg.exists():
        return {}
    try:
        return json.loads(pkg.read_text()).get("scripts", {})
    except Exception:
        return {}


def _run_node_project(repo_path: Path) -> tuple[bool, str]:
    """Runs npm install, build, test, and start verification steps for Node.js projects."""
    install = run_command(["npm", "install"], cwd=repo_path)
    if not install.ok:
        return False, f"$ npm install\n{install.stdout}\n{install.stderr}"

    scripts = _npm_scripts(repo_path)
    log_parts = [f"$ npm install\n{install.stdout[-500:]}"]
    ran_a_check = False

    # Execute build script if defined
    if "build" in scripts:
        build = run_command(["npm", "run", "build"], cwd=repo_path)
        log_parts.append(f"$ npm run build\n{build.stdout}\n{build.stderr}")
        if not build.ok:
            return False, "\n".join(log_parts)
        ran_a_check = True

    # Execute test script if defined
    if "test" in scripts:
        test = run_command(["npm", "test"], cwd=repo_path)
        test_out = f"{test.stdout}\n{test.stderr}"
        # Skip failure if it's just the default NPM placeholder script "no test specified"
        if not test.ok and "no test specified" not in test_out.lower():
            log_parts.append(f"$ npm test\n{test_out}")
            return False, "\n".join(log_parts)
        if test.ok:
            log_parts.append(f"$ npm test\n{test_out}")
            ran_a_check = True

    # Execute start script with grace period handling for long-running servers
    if "start" in scripts:
        try:
            result = run_command(
                ["npm", "start"], cwd=repo_path, timeout=SERVER_START_GRACE_SECONDS
            )
        except Exception as e:
            return False, str(e)

        if result.returncode == -1 and "timed out" in result.stderr.lower():
            log_parts.append("$ npm start\nDev server started successfully without immediate crash.")
            return True, "\n".join(log_parts)
        if result.ok:
            log_parts.append(f"$ npm start\n{result.stdout}")
            return True, "\n".join(log_parts)
        
        # If server crashed on startup, return error
        log_parts.append(f"$ npm start\n{result.stdout}\n{result.stderr}")
        return False, "\n".join(log_parts)

    if ran_a_check:
        return True, "\n".join(log_parts)

    return True, "No build or start script found; install succeeded, skipping run step."


def _run_python_project(repo_path: Path) -> tuple[bool, str]:
    """Runs pip install and python syntax compilation for Python projects."""
    install = run_command(["pip", "install", "-r", "requirements.txt", "--quiet"], cwd=repo_path)
    if not install.ok:
        return False, f"$ pip install -r requirements.txt\n{install.stdout}\n{install.stderr}"
    compile_check = run_command(
        ["python", "-m", "compileall", "-q", "."], cwd=repo_path
    )
    if compile_check.ok:
        return True, "Dependencies installed and all files compiled cleanly."
    return False, f"$ python -m compileall .\n{compile_check.stdout}\n{compile_check.stderr}"


def _guess_offending_file(logs: str, candidate_files: list[str]) -> str | None:
    """Attempts to identify the file causing build/run failure from error logs."""
    for f in candidate_files:
        if f in logs:
            return f
    match = re.search(r"([a-zA-Z0-9_\-/]+\.(?:js|ts|py|jsx|tsx|ejs))", logs)
    return match.group(1) if match else None


def verify_and_fix(repo_path: Path, plan: ExecutionPlan, llm: LLMClient) -> VerificationResult:
    """Runs build/run checks on the codebase and triggers fix loops if errors occur."""
    attempts = 0
    logs = ""

    while attempts < config.MAX_VERIFICATION_RETRIES:
        attempts += 1
        logger.info(f"Verification attempt {attempts}")

        # Check project type and run appropriate verification
        if (repo_path / "package.json").exists():
            success, logs = _run_node_project(repo_path)
        elif (repo_path / "requirements.txt").exists() or (repo_path / "pyproject.toml").exists():
            success, logs = _run_python_project(repo_path)
        else:
            logger.warning("No recognized project type for verification; skipping run step")
            success, logs = True, "No recognized package manifest; skipped automated verification."

        if success:
            logger.info("Verification succeeded")
            return VerificationResult(success=True, attempts=attempts, log_excerpt=logs[-3000:])

        logger.warning(f"Verification failed on attempt {attempts}:\n{logs[-1500:]}")

        if attempts >= config.MAX_VERIFICATION_RETRIES:
            break

        # Attempt auto-fix for offending file
        offending_file = _guess_offending_file(logs, plan.files_to_modify)
        if not offending_file:
            logger.warning("Could not identify offending file from logs; stopping retry loop")
            break

        apply_fix(repo_path, offending_file, logs, llm)

    return VerificationResult(success=False, attempts=attempts, log_excerpt=logs[-3000:])

