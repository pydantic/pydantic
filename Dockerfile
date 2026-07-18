FROM python:3.13-slim

# System deps for Rust + uv
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl build-essential git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# Rust stable (matches CI: dtolnay/rust-toolchain stable)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
ENV PATH="/root/.cargo/bin:${PATH}"

# uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /workspace

# Clone and pin
RUN git clone https://github.com/pydantic/pydantic.git . && \
    git checkout cf67d4b3193c3fe43ede18612ed62785eee11382

# Apply patches
COPY solution.patch tests.patch ./
RUN git apply solution.patch && git apply tests.patch

# Install Python deps (network available at build time)
RUN uv sync --all-packages --group testing-extra

# Compile local Rust extension at IMAGE BUILD TIME (network available)
RUN cd pydantic-core && uv run maturin develop --uv

# Copy test script
COPY test.sh /test.sh
RUN chmod +x /test.sh

CMD ["/test.sh"]
