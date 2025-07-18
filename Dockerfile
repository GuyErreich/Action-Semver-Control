FROM ghcr.io/astral-sh/uv:0.7.20-python3.13-alpine@sha256:66fc613d6880444f8593aa0a158716448e7ed6f0dc7965383d10f6b8e51d5769

ENV WORKDIR=/github/workspace \
    PYTHONUNBUFFERED=1

RUN apk add --no-cache git \
 && addgroup -S appgroup \
 && adduser -S appuser -G appgroup \
 && mkdir -p ${WORKDIR} \
 && chown -R appuser:appgroup ${WORKDIR}

WORKDIR ${WORKDIR}

COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

RUN uv build \
 && uv pip install --system dist/*.whl \
 && chown -R appuser:appgroup ${WORKDIR}

USER appuser

ENTRYPOINT ["auto-semver"]
