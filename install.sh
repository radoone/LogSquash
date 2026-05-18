#!/bin/bash

# LogSquash Installer for Gemini CLI and Codex CLI

set -e

GEMINI_EXTENSION_DIR="$HOME/.gemini/extensions/logsquash"
CODEX_EXTENSION_DIR="$HOME/.codex/extensions/logsquash"
REPO_URL="https://github.com/radoone/LogSquash.git"

echo "🪵 LogSquash: Installing extension..."

# Create extensions directories if they don't exist
mkdir -p "$HOME/.gemini/extensions"
mkdir -p "$HOME/.codex/extensions"

# Clone or update the repository
if [ -d "$GEMINI_EXTENSION_DIR" ]; then
    echo "Updating existing installation in Gemini CLI..."
    cd "$GEMINI_EXTENSION_DIR"
    git pull
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$GEMINI_EXTENSION_DIR"
    cd "$GEMINI_EXTENSION_DIR"
fi

# Install dependencies and build
echo "Building LogSquash..."
npm install
npm run build

# Link to Codex CLI
if [ ! -d "$CODEX_EXTENSION_DIR" ]; then
    echo "Linking extension for Codex CLI..."
    ln -sf "$GEMINI_EXTENSION_DIR" "$CODEX_EXTENSION_DIR"
fi

echo "✅ LogSquash installed successfully!"
echo "Restart your Gemini CLI or Codex CLI session to activate the new tools."
