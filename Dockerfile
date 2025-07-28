FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY . .

# Set permissions
RUN chmod +x *.py

# Expose port (using 5002 to match your current setup)
EXPOSE 5002

# Use gunicorn for production
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5002", "main:app"] 