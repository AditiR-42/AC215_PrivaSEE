# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Install bash and essential tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    build-essential \
    curl \
    libnss3 \
    libxss1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libgbm-dev \
    libgtk-3-0 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install pipenv
RUN pip install --no-cache-dir --upgrade pip && \
    pip install pipenv

# Create application directory
WORKDIR /app

# Copy Pipfile and install dependencies
ADD Pipfile Pipfile.lock /app/
RUN pipenv sync

# Install Playwright browsers
RUN pipenv run playwright install --with-deps

# Copy the rest of the application code
ADD . /app

# Install system-wide dependencies to avoid using pipenv run
RUN pipenv install --deploy --system

# Set bash as the default command to keep the container alive
CMD ["/bin/bash"]