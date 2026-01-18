#!/bin/bash
# Start script for the Terabox bot

# Exit on error
set -e

echo "Installing Playwright browsers..."
playwright install chromium --with-deps

echo "Starting bot..."
python main.py
