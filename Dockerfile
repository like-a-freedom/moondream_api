FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    gcc \
    g++ \
    ninja-build \
    libopenblas-dev \
    liblapack-dev \
    python3-dev \
    protobuf-compiler \
    libprotoc-dev \
    libprotobuf-dev \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1
# Fix for ARM64 compilation issues
ARG TARGETARCH
ENV CMAKE_ARGS="-DONNX_USE_FULL_PROTOBUF=OFF"
ENV ONNX_USE_LITE_PROTO=ON

# Disable unsupported flags on ARM64
RUN if [ "$TARGETARCH" = "arm64" ]; then \
    echo "Using ARM64, adjusting compiler flags"; \
    export CXXFLAGS="-mcpu=generic"; \
    fi


WORKDIR /app

# Copy only the files needed for dependency installation
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    CXXFLAGS="$CXXFLAGS" uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application
COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    CXXFLAGS="$CXXFLAGS" uv sync --frozen --no-dev

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