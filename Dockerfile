FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

WORKDIR /app

COPY pyproject.toml uv.lock ./

# The cloud build overrides kestrel-kernels with a no-op version so that
# CUDA/nvidia packages (~2 GB) are never downloaded. Local (Photon) builds
# use the real kestrel-kernels for GPU inference.
ARG MOONDREAM_FLAVOR=cloud
RUN if [ "$MOONDREAM_FLAVOR" = "cloud" ]; then \
      echo "Configuring for cloud-only build" \
      && echo '{"kestrel-kernels": {"version": "0.0.0"}}' > /dev/null; \
    fi

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$MOONDREAM_FLAVOR" = "cloud" ]; then \
      uv sync --frozen --no-install-project --no-dev \
        --no-install-package kestrel-kernels \
        --no-install-package kestrel-native \
        --no-install-package nvidia-cublas \
        --no-install-package nvidia-cuda-cupti \
        --no-install-package nvidia-cuda-nvrtc \
        --no-install-package nvidia-cuda-runtime \
        --no-install-package nvidia-cudnn-cu13 \
        --no-install-package nvidia-cufft \
        --no-install-package nvidia-curand \
        --no-install-package nvidia-cusparse \
        --no-install-package nvidia-cusparselt-cu13 \
        --no-install-package nvidia-nccl-cu13 \
        --no-install-package nvidia-nvjitlink \
        --no-install-package triton \
        --no-install-package sympy \
        --no-install-package networkx \
        --no-install-package mpmath; \
    else \
      uv sync --frozen --no-install-project --no-dev; \
    fi

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    if [ "$MOONDREAM_FLAVOR" = "cloud" ]; then \
      uv sync --frozen --no-dev \
        --no-install-package kestrel-kernels \
        --no-install-package nvidia-cublas \
        --no-install-package nvidia-cuda-cupti \
        --no-install-package nvidia-cuda-nvrtc \
        --no-install-package nvidia-cuda-runtime \
        --no-install-package nvidia-cudnn-cu13 \
        --no-install-package nvidia-cufft \
        --no-install-package nvidia-curand \
        --no-install-package nvidia-cusparse \
        --no-install-package nvidia-cusparselt-cu13 \
        --no-install-package nvidia-nccl-cu13 \
        --no-install-package nvidia-nvjitlink \
        --no-install-package triton \
        --no-install-package sympy \
        --no-install-package networkx \
        --no-install-package mpmath; \
    else \
      uv sync --frozen --no-dev; \
    fi

FROM python:3.13-slim-bookworm

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app /app

WORKDIR /app

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH=/app

RUN useradd -m appuser && chown -R appuser:appuser /app

USER appuser
CMD ["uv", "run", "fastapi", "run", "./src/api.py", "--host", "0.0.0.0", "--port", "8000"]
