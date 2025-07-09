FROM python:3.13-slim

# Install system dependencies including uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends git curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && curl -LsSf https://astral.sh/uv/install.sh | sh

# Add uv to PATH
ENV PATH="/root/.cargo/bin:$PATH"

# Set working directory
WORKDIR /github/workspace

# Copy Python project configuration
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync --frozen --no-dev

# Copy source code
COPY src/ /app

# Set PYTHONPATH to include your source
ENV PYTHONPATH=/app

# Set default command using uv run for proper environment
ENTRYPOINT ["uv", "run", "python", "-m", "auto_semver.cli"]
