FROM python:3.13-slim

# Required by the official MCP Registry to verify image ownership
LABEL io.modelcontextprotocol.server.name="io.github.typedb/typedb-mcp"

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY *.py ./

# --no-dev keeps test tooling out of the image
RUN pip install --no-cache-dir uv && \
    uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8001

USER nobody

# 0.0.0.0 is only the container bind (needed for the published port); the CLI default is 127.0.0.1.
# Arguments from `docker run` / compose `command:` are appended; a later --host wins.
ENTRYPOINT ["python", "server.py", "--host", "0.0.0.0"]
