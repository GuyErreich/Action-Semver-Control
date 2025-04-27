FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y git && apt-get clean

# Set working directory
WORKDIR /github/workspace

# Mark /github/workspace as safe for git
RUN git config --global --add safe.directory /github/workspace

# Copy only necessary files
COPY pyproject.toml requirements.txt ./
COPY auto_semver_config.yml ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set default command
ENTRYPOINT ["python", "-m", "src.main"]
