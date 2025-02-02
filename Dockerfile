FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Install comprehensive build dependencies
RUN apt-get update 
RUN apt-get install -y \
    # build-essential \
    cmake \
    gcc \
    autoconf \
    automake \
    g++ \
    git \
    python3-dev \
    libabsl-dev
# protobuf-compiler \
# libprotobuf-dev

# RUN apt-get autoclean
ENV CFLAGS=-O0
ENV CXXFLAGS=-O0
ENV CC=/usr/bin/clang
ENV CXX=/usr/bin/clang++
ENV ULIMIT_STACK=1048576

#29.3
#5.29.3
ARG PROTOBUF_VERSION=22.3
RUN git clone --branch v${PROTOBUF_VERSION} --recurse-submodules https://github.com/protocolbuffers/protobuf && \
    cd protobuf && \
    cmake -Dprotobuf_BUILD_TESTS=OFF \
    -Dprotobuf_BUILD_SHARED_LIBS=ON \
    -B build && \
    cmake --build build --parallel $(nproc) && \
    cmake --install build

RUN git clone https://github.com/pybind/pybind11.git \
    && cd pybind11 \
    && git checkout v2.13.6 \
    && mkdir build \
    && cd build \
    && cmake -DCMAKE_BUILD_TYPE=Release \
    -DPYBIND11_PYTHON_VERSION=3.13 \
    -DPYBIND11_TEST=OFF \
    -DPython_EXECUTABLE=$(which python3) \
    -DPython_INCLUDE_DIRS=/usr/local/include/python3.13 \
    -DPython_LIBRARIES=/usr/local/lib/libpython3.13.so \
    .. \
    && make -j1 install \
    && cd / \
    && rm -rf /pybind11 \
    && pip install pybind11

RUN ldconfig
ENV LD_LIBRARY_PATH=/usr/local/lib

# Set comprehensive build environment variables
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV DEBIAN_FRONTEND=noninteractive

# Compiler and build flags for position-independent code
# ENV MAKEFLAGS="-j1"
# ENV CMAKE_BUILD_PARALLEL_LEVEL=1

# # Set architecture-specific compiler flags
# ARG TARGETARCH
# RUN if [ "$TARGETARCH" = "amd64" ]; then \
#     export CFLAGS="-O3 -pipe -fPIC -Wall -mno-sse2 -mno-sse3 -mno-ssse3 -mno-sse4.1 -mno-sse4.2 -mno-aes"; \
#     export CXXFLAGS="-O3 -pipe -fPIC -Wall -mno-sse2 -mno-sse3 -mno-ssse3 -mno-sse4.1 -mno-sse4.2 -mno-aes"; \
#     else \
#     export CFLAGS="-O3 -pipe -fPIC -Wall"; \
#     export CXXFLAGS="-O3 -pipe -fPIC -Wall"; \
#     fi

# # Comprehensive CMake configuration
# ENV CMAKE_ARGS="-DCMAKE_POSITION_INDEPENDET_CODE=ON \
#     -DONNX_USE_PROTOBUF_SHARED_LIBS=ON \
#     -DONNX_USE_LITE_PROTO=OFF \
#     -DCMAKE_BUILD_TYPE=Release \
#     -DFETCHCONTENT_FULLY_DISCONNECTED=ON \
#     # -DCMAKE_MODULE_PATH=/usr/local/cmake/Modules \
#     # -Dprotobuf_BUILD_PROTOBUF_BINARIES=ON \
#     # -Dprotobuf_BUILD_PROTOC_BINARIES=ON \
#     # -DProtobuf_PROTOC_EXECUTABLE=/usr/bin/protoc \
#     # -DProtobuf_INCLUDE_DIR=/usr/include/google/protobuf \
#     # # -DProtobuf_LIBRARY=/usr/lib/aarch64-linux-gnu/libprotobuf.so \
#     # -DPYTHON_INCLUDE_DIR=/usr/include/python3.13 \
#     # -DPYTHON_EXECUTABLE=/usr/local/bin/python3.13 \
#     -Wno-dev"

# ENV CMAKE_ARGS='-DCMAKE INSTALL_PREFIX=/usr/local -DCMAKE_INSTALL_RPATH="/usr/local/lib:/usr/lib:/usr/local/lib"'

# # Additional environment variables for ONNX build
# ENV ONNX_ML=1
# ENV ONNX_BUILD_TESTS=OFF

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
