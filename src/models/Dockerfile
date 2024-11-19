FROM python:3.11-slim

# Ensure bash is available
RUN apt-get update && apt-get install -y bash

ENV PYENV_SHELL=/bin/bash

# Install essential tools and Playwright dependencies
RUN set -ex; \
    apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
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
    pip install --no-cache-dir --upgrade pip && \
    pip install pipenv && \
    mkdir -p /app

# Set working directory
WORKDIR /app

# Copy Pipfile and Pipfile.lock for dependency management
ADD Pipfile Pipfile.lock /app/

# Install the Python dependencies using Pipenv
RUN pipenv sync

# Install the Playwright browsers
RUN pipenv run playwright install --with-deps

# Add the rest of the application files
ADD . /app

# Ensure pipenv shell is not required to run scripts
RUN pipenv install --deploy --system

# Install PyTorch
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Set entrypoint to open bash by default
CMD ["/bin/bash"]