FROM python:3.12.12-slim-bookworm AS python-base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONDEFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=2.2.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache \
    PYSETUP_PATH="/app" \
    VENV_PATH="/app/.venv"
ENV PATH="$VENV_PATH/bin:$PATH"

FROM python-base AS builder

# Update system packages to reduce vulnerabilities
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir pip==25.2 \
    && pip install --no-cache-dir "poetry==$POETRY_VERSION"

WORKDIR $PYSETUP_PATH

# Install dependencies and remove caches
COPY pyproject.toml $PYSETUP_PATH
COPY poetry.lock $PYSETUP_PATH
RUN poetry install --no-root && rm -rf "$POETRY_CACHE_DIR"

FROM python-base AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && apt-get upgrade -y \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -g 1234 customgroup \
    && useradd -m -u 1234 -g customgroup customuser \
    && mkdir /src && chown -hR customuser /src

USER customuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv/

ENV PATH="/app/.venv/bin:$PATH"

COPY src /app

EXPOSE 8000/tcp

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 CMD [ "curl", "-f", "http://localhost:8000/healths"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
