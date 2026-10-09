# The uv tag is this action's build pin only. Consumer lockfiles are updated by
# the uv or npm already on the runner, not by the uv in this image.
FROM ghcr.io/astral-sh/uv:0.12.23-python3.13-alpine@sha256:50171185972b4532b34f433d8af999fc42cffd6c3274f0ca294a9da90557aadc

ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install outside /github/workspace so GHA's bind-mount cannot unhook the venv.
WORKDIR /src
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN apk add --no-cache git \
    && UV_FROZEN=1 uv sync --no-dev --no-editable

WORKDIR /github/workspace

ENTRYPOINT ["auto-semver"]
