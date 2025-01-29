FROM --platform=$TARGETPLATFORM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    gcc \
    g++ \
    git \
    libprotobuf-dev \
    protobuf-compiler \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set build environment variables
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_PREFER_BINARY=1
ENV PIP_ONLY_BINARY=:all:
ENV MAKEFLAGS="-j1"
ENV CMAKE_BUILD_PARALLEL_LEVEL=1
ENV ONNX_ML=1
ENV ONNX_BUILD_TESTS=OFF
ENV CMAKE_ARGS="-DONNX_USE_PROTOBUF_SHARED_LIBS=OFF -DCMAKE_BUILD_TYPE=Release -DFETCHCONTENT_FULLY_DISCONNECTED=ON -Wno-dev"
ENV CFLAGS="-O2 -pipe"
ENV CXXFLAGS="-O2 -pipe"
ENV LDFLAGS="-Wl,--as-needed"

WORKDIR /app

# Copy only the files needed for dependency installation
COPY pyproject.toml uv.lock ./

# Install dependencies in two phases
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application
COPY . /app

# Then build remaining packages
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.13-slim-bookworm

COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/
COPY --from=builder --chown=app:app /app /app

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app
ENV MODEL_CACHE_DIR=/app/model_cache

RUN useradd -m appuser \
    && chown -R appuser:appuser /app

USER appuser
CMD ["uv", "run", "fastapi", "run", "./src/api.py", "--host", "0.0.0.0", "--port", "8000"]