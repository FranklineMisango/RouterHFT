FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    bird2 \
    traceroute \
    iputils-ping \
    tcpdump \
    net-tools \
    iproute2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/
COPY configs/ ./configs/

# Create data directory
RUN mkdir -p /app/data

# Set environment variables
ENV PYTHONPATH=/app
ENV HFT_DATA_DIR=/app/data
ENV HFT_CONFIG_DIR=/app/configs

# Create non-root user
RUN useradd -m -u 1000 hft && chown -R hft:hft /app
USER hft

# Expose ports for monitoring and APIs
EXPOSE 8080 8081

# Default command
CMD ["python", "-m", "src.main"]
