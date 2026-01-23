#!/bin/bash
# Quick start script for Blood Report Analyzer
# Run this after copying project to new PC with Ollama installed

set -e  # Exit on error

echo "================================"
echo "Blood Report Analyzer - Quick Start"
echo "================================"
echo ""

# Check Python version
echo "✓ Checking Python version..."
python3 --version || {
    echo "✗ Python 3 not found. Please install Python 3.12+"
    exit 1
}

# Check Ollama
echo "✓ Checking Ollama..."
curl -s http://localhost:11434/api/tags > /dev/null || {
    echo "✗ Ollama not running on localhost:11434"
    echo "  Please start Ollama: ollama serve"
    exit 1
}

echo "✓ Ollama is running"

# Create virtual environment
echo ""
echo "✓ Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "✓ Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "✓ Installing dependencies..."
pip install -q -r requirements.txt

echo ""
echo "================================"
echo "Setup Complete! ✅"
echo "================================"
echo ""
echo "Start the application:"
echo ""
echo "Terminal 1 (Backend API):"
echo "  source .venv/bin/activate"
echo "  uvicorn main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "Terminal 2 (Frontend UI):"
echo "  source .venv/bin/activate"
echo "  streamlit run frontend/app.py"
echo ""
echo "Then open browser to:"
echo "  http://localhost:8501"
echo ""
echo "Optional: Copy .env.example to .env to customize settings"
echo ""

