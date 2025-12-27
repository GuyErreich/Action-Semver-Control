FROM ghcr.io/astral-sh/uv:0.9.18-python3.13-alpine@sha256:adf77e722d04970edb8bafaa7e3e5b5aac2e097a9f624db3dd8010b6613fa304

ENV PYTHONUNBUFFERED=1

WORKDIR /github/workspace 


COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN apk add --no-cache git \
    && uv build \
    && uv pip install --system dist/*.whl

ENTRYPOINT ["auto-semver"]
