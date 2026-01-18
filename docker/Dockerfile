# CodeTruth-MCP Docker Image
# Multi-stage build for minimal image size

FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for JS/TS analysis
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Install analysis tools
RUN pip install --no-cache-dir \
    semgrep \
    ruff \
    mypy \
    pip-audit

# Install Node.js tools
RUN npm install -g \
    eslint \
    typescript \
    @typescript-eslint/parser \
    @typescript-eslint/eslint-plugin

# Production image
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js runtime
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Copy from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/lib/node_modules /usr/lib/node_modules
COPY --from=builder /app/src /app/src

# Create non-root user
RUN useradd -m -u 1000 codetruth
USER codetruth

# Set up data directory
RUN mkdir -p /home/codetruth/.codetruth

ENV CODETRUTH_DB_PATH=/home/codetruth/.codetruth/evidence.db

ENTRYPOINT ["codetruth"]
CMD ["serve"]
