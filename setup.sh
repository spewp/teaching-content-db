#!/bin/bash

echo "Setting up Teaching Content Database development environment..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from your package manager or https://python.org"
    exit 1
fi

echo "✓ Python 3 found"
echo

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

if [ $? -ne 0 ]; then
    echo "Error: Failed to create virtual environment"
    exit 1
fi

echo "✓ Virtual environment created"
echo

# Activate virtual environment and install dependencies
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies"
    exit 1
fi

echo
echo "✅ Setup complete!"
echo
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo
echo "To deactivate, run:"
echo "  deactivate" 