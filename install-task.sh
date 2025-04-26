#!/usr/bin/env bash

set -euo pipefail

# Configurable version
TASK_VERSION="3.33.1"

# Determine OS and ARCH
OS=$(uname | tr '[:upper:]' '[:lower:]')
ARCH=$(uname -m)

# Normalize architecture names
case "$ARCH" in
  x86_64) ARCH="amd64" ;;
  arm64|aarch64) ARCH="arm64" ;;
  *) echo "Unsupported architecture: $ARCH" && exit 1 ;;
esac

# Construct download URL
TAR_NAME="task_${OS}_${ARCH}.tar.gz"
URL="https://github.com/go-task/task/releases/download/v${TASK_VERSION}/${TAR_NAME}"

# Download and install
echo "Installing Task v${TASK_VERSION} for ${OS}/${ARCH}"
curl -sSL "$URL" -o "$TAR_NAME"
tar -xzf "$TAR_NAME" task
chmod +x task
sudo mv task /usr/local/bin/task

# Cleanup
rm "$TAR_NAME"

echo "✅ Task installed at: $(which task)"
echo "📦 Version: $(task --version)"
