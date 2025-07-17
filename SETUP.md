# PlanogramVisionAgent Setup Guide

## Project Overview
PlanogramVisionAgent is a computer vision application that analyzes retail shelf videos and images to detect and locate products. It uses Azure OpenAI GPT-4 Vision to identify products and provides price comparison functionality.

## System Requirements
- Python 3.8 or higher
- WSL/Linux environment (recommended)
- Internet connection for API access

## Setup Instructions

### 1. Environment Setup

**Option A: Using Virtual Environment (Recommended)**
```bash
# Install python3-venv (if not available)
sudo apt update
sudo apt install python3.12-venv

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate     # On Windows
```

**Option B: System-wide Installation**
```bash
# Install dependencies directly
python3 -m pip install -r requirements.txt
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Variables Configuration

Edit the `.env` file with your actual API credentials:

```env
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_actual_azure_openai_api_key
AZURE_SEARCH_SERVICE_ENDPOINT=https://your-service-name.openai.azure.com/
GPT4_LLM_MODEL_DEPLOYMENT_NAME=your_gpt4_deployment_name
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# SerpAPI Configuration (for price comparison)
SERPAPI_API_KEY=your_actual_serpapi_key
```

**Getting API Keys:**
- **Azure OpenAI**: Sign up at https://azure.microsoft.com/en-us/products/cognitive-services/openai-service/
- **SerpAPI**: Sign up at https://serpapi.com/ for Google Shopping API access

### 4. Run the Application
```bash
streamlit run streamlit_app.py
```

The application will be available at `http://localhost:8501`

## Project Structure

```
PlanogramVisionAgent/
├── README.md                 # Basic project info
├── requirements.txt          # Python dependencies
├── .env                     # Environment variables (create this)
├── streamlit_app.py         # Main Streamlit application
├── product_tile.html        # HTML template for price display
├── uploaded_files/          # Storage for uploaded videos/images
│   ├── 2.mp4
│   ├── image6.jpg
│   └── image8.png
└── app/
    ├── analyze.py           # Core video/image analysis
    ├── mcp_server.py        # Tool orchestration
    ├── tools/
    │   └── price_compare.py # Price comparison using SerpAPI
    └── utils/
        └── product_extractor.py # Product name extraction
```

## Usage

1. **Upload File**: Upload a video (MP4, MOV, AVI) or image (JPG, PNG) of retail shelves
2. **Ask Question**: Enter a natural language question about product locations
   - Example: "Where is Tide powder located?"
   - Example: "Show me the detergent section"
3. **View Results**: 
   - Get AI-generated summary of product locations
   - For videos: See timeline markers indicating when products are visible
   - View extracted frames at specific timestamps
4. **Price Comparison**: Toggle price comparison to see current prices from e-commerce sites

## Features

- **Multi-format Support**: Videos (MP4, MOV, AVI) and images (JPG, PNG)
- **AI-powered Analysis**: Uses Azure OpenAI GPT-4 Vision for accurate product detection
- **Interactive Timeline**: For videos, shows when products are detected
- **Frame Extraction**: View specific frames where products are found
- **Price Integration**: Real-time price comparison from multiple retailers
- **File Management**: Upload new files or choose from previously uploaded ones

## Troubleshooting

### Common Issues

1. **Virtual Environment Creation Fails**
   ```bash
   # Install required packages
   sudo apt install python3.12-venv
   ```

2. **API Key Errors**
   - Ensure `.env` file exists with correct API keys
   - Check Azure OpenAI service is active and deployment name is correct

3. **Video Processing Issues**
   - Ensure OpenCV is properly installed: `pip install opencv-python`
   - Check video format is supported (MP4, MOV, AVI)

4. **Price Comparison Not Working**
   - Verify SERPAPI_API_KEY is set correctly
   - Check SerpAPI quota limits

### Development Notes

- The application processes video frames at intervals (default: every 23rd frame)
- AI analysis includes accuracy evaluation and confidence scoring
- Price comparison shows results from top 5 shopping results
- Files are stored in `uploaded_files/` directory

## API Requirements

- **Azure OpenAI**: GPT-4 Vision model with sufficient quota
- **SerpAPI**: Google Shopping API access for price comparison

## Next Steps

The application is now ready for use and further development. Key areas for enhancement:
- Add more e-commerce platforms for price comparison
- Implement batch processing for multiple videos
- Add export functionality for analysis results
- Integrate with inventory management systems