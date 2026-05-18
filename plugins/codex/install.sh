#!/bin/bash
# LogSquash Installer for Codex CLI

set -e

EXTENSION_DIR="$HOME/.codex/extensions/logsquash"
REPO_URL="https://github.com/radoone/LogSquash.git"

echo "🪵 LogSquash: Installing Codex extension..."

mkdir -p "$HOME/.codex/extensions"

if [ -d "$EXTENSION_DIR" ]; then
    echo "Updating existing installation in Codex CLI..."
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

# Link the config to the root of the extension so Codex CLI can find it
ln -sf plugins/codex/codex-extension.json codex-extension.json

echo "✅ LogSquash installed successfully!"
echo "Restart your Codex CLI session to activate the new tools."
