#!/bin/bash

# Script to fix psycopg2-binary installation issues

cd "$(dirname "$0")"

echo "🔧 Fixing backend dependencies installation..."

# Activate venv if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Upgrade pip, setuptools, and wheel
echo "📦 Upgrading pip, setuptools, and wheel..."
pip3 install --upgrade pip setuptools wheel

# Try installing psycopg2-binary first
echo "📦 Installing psycopg2-binary..."
pip3 install psycopg2-binary

# Then install all other dependencies
echo "📦 Installing all dependencies..."
pip3 install -r requirements.txt

echo "✅ Installation complete!"

