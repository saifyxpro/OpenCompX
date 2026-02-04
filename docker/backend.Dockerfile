# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# gcc and python3-dev are often needed for compiling python packages
# docker.io is needed if the backend spawns sibling containers
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI (for sibling container orchestration)
RUN curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
