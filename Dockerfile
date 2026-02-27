FROM python:3.11-slim

WORKDIR /app

# System deps for exchangelib (lxml)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt1-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir -e .

# MCP server listens on 8000 internally
EXPOSE 8000

# Run as non-root
RUN useradd -m mcp
USER mcp

CMD ["email-mcp-server"]
