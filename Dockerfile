# Stage 1: build React Mini App
FROM node:20-alpine AS webapp-build
WORKDIR /webapp
COPY webapp/package*.json ./
RUN npm install
COPY webapp/ ./
RUN npm run build

# Stage 2: Python bot
FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ ./bot/

# Copy built React app into expected location
COPY --from=webapp-build /webapp/dist ./webapp/dist

WORKDIR /app/bot
CMD ["python", "main.py"]
