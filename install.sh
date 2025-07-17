#!/bin/bash

echo "=== PlanogramVisionAgent Installation Script ==="
echo "This script will set up the PlanogramVisionAgent project."
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: requirements.txt not found. Please run this script from the PlanogramVisionAgent directory."
    exit 1
fi

echo "Step 1: Installing system dependencies..."
echo "Note: You may need to run these commands manually with sudo:"
echo "  sudo apt update"
echo "  sudo apt install -y python3-pip python3-venv"
echo ""

# Try to install pip if not available
if ! python3 -m pip --version &> /dev/null; then
    echo "Installing pip..."
    # Download get-pip.py if pip is not available
    curl -sSL https://bootstrap.pypa.io/get-pip.py | python3 - --user
fi

echo "Step 2: Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv || {
        echo "Virtual environment creation failed. Installing virtualenv..."
        python3 -m pip install --user virtualenv
        python3 -m virtualenv venv
    }
fi

echo "Step 3: Activating virtual environment..."
source venv/bin/activate

echo "Step 4: Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

echo "Step 5: Checking installation..."
python3 -c "import streamlit; print('Streamlit version:', streamlit.__version__)"
python3 -c "import cv2; print('OpenCV version:', cv2.__version__)"
python3 -c "import openai; print('OpenAI library installed')"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To start the application:"
echo "1. Activate the virtual environment: source venv/bin/activate"
echo "2. Configure your API keys in the .env file"
echo "3. Run the application: streamlit run streamlit_app.py"
echo ""
echo "The application will be available at: http://localhost:8501"
echo ""
echo "See SETUP.md for detailed configuration instructions."