# Contributing to AI Desk Dashboard

Thank you for your interest in contributing! We welcome bug fixes, performance improvements, new data collectors, and display backends.

To keep the project clean, fast, and reliable, please follow these guidelines:

---

## 1. General Principles

- **Open an Issue First for Large Changes**: If you plan to add a new display backend, introduce a major UI redesign, or alter the core engine, open an issue first to discuss the design.
- **Small, Focused Pull Requests**: Keep pull requests tightly scoped to a single feature or bug fix.
- **Minimal Dependencies**: The core runtime relies on pure Python standard library plus `pillow`, `pyserial`, `requests`, and `psutil`. Do not introduce heavyweight dependencies (no Electron, no web servers, no Qt).
- **Independent Component Failure**: Every integration must fail gracefully. A failure or timeout in one collector must never break another collector or crash the application.
- **Preserve Fallback Behavior**: The desktop companion app must remain 100% operational even when no physical hardware is attached.
- **No Secrets or Machine-Specific Configuration**: Never commit API keys, personal paths (`D:\...`, `C:\Users\<user>\...`), private IP addresses, or hardcoded COM port numbers. Always use relative paths and auto-detection.

---

## 2. Development Workflow

### Setup

```powershell
# Clone and setup virtual environment
git clone https://github.com/Tacdelgineer/Divoom-display.git
cd Divoom-display
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

### Running Checks & Tests

Before submitting a pull request:

```powershell
# 1. Validate Python syntax and compilation across all modules
python -m compileall .

# 2. Run test suite
pytest tests/ -v

# 3. Verify terminal status report runs without errors
python dashboard.py --status

# 4. Verify preview frame rendering
python dashboard.py --preview
```

---

## 3. Pull Request Guidelines

1. **Branch Naming**: Use descriptive branch names like `feature/ollama-collector` or `fix/reconnect-timeout`.
2. **Commit Messages**: Write clear, imperative commit messages (e.g., `Add Ollama local LLM health probe`, `Fix COM port probing timeout on Windows`).
3. **Documentation**: Update [README.md](README.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), or [AGENTS.md](AGENTS.md) if your change adds new configurations, CLI flags, or collectors.
4. **Subprocess Safety**: On Windows, all child processes must use `subproc.py` (`CREATE_NO_WINDOW`, `SW_HIDE`, `shell=False`) to prevent console window popping.
