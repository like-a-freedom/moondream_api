# Moondream API Service

OpenAI- and Ollama-compatible REST API for [Moondream](https://moondream.ai) — a fast vision-language model. Designed for home-automation setups (Home Assistant + Frigate) to describe camera shots in human-readable language.

## Architecture

The service wraps the **Moondream Python SDK** (v1.3+) in a FastAPI application, exposing:

- **OpenAI-compatible** — `POST /v1/chat/completions`
- **Ollama-compatible** — `POST /api/chat`, `POST /api/generate`, `POST /api/show`

Moondream runs in one of two modes:

| Mode | Description | Requirements |
|---|---|---|
| **Cloud API** (default) | Inference on Moondream's servers | API key (free tier available) |
| **Local Photon** | Local inference via Photon engine | API key + Apple Silicon (macOS 13+) or NVIDIA GPU (Linux/Windows) |

No model files to download. No GPU required for cloud mode.

## Quick Start

### Prerequisites

- Docker (or Python 3.13+ with `uv`)
- [Moondream API key](https://moondream.ai/c/cloud/api-keys)

### Docker — cloud (default, lightweight)

```bash
export MOONDREAM_API_KEY="your-api-key"
docker compose up -d
```

Service available at `http://localhost:18000`. Fast build, no GPU required.

### Docker — local inference (NVIDIA GPU / Photon)

```bash
export MOONDREAM_API_KEY="your-api-key"
docker compose --profile local up -d
```

Service available at `http://localhost:18001`. Requires NVIDIA GPU with CUDA 12. Build is slower (~20 min) — it downloads CUDA runtime + PyTorch.

### Docker profiles

The project provides two Docker Compose profiles:

| Profile | Build | Image size | Use case |
|---|---|---|---|
| `cloud` (default) | `Dockerfile` | ~200 MB | Cloud API (no GPU) |
| `local` | `Dockerfile.nvidia` + `nvidia/cuda` base | ~5 GB | Local Photon (NVIDIA GPU) |

The cloud profile strips CUDA packages after installation, keeping the image lean.

### Build locally

```bash
# Build cloud image and tag
MOONDREAM_API_KEY=test docker compose build moondream-api
MOONDREAM_API_KEY=test docker tag ghcr.io/like-a-freedom/moondream_api:cloud moondream-api:$(git rev-parse --short HEAD)

# Build NVIDIA variant
MOONDREAM_API_KEY=test docker compose --profile local build
```

### Local (Python 3.13+)

```bash
git clone https://github.com/like-a-freedom/moondream_api
cd moondream_api

# Install dependencies
uv sync

# Run
MOONDREAM_API_KEY="your-api-key" uv run fastapi run ./src/api.py --host 0.0.0.0 --port 8000
```

## Configuration

All settings are driven by environment variables:

| Variable | Default | Description |
|---|---|---|
| `MOONDREAM_API_KEY` | `""` | **Required.** Moondream API key |
| `MOONDREAM_MODE` | `"api"` | `"api"` for cloud, `"local"` for Photon |
| `MODEL_NAME` | `"moondream3.1-9B-A2B"` | Model to use (`moondream3.1-9B-A2B`, `moondream3-preview`, or a finetune) |
| `HTTP_PROXY` | `""` | HTTP proxy for outbound requests (image fetching, cloud API) |
| `HTTPS_PROXY` | `""` | HTTPS proxy for outbound requests |
| `ALL_PROXY` | `""` | Fallback proxy for all protocols |
| `NO_PROXY` | `""` | Comma-separated list of hosts to bypass proxy |

### Proxy Configuration

The service supports outbound HTTP/HTTPS proxies. Set standard environment variables:

```bash
# Docker — all traffic through a proxy
export HTTPS_PROXY="http://proxy.example.com:8080"
docker compose up -d

# Or with ALL_PROXY as a catch-all
export ALL_PROXY="socks5://proxy.example.com:1080"
docker compose up -d

# Exclude specific hosts from proxy
export NO_PROXY="localhost,127.0.0.1,10.0.0.0/8"
```

For local Python runs, set the same variables in your shell:

```bash
HTTPS_PROXY="http://proxy.example.com:8080" \
MOONDREAM_API_KEY="your-key" \
uv run fastapi run ./src/api.py --host 0.0.0.0 --port 8000
```

**What goes through the proxy:**
- Image fetching from HTTP/HTTPS URLs (`httpx`)
- Moondream Cloud API calls (`urllib.request` — respects env vars natively)

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/chat/completions` | OpenAI-compatible chat with image support |
| `POST` | `/api/chat` | Ollama-compatible chat |
| `POST` | `/api/generate` | Ollama-compatible generate |
| `POST` | `/api/show` | Ollama model info |
| `GET` | `/health` | Service health check |

Interactive docs: [`http://localhost:18000/docs`](http://localhost:18000/docs) (Swagger) or [`http://localhost:18000/redoc`](http://localhost:18000/redoc) (ReDoc).

### Examples

**OpenAI-compatible — describe an image:**

```bash
curl http://localhost:18000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "moondream3.1-9B-A2B",
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "What do you see in this image?"},
          {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
      }
    ]
  }'
```

**Streaming (SSE) — set `"stream": true`:**

```bash
curl -N http://localhost:18000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "moondream3.1-9B-A2B",
    "stream": true,
    "messages": [
      {
        "role": "user",
        "content": [
          {"type": "text", "text": "Describe this image"},
          {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,..."}}
        ]
      }
    ]
  }'
```

**Ollama-compatible:**

```bash
curl http://localhost:18000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "model": "moondream3.1-9B-A2B",
    "messages": [
      {"role": "user", "content": "Describe this", "images": ["<base64>"]}
    ]
  }'
```

## Image Input Formats

The service accepts images in three formats:

1. **HTTP/HTTPS URLs** — fetched server-side
2. **Data URIs** — `data:image/jpeg;base64,...`
3. **Raw base64** — plain base64-encoded bytes

## Development

### Prerequisites

- Python 3.13+ (local dev)
- `uv` package manager

### Setup

```bash
uv sync                  # install dependencies + dev dependencies
uv run pytest            # run tests with coverage
uv run ruff check .      # lint
uv run ruff format .     # format
```

### Test Suite

```bash
# Run all tests with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/test_routes.py -v
```

Test structure:

| File | Tests |
|---|---|
| `tests/test_api.py` | App entry point, metadata |
| `tests/test_api_lifespan.py` | Lifespan lifecycle |
| `tests/test_config.py` | Settings defaults |
| `tests/test_exceptions.py` | Exception hierarchy |
| `tests/test_routes.py` | All API endpoints, streaming |
| `tests/test_schemas.py` | Pydantic model validation |
| `tests/test_vision_service.py` | Image loading, analysis, token costing |

### Coverage Target

> **94%+** across the entire `src/` tree. No regressions allowed.

## Project Structure

```
src/
  api.py                — FastAPI app, lifespan, router mounting
  config.py             — Settings from environment variables
  exceptions.py         — VisionServiceError, ImageAnalysisError, ImageLoadError
  ollama_model_mocks.py — Static mock data for /api/show
  routes.py             — Route handlers, SSE streaming helpers
  schemas.py            — Pydantic request/response models
  vision_service.py     — Moondream client wrapper, image loading
```

## License

MIT. See [LICENSE](LICENSE).
