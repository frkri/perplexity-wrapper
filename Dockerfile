FROM ghcr.io/astral-sh/uv:0.11.25-python3.14-trixie-slim

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/app/.venv

COPY pyproject.toml ./

RUN uv sync --no-dev

COPY . ./

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]