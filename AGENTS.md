# AGENTS.md — moondream_api

## Project overview

REST API that runs the [Moondream](https://github.com/vikhyat/moondream) vision-language model locally or via Moondream Cloud. Exposes OpenAI- and Ollama-compatible endpoints so that existing integrations (Home Assistant, Frigate, etc.) can use it as a drop-in vision service.

Designed for edge hardware (Raspberry Pi, Orange Pi) and home-automation setups where camera frames need human-readable descriptions.

Single FastAPI application — no frontend, database, or microservice split.

## Tech stack

Python 3.13 · FastAPI · [uv](https://docs.astral.sh/uv/) · Docker (multi-stage, profiles) · GitHub Actions CI/CD · Ruff for linting · [ty](https://github.com/astral-sh/ty) for type checking

## Getting started

### Local (Python 3.13)

```bash
uv sync
uv run fastapi run ./src/api.py --host 0.0.0.0 --port 8000
```

### Docker — cloud (default, lightweight)

```bash
docker compose up -d
```

Service available at `localhost:18000`. Build is arm64-native on Apple Silicon.

### Docker — local inference (NVIDIA GPU / Photon)

```bash
docker compose --profile local up -d
```

Service available at `localhost:18001`. Requires NVIDIA GPU with CUDA 12.

## Docker build profiles

| Profile | Dockerfile | Base image | Size | Use case |
|---|---|---|---|---|
| `cloud` (default) | `Dockerfile` | `python:3.13-slim` | ~200 MB | Cloud API (no GPU) |
| `local` | `Dockerfile.nvidia` | `nvidia/cuda:12.8-runtime` | ~5 GB | Local Photon (NVIDIA GPU) |

The cloud image strips CUDA/PyTorch packages after install, keeping it lean for edge devices.

```bash
# Build and tag
MOONDREAM_API_KEY=your-key docker compose up -d --build

# NVIDIA variant
docker compose --profile local up -d --build
```

## Key commands

| Action | Command |
|---|---|
| Install deps | `uv sync` |
| Run locally | `uv run fastapi run ./src/api.py --host 0.0.0.0 --port 8000` |
| Run via Docker | `docker compose up -d` |
| Build cloud image | `docker compose up -d --build` |
| Build local (NVIDIA) image | `docker compose --profile local up -d --build` |
| Lint | `uv run ruff check .` |
| Format | `uv run ruff format .` |
| Type check | `uv run ty check src/` |

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
- `tests/test_routes.py` — HTTP endpoints (OpenAI, Ollama, health)
- `tests/test_schemas.py` — Pydantic model construction/validation
- `tests/test_vision_service.py` — image loading, analysis, token costing

Interactive docs also available:
- Swagger UI: `http://localhost:18000/docs`
- ReDoc: `http://localhost:18000/redoc`

## API surface

The service exposes three groups of endpoints:

- **OpenAI-compatible** — `POST /v1/chat/completions`
- **Ollama-compatible** — `POST /api/chat`, `POST /api/generate`, `POST /api/show`
- **Operational** — `GET /health`

## Configuration

All settings are driven by environment variables (`MODEL_NAME`, `MOONDREAM_MODE`, `MOONDREAM_API_KEY`). See `src/config.py` for the full list.

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

### Type checker (ty)

This project uses **[ty](https://github.com/astral-sh/ty)** for type checking — an extremely fast Python type checker written in Rust. Configuration is minimal: `ty` discovers `pyproject.toml` and `.venv` automatically, no config file needed.

```bash
# Run type checking
uv run ty check src/
```

**If you see import resolution errors:** make sure `uv sync` has completed successfully on Python 3.13 (`.python-version`).

**Understanding diagnostics:**

| Source | What it checks | How to run |
|---|---|---|
| **ruff** | Code style, formatting, import sorting | `uv run ruff check .` |
| **ty** | Type safety, None guards, attribute access | `uv run ty check src/` |

The quality gate targets **both** — zero ruff errors AND zero ty errors is mandatory.

**Common `ty` patterns in this codebase:**

```python
# ❌ Avoid — dict without type parameters triggers error
kws: dict = {"key": value}

# ✅ Always specify type arguments
kws: dict[str, Any] = {"key": value}

# ❌ Avoid — direct access on TypedDict may raise runtime error
result["answer"]

# ✅ Use .get() with default
result.get("answer", "")

# ❌ Avoid — calling .startswith() on object | None
raw = part.get("key")
if raw and raw.startswith("http"):

# ✅ Narrow the type with isinstance first
raw = part.get("key")
if isinstance(raw, str) and raw.startswith("http"):
```

## Code conventions

- Secrets and tuneable values come from env — never hardcode them.
- Run linter manually before pushing (no pre-commit hooks).

## Quality gate

Before any commit or PR:

- Zero linter errors (`uv run ruff check .`)
- Zero formatting issues (`uv run ruff format .`)
- Zero type errors (`uv run ty check src/`)
- All tests pass
- Cloud Docker image builds successfully (`docker compose up -d --build`)

No exceptions. If any check fails, fix it before proceeding.

## Contributing

1. Branch off `master`, make changes.
2. Run `ruff check .` and `ruff format .`.
3. Test with `docker compose up -d --build` or local `uv run fastapi run`.
4. Open a PR — CI builds the Docker image.
