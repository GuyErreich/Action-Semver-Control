# Keep the image tag in sync with .uv-version (CI installs the same uv via setup-uv).
FROM ghcr.io/astral-sh/uv:0.12.23-python3.13-alpine@sha256:50171185972b4532b34f433d8af999fc42cffd6c3274f0ca294a9da90557aadc

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
