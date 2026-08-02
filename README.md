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


