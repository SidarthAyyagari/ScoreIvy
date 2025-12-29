#!/bin/bash

# ScoreIvy Backend Startup Script
# This script sets up and starts the backend server

set -e

echo "🚀 Starting ScoreIvy Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip, setuptools, and wheel first
echo "📥 Upgrading pip and setuptools..."
pip3 install --upgrade pip setuptools wheel

# Install dependencies
echo "📥 Installing dependencies..."
pip3 install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    echo "DATABASE_URL=postgresql://postgres:postgres@localhost:5432/scoreivy" > .env
fi

# Start the server
echo "🎯 Starting server..."
python3 -m uvicorn main:app --reload

