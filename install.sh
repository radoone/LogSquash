#!/bin/bash

# LogSquash Installer for Gemini CLI

set -e

EXTENSION_DIR="$HOME/.gemini/extensions/logsquash"
REPO_URL="https://github.com/radoone/LogSquash.git"

echo "🪵 LogSquash: Installing extension..."

# Create extensions directory if it doesn't exist
mkdir -p "$HOME/.gemini/extensions"

# Clone or update the repository
if [ -d "$EXTENSION_DIR" ]; then
    echo "Updating existing installation..."
    cd "$EXTENSION_DIR"
    git pull
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$EXTENSION_DIR"
    cd "$EXTENSION_DIR"
fi

# Install dependencies and build
echo "Building LogSquash..."
npm install
npm run build

echo "✅ LogSquash installed successfully!"
echo "Restart your Gemini CLI session to activate the new tools."
