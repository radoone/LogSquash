#!/bin/bash
# LogSquash Installer for Gemini CLI

set -e

EXTENSION_DIR="$HOME/.gemini/extensions/logsquash"
REPO_URL="https://github.com/radoone/LogSquash.git"

echo "🪵 LogSquash: Installing Gemini extension..."

mkdir -p "$HOME/.gemini/extensions"

if [ -d "$EXTENSION_DIR" ]; then
    echo "Updating existing installation in Gemini CLI..."
    cd "$EXTENSION_DIR"
    git pull
else
    echo "Cloning repository..."
    git clone "$REPO_URL" "$EXTENSION_DIR"
    cd "$EXTENSION_DIR"
fi

echo "Building LogSquash..."
npm install
npm run build

echo "✅ LogSquash installed successfully!"
echo "Restart your Gemini CLI session to activate the new tools."
