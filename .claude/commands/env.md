# Environment Skills

## Programming Language
- This repository uses **Python** as the primary programming language.

## Environment Management
- This repository uses **uv** as the default environment and package management tool.
- Use `uv` for all dependency installation, virtual environment creation, and package management tasks.
- Prefer `uv run` to execute Python scripts within the managed environment.
- Prefer `uv add` to add dependencies instead of `pip install`.
- Prefer `uv sync` to synchronize the environment from lockfiles.
