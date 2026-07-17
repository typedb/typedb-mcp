FROM python:3.11-slim

# Required by the official MCP Registry to verify image ownership
LABEL io.modelcontextprotocol.server.name="io.github.typedb/typedb-mcp"

WORKDIR /app

COPY pyproject.toml uv.lock ./
COPY *.py ./

RUN pip install --no-cache-dir uv && \
    uv sync --frozen

EXPOSE 8001

ENTRYPOINT ["uv", "run", "python", "server.py"]
