# Filing Radar, hosted demo image (Cloud Run). One container: FastAPI under /api, the built screen at /.
# It serves the committed analysis cache (data/cache) and results/, so it needs no ITU databases and no network.
#
#   docker build -t filing-radar .
#   docker run --rm -p 8080:8080 filing-radar      # http://localhost:8080

# --- 1. build the screen --------------------------------------------------------------------------------
FROM node:22-bookworm-slim AS screen
WORKDIR /src
COPY design/ design/
COPY frontend/package.json frontend/package-lock.json frontend/
RUN cd frontend && npm ci --no-audit --no-fund
COPY frontend/ frontend/
RUN cd frontend && npm run build

# --- 2. API runtime -------------------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim
# git: py1546 is pinned to a commit of its GitHub repository (pyproject.toml)
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/ backend/
COPY prompts/ prompts/
COPY data/cache/ data/cache/
COPY data/reference/ data/reference/
COPY results/ results/
COPY scoring/ scoring/
COPY --from=screen /src/frontend/dist frontend/dist

ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app DEMO_MODE=1 LLM_DISABLED=1 PORT=8080
EXPOSE 8080
CMD ["sh", "-c", "exec uvicorn radar.serve:app --app-dir backend --host 0.0.0.0 --port ${PORT}"]
