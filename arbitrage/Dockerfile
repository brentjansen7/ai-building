FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m arbitrage && chown -R arbitrage:arbitrage /app
USER arbitrage

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
