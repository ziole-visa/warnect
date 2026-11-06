FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl ca-certificates gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN cd warnect/bridge && npm ci --omit=dev --no-audit --no-fund
RUN pip install --no-cache-dir .

EXPOSE 8080
CMD ["warnect", "serve", "--host", "0.0.0.0", "--port", "8080"]
