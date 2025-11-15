FROM ghcr.io/astral-sh/uv:0.7.20-python3.13-alpine@sha256:66fc613d6880444f8593aa0a158716448e7ed6f0dc7965383d10f6b8e51d5769

ENV PYTHONUNBUFFERED=1

WORKDIR /github/workspace 


COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN apk add --no-cache git \
    && uv build \
    && uv pip install --system dist/*.whl

ENTRYPOINT ["auto-semver"]
