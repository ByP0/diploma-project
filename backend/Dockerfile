FROM python:3.11-slim AS base

ARG HTTP_PROXY=
ARG HTTPS_PROXY=
ARG NO_PROXY=

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app


FROM base AS deps

ARG HTTP_PROXY=
ARG HTTPS_PROXY=
ARG NO_PROXY=
ARG PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=
ARG PIP_PROXY=

COPY requirements.txt ./requirements.txt

RUN HTTP_PROXY="${HTTP_PROXY}" \
    HTTPS_PROXY="${HTTPS_PROXY}" \
    NO_PROXY="${NO_PROXY}" \
    PIP_INDEX_URL="${PIP_INDEX_URL}" \
    PIP_TRUSTED_HOST="${PIP_TRUSTED_HOST}" \
    PIP_PROXY="${PIP_PROXY}" \
    python -m pip install --no-cache-dir -r requirements.txt


FROM deps AS runtime

COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts

EXPOSE 8080

CMD ["python", "scripts/start_backend.py"]
