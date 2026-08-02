"""
Central configuration for the AI Coding Agent.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# --- Paths -----------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = ROOT_DIR / "workspace"
LOGS_DIR = ROOT_DIR / "logs"
OUTPUT_DIR = ROOT_DIR / "output"

for d in (WORKSPACE_DIR, LOGS_DIR, OUTPUT_DIR):
    d.mkdir(parents=True, exist_ok=True)

# --- LLM provider ------------------------------------------------------------
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "qwen2.5-coder:latest")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")

MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# --- Agent behavior ----------------------------------------------------------
MAX_FILES_TO_SUMMARIZE = int(os.getenv("MAX_FILES_TO_SUMMARIZE", "40"))
MAX_FILE_BYTES_FOR_CONTEXT = int(os.getenv("MAX_FILE_BYTES_FOR_CONTEXT", "20_000"))
MAX_VERIFICATION_RETRIES = int(os.getenv("MAX_VERIFICATION_RETRIES", "3"))
COMMAND_TIMEOUT_SECONDS = int(os.getenv("COMMAND_TIMEOUT_SECONDS", "180"))

# Output filenames
EXECUTION_PLAN_FILENAME = "execution_plan.md"
SUMMARY_FILENAME = "SUMMARY.md"

# Directories/files we never want to feed to the LLM or walk into.
IGNORE_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", ".cache", "coverage", ".idea", ".vscode",
}
IGNORE_FILE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".svg", ".woff", ".woff2",
    ".ttf", ".eot", ".lock", ".map", ".zip", ".tar", ".gz",
}

# Files that are especially informative about a project's shape.
HIGH_VALUE_FILENAMES = {
    "package.json", "requirements.txt", "pyproject.toml", "Cargo.toml",
    "go.mod", "pom.xml", "build.gradle", "README.md", "readme.md",
    "Dockerfile", "docker-compose.yml", ".env.example",
}
