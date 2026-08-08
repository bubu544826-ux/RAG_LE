# Repository Guidelines

## Project Structure & Module Organization

The FastAPI application lives in `backend/`. `app.py` defines HTTP routes and serves the static client; RAG orchestration, document ingestion, vector storage, search tools, session state, configuration, and model integrations are split into focused modules alongside it. Backend tests are in `backend/tests/` and follow the source features they exercise. The browser client is plain HTML, CSS, and JavaScript under `frontend/`. Course transcripts used for ingestion live in `docs/`. Root-level scripts provide common development workflows.

## Build, Test, and Development Commands

- `uv sync --dev` installs locked runtime and development dependencies for Python 3.13+.
- `./run.sh` starts Uvicorn with reload on port 8000; open `http://localhost:8000`.
- `uv run pytest` runs the complete test suite configured in `pyproject.toml`.
- `uv run pytest backend/tests/test_api.py -q` runs one test module during iteration.
- `./scripts/format.sh` formats Python files with Black.
- `./scripts/check-quality.sh` checks backend formatting without modifying files.

Run the application from the repository root because backend paths are relative to `backend/`.

## Coding Style & Naming Conventions

Use four-space indentation and Black's 88-character line length for Python. Prefer type hints, small single-purpose modules, and concise docstrings for public classes, fixtures, and endpoints. Use `snake_case` for functions, variables, modules, and test names; use `PascalCase` for classes and Pydantic models; use uppercase names for configuration constants. Keep frontend code dependency-free unless a project-wide change is explicitly justified.

## Testing Guidelines

Pytest discovers `backend/tests/test_*.py`. Name tests `test_<behavior>` and group reusable setup in `conftest.py`. Mock Anthropic, embedding, vector-store, and filesystem boundaries so routine tests remain deterministic and do not require credentials or network access. Add regression coverage for bug fixes and endpoint status codes, response bodies, and session side effects. No numeric coverage threshold is configured; prioritize meaningful behavior coverage.

## Commit & Pull Request Guidelines

Recent history favors short Conventional Commit-style subjects such as `feat: improve chat interface`, `test: add backend API test suite`, and `chore: ...`. Keep commits focused and use an imperative summary. Pull requests should explain the user-visible change, list verification commands, link related issues, and call out configuration or data changes. Include screenshots for frontend changes and sample request/response payloads for API changes.

## Security & Configuration

Store `ANTHROPIC_API_KEY` only in the root `.env`; never commit credentials, `backend/chroma_db/`, virtual environments, or uploaded data. When adding settings, document safe defaults in `backend/config.py` and update the README when setup changes.
