# PIZDo — Markdown to PDF (Typst). Python 3.12 + pandoc + typst.
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    xz-utils \
    gzip \
    && rm -rf /var/lib/apt/lists/*

# Install Pandoc from upstream (Debian's pandoc is too old and lacks typst output)
# Pandoc 3.9 — точная версия, совпадает с pandoc-wasm 1.0.1 (docs/sprint/VERSIONS.md)
ARG PANDOC_VERSION=3.9
RUN curl -sSL "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-linux-amd64.tar.gz" \
    | tar -xzf - -C /tmp \
    && mv /tmp/pandoc-${PANDOC_VERSION}/bin/pandoc /usr/local/bin/ \
    && rm -rf /tmp/pandoc-${PANDOC_VERSION}

# Install Typst CLI (official Linux x64 binary)
# Typst 0.14.2 — точная версия, совпадает с компилятором typst.ts (docs/sprint/VERSIONS.md)
ARG TYPST_VERSION=0.14.2
RUN curl -sSL "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-x86_64-unknown-linux-musl.tar.xz" \
    | tar -xJ -C /tmp \
    && mv /tmp/typst-x86_64-unknown-linux-musl/typst /usr/local/bin/ \
    && chmod +x /usr/local/bin/typst \
    && rm -rf /tmp/typst-x86_64-unknown-linux-musl

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY assets/fonts/ ./assets/fonts/
COPY alembic/ ./alembic/
COPY alembic.ini .

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
