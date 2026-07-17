# AGENTS.md — moondream_api

## Project overview

REST API that runs the [Moondream](https://github.com/vikhyat/moondream) vision-language model locally or via Moondream Cloud. Exposes OpenAI- and Ollama-compatible endpoints so that existing integrations (Home Assistant, Frigate, etc.) can use it as a drop-in vision service.

Designed for edge hardware (Raspberry Pi, Orange Pi) and home-automation setups where camera frames need human-readable descriptions.

Single FastAPI application — no frontend, database, or microservice split.

## Tech stack

Python 3.14 · FastAPI · [uv](https://docs.astral.sh/uv/) · Docker (multi-stage) · GitHub Actions CI/CD · Ruff for linting

## Getting started

### Local (Python 3.13)

The project pins Python 3.13 locally because C-extension packages (`tiktoken`, `onnx`, `pydantic-core`) depend on PyO3 which only supports up to 3.13 on macOS ARM. Docker builds use Python 3.14 (builds from source).

```bash
# Local (uses .python-version → 3.13)
uv sync
uv run fastapi run ./src/api.py --host 0.0.0.0 --port 8000

# Docker
docker compose up -d
```

Service available at `localhost:8000` (local) or `localhost:18000` (Docker).

## Key commands

| Action | Command |
|---|---|
| Install deps | `uv sync` |
| Run locally | `uv run fastapi run ./src/api.py --host 0.0.0.0 --port 8000` |
| Run via Docker | `docker compose up -d` |
| Rebuild image | `docker compose up -d --build` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |

## Testing

Automated test suite with pytest + pytest-cov:

```bash
# Run all tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_routes.py -v

# Run tests without coverage
uv run pytest -v
```

Test structure:
- `tests/conftest.py` — shared fixtures (fake model, fake vision service, test client)
- `tests/test_api.py` — API app entry point
- `tests/test_api_lifespan.py` — lifespan lifecycle
- `tests/test_config.py` — Settings
- `tests/test_exceptions.py` — exception hierarchy
- `tests/test_model_downloader*.py` — model download logic
- `tests/test_routes.py` — HTTP endpoints (OpenAI, Ollama, health)
- `tests/test_schemas.py` — Pydantic model construction/validation
- `tests/test_vision_service*.py` — image loading, analysis, token costing

Interactive docs also available:
- Swagger UI: `http://localhost:18000/docs`
- ReDoc: `http://localhost:18000/redoc`

## API surface

The service exposes three groups of endpoints:

- **OpenAI-compatible** — `POST /v1/chat/completions`
- **Ollama-compatible** — `POST /api/chat`, `POST /api/generate`, `POST /api/show`
- **Operational** — `GET /health`

## Configuration

All settings are driven by environment variables (`MODEL_NAME`, `MOONDREAM_MODE`, `MOONDREAM_API_KEY`, `MODEL_CACHE_DIR`, model download URLs). See `src/config.py` for the full list.

## Code exploration with octocode

Use [octocode](https://github.com/Muvon/octocode) CLI for codebase navigation and discovery:

```bash
# Index the codebase first (run once, or after major changes)
octocode index

# Semantic search — find code by meaning, not keywords
octocode search "image analysis pipeline"

# View file/function signatures without reading full files
octocode view src/vision_service.py

# Navigate imports, calls, and dependencies via knowledge graph
octocode graphrag overview
octocode graphrag get-relationships --node-id "src/routes.py"

# Search commit history
octocode search "add ollama endpoints" --mode commits

# Structural search with AST patterns
octocode grep "def analyze_image($$$)"
```

When working with this codebase, run `octocode index` first, then use `octocode search`, `octocode view`, and `octocode graphrag` to navigate the codebase before reading files in full.

## Configuration

### Type checker (basedpyright)

Zed uses basedpyright for type checking. Configuration is in `basedpyrightconfig.json`:
- Points to `.venv` for package resolution
- `typeCheckingMode: "standard"` — catches real issues
- Noisy diagnostics (`reportUnknown*`, `reportAny`, `reportAttributeAccessIssue`) are disabled — they cascade from third-party packages without stubs

If you see import resolution errors, make sure `uv sync` has completed successfully (Python 3.13).

## Code conventions

- Secrets and tuneable values come from env — never hardcode them.
- Run linter manually before pushing (no pre-commit hooks).

## Quality gate

Before any commit or PR:

- Zero linter errors (`uv run ruff check .`)
- Zero formatting issues (`uv run ruff format .`)
- All tests pass
- Docker image builds successfully (`docker compose up -d --build`)

No exceptions. If any check fails, fix it before proceeding.

## Contributing

1. Branch off `master`, make changes.
2. Run `ruff check .` and `ruff format .`.
3. Test with `docker compose up -d --build` or local `uv run fastapi run`.
4. Open a PR — CI builds the Docker image.
