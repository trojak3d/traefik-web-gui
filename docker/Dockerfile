FROM python:3.11-alpine

# Install system dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    curl \
    tini \
    python3-dev \
    yaml-dev

# Create traefik user and group (match production)
RUN addgroup -S traefik && adduser -S traefik -G traefik

# Set working directory
WORKDIR /app

# Copy requirements
COPY app/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY app/app.py .
COPY app/templates templates/

# Create config directory (simulates /etc/traefik/dynamic)
RUN mkdir -p /etc/traefik/dynamic && \
    chown -R traefik:traefik /etc/traefik/dynamic && \
    chmod 755 /etc/traefik/dynamic

# Create data directory and set ownership before switching user
RUN mkdir -p /var/lib/traefik-web-gui && \
    chown traefik:traefik /var/lib/traefik-web-gui && \
    chmod 700 /var/lib/traefik-web-gui

# Create log directory
RUN mkdir -p /var/log && \
    chown traefik:traefik /var/log

# Change to traefik user
USER traefik

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/ || exit 1

# Use tini as init system to handle signals properly
ENTRYPOINT ["/sbin/tini", "--"]

# Start the application
CMD ["python3", "app.py"]
