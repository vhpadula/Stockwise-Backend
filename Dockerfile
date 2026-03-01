# Use official Python image
FROM python:3.11-slim

# Prevent .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv
RUN pip install pipenv

# Copy Pipfile
COPY Pipfile Pipfile.lock /app/

# Install dependencies
RUN pipenv install --system --deploy

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# Run server
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${APP_INTERNAL_PORT}"]