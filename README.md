# Autonomous AI Coding Agent

> An end-to-end, production-grade autonomous coding agent built with **Python 3.11+** and **LangChain**. Capable of repository exploration, architectural analysis, structured execution planning, automated file editing, verification testing, and pull-request summary generation.

---

## 🌟 Architecture Overview

```
                      ┌────────────────────────┐
                      │  User Task & Repo URL │
                      └───────────┬────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  1. Repository Explorer      │
                   │     (Git clone & context)    │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  2. Architectural Analyzer   │
                   │     (LangChain + LLM)        │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  3. Execution Planner        │
                   │     (execution_plan.md)      │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  4. Automated Code Editor    │
                   │     (Preserves style/syntax) │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  5. Verification & Fix Loop  │
                   │     (npm test / npm start)   │
                   └──────────────┬───────────────┘
                                  │
                                  ▼
                   ┌──────────────────────────────┐
                   │  6. Engineering Summarizer   │
                   │     (output/SUMMARY.md)      │
                   └──────────────────────────────┘
```

---

## 🤖 Agent Workflow & Stage Lifecycle

The agent executes tasks through a **6-stage sequential pipeline**, ensuring predictable, verifiable software modifications without uncontrolled hallucinations:

1. **Repository Exploration (`agent/explorer.py`)**: Clones target repos into `workspace/`, scans file hierarchies (filtering out build artifacts like `node_modules`), and extracts context snippets.
2. **Architectural Analysis (`agent/analyzer.py`)**: Uses the LLM to identify frameworks, database schemas (Mongoose/Prisma), routing mechanisms (Express/Fastapi), and existing design patterns.
3. **Structured Execution Planning (`agent/planner.py`)**: Generates a strictly validated JSON/Pydantic plan (`execution_plan.md`) outlining specific target files, exact modification steps, and potential risk factors.
4. **Automated Code Editing (`agent/editor.py`)**: Applies modifications file-by-file while maintaining existing code style, preserving comments, and adhering to controller/model conventions.
5. **Verification & Self-Healing Loop (`agent/verifier.py`)**: Runs syntax validation (`node -c`), installs dependencies (`npm install`), and executes tests (`npm test`). If errors occur, it triggers an iterative repair loop (up to 3 retries) with full error stack traces fed back into the LLM.
6. **Engineering Summarizer (`agent/summarizer.py`)**: Generates a Pull-Request style report (`output/SUMMARY.md`) highlighting git diffs, changed files, verification logs, and assumptions made.

---

## 🔍 How the Repository is Explored

To operate efficiently over repositories of varying sizes without exceeding token limits or incurring high costs, the agent uses a **curated exploration strategy**:

* **Shallow Git Cloning**: Performs `git clone --depth 1` to retrieve the latest codebase snapshot fast.
* **Directory Tree Filtering**: Traverses the directory tree up to 400 entries while stripping out noise directories (`node_modules`, `.git`, `dist`, `build`, `coverage`) and lockfiles/binaries.
* **Heuristic Priority Scoring**: Categorizes and prioritizes files into 4 tiers:
  1. **Tier 0 (Manifests)**: `package.json`, `requirements.txt`, `README.md`
  2. **Tier 1 (Core Architecture)**: Files containing `model`, `controller`, `route`, `schema`, `api`, `src` in path hints
  3. **Tier 2 (Source Files)**: Common code extensions (`.js`, `.ts`, `.py`, `.json`, etc.)
  4. **Tier 3 (Auxiliary)**: Other non-ignored repository files
* **Bounded Context Snippets**: Collects snippets from top prioritized files (up to `MAX_FILES_TO_SUMMARIZE=20`, capped at 8KB per file) to construct a high-signal `ProjectContext` object for the LLM.

---

## ⚖️ Key Assumptions & Technical Trade-offs

| Domain | Decision / Approach | Trade-off & Rationale |
| :--- | :--- | :--- |
| **Code Exploration** | Heuristic file snippet curation over vector embedding search (RAG) | **Trade-off**: For giant mono-repos, non-curated files might be missed. <br>**Rationale**: Fast, zero-overhead execution for small-to-medium repos without requiring external database setup. |
| **Code Editing** | Full file overwrite via structured LLM prompt instructions | **Trade-off**: Higher token usage per modified file. <br>**Rationale**: Simpler and less error-prone than fuzzy diff patching or line regex replacements across arbitrary JS syntax. |
| **Verification Harness** | Native local shell subprocess execution (`npm test` / `node -c`) | **Trade-off**: Executes code directly on host machine instead of an isolated sandbox container. <br>**Rationale**: Maximum execution speed and minimal runtime dependencies without requiring Docker. |
| **Retry Strategy** | Bounded self-healing loop (Max 3 repair attempts) | **Trade-off**: May halt on complex cascading failures requiring manual architectural refactoring. <br>**Rationale**: Prevents infinite LLM repair loops and runaway API costs. |

---

## 📋 System Prerequisites

| Dependency | Required Version | Description |
| :--- | :--- | :--- |
| **Python** | `3.11+` | Core execution environment for the agent framework |
| **Node.js & npm** | `18.x+` | Required for project verification (`npm install`, `npm test`, `npm run build`) |
| **Git** | Latest | Required for cloning and inspecting target repositories |

---

## 🚀 Quickstart & Setup

### 1. Environment Setup

Clone this repository and create a Python 3.11 virtual environment:

```powershell
# Create virtual environment
py -3.11 -m venv .venv

# Activate virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate virtual environment (Linux / macOS)
source .venv/bin/activate
```

### 2. Dependency Installation

Install all required Python dependencies:

```bash
pip install -r requirements.txt
```

---

## ⚙️ LLM Provider Configuration (`.env`)

Create a `.env` file in the root directory and choose your preferred LLM provider:

### Option A: Google Gemini (Recommended)
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

### Option B: OpenAI or Ollama (Local)
```env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1
```

---

## 🏃 Usage & Execution Examples

### Basic Command Syntax

```bash
python main.py --repo <GITHUB_REPO_URL> --task "<NATURAL_LANGUAGE_INSTRUCTION>"
```

### Example Commands

#### 1. Full Autonomous Workflow
```powershell
python main.py --repo https://github.com/callicoder/node-easy-notes-app --task "Improve the application so users can better organize and search their notes."
```

#### 2. Fast Execution Mode (`--skip-verify`)
Skips post-edit verification (`npm install` / `npm test`) for rapid iteration:
```powershell
python main.py --repo https://github.com/callicoder/node-easy-notes-app --task "Add category tag filtering to notes controller" --skip-verify
```

#### 3. Verbose Debugging Mode (`--verbose`)
Prints detailed internal execution logs and LLM completion prompts directly to stdout:
```powershell
python main.py --repo https://github.com/callicoder/node-easy-notes-app --task "Add pinned notes feature" --verbose
```

#### 4. Clean Workspace Re-clone (`--force-clone`)
Deletes existing workspace artifacts and re-clones the target repository:
```powershell
python main.py --repo https://github.com/callicoder/node-easy-notes-app --task "Implement note search and sorting APIs" --force-clone
```

---

## 🚩 Command-Line Arguments Reference

| Argument | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `--repo` | `string` | **Yes** | Target GitHub repository URL to clone and analyze |
| `--task` | `string` | **Yes** | High-level natural language prompt describing the feature request |
| `--skip-verify` | `flag` | No | Bypasses automated project verification (`npm test`, build scripts) |
| `--force-clone` | `flag` | No | Forces re-cloning of the target repository into `workspace/` |
| `--verbose` | `flag` | No | Enables detailed debug logging output in terminal |

---

## 📂 Generated Artifacts

Each successful run produces persistent documentation in the `output/` directory:

- **`output/execution_plan.md`**: Contains the exact breakdown of target files, implementation steps, and architectural risk assessment.
- **`output/SUMMARY.md`**: PR-style engineering report documenting technical changes, assumptions, modified file diffs, and verification logs.


