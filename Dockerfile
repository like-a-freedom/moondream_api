FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

# Cloud-only build — skip kestrel (the Photon engine) and its CUDA/PyTorch
# baggage (~2 GB). Moondream's CloudVL only needs Pillow at runtime.
COPY pyproject.toml uv.lock ./

# Install moondream WITHOUT its kestrel dependency (--no-deps).
# Then install the remaining runtime deps. kestrel is only needed for
# local Photon inference (see Dockerfile.nvidia).
RUN --mount=type=cache,target=/root/.cache/uv \
    uv venv && \
    uv pip install moondream --no-deps && \
    uv pip install pillow fastapi[standard] httpx psutil

# Copy the rest of the application
COPY . /app

# Install the project itself (uses the existing .venv, no deps resolved)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e . --no-deps

FROM python:3.13-slim-bookworm

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

RUN useradd -m appuser && chown -R appuser:appuser /app

USER appuser
CMD ["uv", "run", "fastapi", "run", "./src/api.py", "--host", "0.0.0.0", "--port", "8000"]
