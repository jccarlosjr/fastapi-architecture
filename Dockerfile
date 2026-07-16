# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt /workspace/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /workspace/

# Expose port 8000
EXPOSE 8000

# Command to run migrations, seed permissions, and then start the application
CMD ["sh", "-c", "alembic upgrade head && python cli.py seed-permissions && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
