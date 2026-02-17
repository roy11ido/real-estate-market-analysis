#!/bin/bash
set -e

echo "=== Real Estate Advertising Agent - Setup ==="
echo ""

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "Homebrew already installed."
fi

# Install Python 3.12
if ! command -v python3.12 &> /dev/null; then
    echo "Installing Python 3.12..."
    brew install python@3.12
else
    echo "Python 3.12 already installed."
fi

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3.12 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate and install dependencies
echo "Installing dependencies..."
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright Chromium browser..."
playwright install chromium

# Create data directories
mkdir -p data/cookies data/images_cache data/logs

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "1. Edit .env with your Notion API key"
echo "2. Add Facebook groups to config/facebook_groups.yaml"
echo "3. Run: source .venv/bin/activate"
echo "4. Run: streamlit run src/app.py"
