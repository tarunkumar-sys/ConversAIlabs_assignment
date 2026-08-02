"""
LLM Client supporting Google Gemini and OpenAI via LangChain.
"""
from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from langchain_core.messages import SystemMessage, HumanMessage
import config


@dataclass
class CommandResult:
    """Dataclass encapsulating standard command execution output."""
    command: list[str]
    returncode: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        """Returns True if the command executed with exit code 0."""
        return self.returncode == 0


def get_logger(name: str = "agent") -> logging.Logger:
    """Returns a named logger instance for the agent."""
    return logging.getLogger(name)


def configure_logging(verbose: bool = False) -> None:
    """Configures root logger with file and console handlers."""
    level = logging.DEBUG if verbose else logging.INFO
    formatter = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    root = logging.getLogger()
    root.setLevel(level)

    for h in root.handlers[:]:
        root.removeHandler(h)

    # Log to file in LOGS_DIR
    fh = logging.FileHandler(config.LOGS_DIR / "agent.log", mode="a", encoding="utf-8")
    fh.setFormatter(formatter)
    fh.setLevel(level)
    root.addHandler(fh)

    # Log to console stdout/stderr
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging.DEBUG if verbose else logging.WARNING)
    root.addHandler(ch)


def run_command(cmd: list[str], cwd: Path, timeout: int | None = None) -> CommandResult:
    """Executes a shell command synchronously with a specified working directory and timeout."""
    timeout = timeout or config.COMMAND_TIMEOUT_SECONDS
    logger = get_logger("command")
    logger.debug(f"Running command in {cwd}: {' '.join(cmd)}")

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=(os.name == "nt"),
        )
        return CommandResult(
            command=cmd,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
        )
    except subprocess.TimeoutExpired:
        logger.warning(f"Command timed out after {timeout}s: {' '.join(cmd)}")
        return CommandResult(
            command=cmd,
            returncode=-1,
            stdout="",
            stderr=f"Command timed out after {timeout} seconds",
        )
    except Exception as e:
        logger.error(f"Command execution error: {e}")
        return CommandResult(
            command=cmd,
            returncode=-1,
            stdout="",
            stderr=str(e),
        )


def strip_code_fence(text: str) -> str:
    """Strips markdown ``` code block fences from LLM text output."""
    stripped = text.strip()
    if stripped.startswith("```"):
        lines = stripped.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        stripped = "\n".join(lines)
    return stripped


class LLMClient:
    """Wrapper around LangChain ChatGoogleGenerativeAI / ChatOpenAI for agent LLM queries."""

    def __init__(self) -> None:
        if config.LLM_PROVIDER == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            api_key = config.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY is not set in environment or config.")
            self._model = ChatGoogleGenerativeAI(
                model=config.GEMINI_MODEL,
                google_api_key=api_key,
                max_output_tokens=config.MAX_TOKENS,
                temperature=0.2,
            )
            self.model_name = config.GEMINI_MODEL
        else:
            from langchain_openai import ChatOpenAI
            api_key = config.OPENAI_API_KEY if config.OPENAI_API_KEY else "ollama"
            base_url = config.OPENAI_BASE_URL if config.OPENAI_BASE_URL else None
            self._model = ChatOpenAI(
                model=config.OPENAI_MODEL,
                api_key=api_key,
                base_url=base_url,
                max_tokens=config.MAX_TOKENS,
                temperature=0.2,
            )
            self.model_name = config.OPENAI_MODEL

        self.total_tokens = 0

    def complete(self, system: str, prompt: str, max_tokens: int | None = None) -> str:
        """Sends system and prompt messages to LLM and tracks token usage."""
        messages = [
            SystemMessage(content=system),
            HumanMessage(content=prompt),
        ]
        kwargs = {}
        if max_tokens:
            if config.LLM_PROVIDER == "gemini":
                kwargs["max_output_tokens"] = max_tokens
            else:
                kwargs["max_tokens"] = max_tokens

        response = self._model.invoke(messages, **kwargs)

        usage = getattr(response, "usage_metadata", {}) or response.response_metadata.get("token_usage", {})
        if "total_tokens" in usage:
            self.total_tokens += usage["total_tokens"]

        return str(response.content) or ""

