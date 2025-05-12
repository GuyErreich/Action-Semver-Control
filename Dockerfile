FROM python:3.12-slim

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Set working directory
WORKDIR /github/workspace

# TODO: test and remove python already handles it
# Mark /github/workspace as safe for git
# RUN git config --global --add safe.directory /github/workspace 

# Install Python dependencies (only your tool's!)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy only your source code
COPY src/ /app

# Set PYTHONPATH to include your source
ENV PYTHONPATH=/app

# Set default command
ENTRYPOINT ["python", "-m", "auto_semver.cli"]
