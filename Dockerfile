FROM ghcr.io/astral-sh/uv:0.9.18-python3.13-alpine@sha256:adf77e722d04970edb8bafaa7e3e5b5aac2e097a9f624db3dd8010b6613fa304

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV UV_FROZEN=1
ENV PATH="/opt/venv/bin:$PATH"

# Install outside /github/workspace so GHA's bind-mount cannot unhook the venv.
WORKDIR /src
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN apk add --no-cache git \
    && uv sync --no-dev --no-editable

WORKDIR /github/workspace

ENTRYPOINT ["auto-semver"]
