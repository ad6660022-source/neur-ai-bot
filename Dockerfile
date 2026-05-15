# Dockerfile for NEUR AI Telegram Bot

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot source
COPY bot/ ./bot/

# Set working directory to bot
WORKDIR /app/bot

# Run the bot
CMD ["python", "main.py"]
