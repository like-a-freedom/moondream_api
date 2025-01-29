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
ENV UV_LINK_MODE=copy
ENV DEBIAN_FRONTEND=noninteractive
ENV CMAKE_BUILD_TYPE=Release
ENV CMAKE_ARGS="-DONNX_WERROR=OFF -DONNX_USE_PROTOBUF_SHARED_LIBS=ON -DCMAKE_POSITION_INDEPENDENT_CODE=ON -DCMAKE_POLICY_DEFAULT_CMP0148=NEW"
# Compiler settings
ENV CC=gcc
ENV CXX=g++
ENV CFLAGS="-fPIC -march=native"
ENV CXXFLAGS="-fPIC -march=native"
ENV ONNX_ML=1
# Explicitly disable SSE and AES instructions
# ENV CFLAGS="${CFLAGS} -mno-sse2 -mno-sse3 -mno-ssse3 -mno-sse4.1 -mno-sse4.2 -mno-aes"
# ENV CXXFLAGS="${CXXFLAGS} -mno-sse2 -mno-sse3 -mno-ssse3 -mno-sse4.1 -mno-sse4.2 -mno-aes"

# ENV CFLAGS="-march=armv8-a+crc -mtune=cortex-a72"
# ENV CXXFLAGS="-march=armv8-a+crc -mtune=cortex-a72"
# Disable x86 specific optimizations
# ENV CPPFLAGS="-DCPUINFO_ARCH_ARM64"


WORKDIR /app

# Copy only the files needed for dependency installation
COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copy the rest of the application
COPY . /app

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