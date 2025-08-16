# Use official Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables to prevent Python from writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies needed for building Python packages (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to leverage Docker cache
COPY requirements.txt .

# Upgrade pip and install dependencies without cache
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy all source code
COPY . .

# Expose port if you run a web server (optional)
# EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"]
