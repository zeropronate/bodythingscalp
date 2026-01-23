# Blood Report Analyzer - Setup Guide for Export

## Overview
This project analyzes blood test reports using a local Ollama LLM (llama3). All data is processed locally - nothing is sent to external servers.

## Prerequisites
- Python 3.12+
- Ollama installed with llama3 model loaded
- 4GB+ RAM (8GB+ recommended)
- 5GB+ disk space (for llama3 model)

## Installation Steps

### 1. Clone/Copy Project
```bash
# Copy the project folder to your target PC
cp -r FastAPIProject /path/to/destination
cd FastAPIProject
```

### 2. Install Dependencies
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# OR
.venv\Scripts\activate     # On Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Verify Ollama is Running
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Should return JSON with llama3 model listed
# If not, start Ollama service:
# Linux/Mac: ollama serve
# Or check systemctl: sudo systemctl start ollama
```

### 4. Environment Configuration (Optional)
```bash
# Copy example env file (optional - defaults work for local setup)
cp .env.example .env

# Edit .env if you need to customize:
# - Different Ollama host/port
# - Different timeout values
# - Different LLM model (if you want to use mistral, neural-chat, etc.)
```

### 5. Run the Application

#### Terminal 1: Start Backend API
```bash
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2: Start Frontend UI
```bash
source .venv/bin/activate
streamlit run frontend/app.py
```

### 6. Access the Application
- **Frontend UI:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **API Health:** http://localhost:8000/health (if available)

## Environment Variables Explained

### OLLAMA_MODEL
- Default: `llama3`
- Change to other models if available: `mistral`, `neural-chat`, `dolphin`, etc.
- Model must be installed: `ollama pull model-name`

### OLLAMA_API_URL
- Default: `http://localhost:11434`
- Change if Ollama is running on different machine:
  - `http://192.168.1.100:11434` (replace with actual IP)
  - Must be accessible from both backend and frontend PCs

### OLLAMA_NUM_PREDICT
- Default: `200` (tokens max response length)
- Higher = more detailed responses (slower)
- Lower = faster responses but less detail
- Recommended: 100-500

### OLLAMA_TEMPERATURE
- Default: `0.0` (deterministic)
- Range: 0.0 (always same) to 1.0 (random)
- For medical analysis, keep at 0.0

### LLM_BASE_TIMEOUT_SECONDS
- Default: `30`
- App uses dynamic timeout (60-120s) but this is the base
- Adjust if llama3 is very slow: increase to 60

### MAX_INPUT_CHARS
- Default: `4000` (maximum chars to send to LLM)
- Larger reports truncated to this size
- Increase if needed, but slower processing

### BACKEND_URL (Frontend)
- Default: `http://localhost:8000`
- Change if backend is on different machine:
  - `http://192.168.1.100:8000`

## Troubleshooting

### "Connection refused" on localhost:11434
**Problem:** Ollama not running or on different address
**Solution:**
```bash
# Check if Ollama is running
pgrep ollama

# If not, start it
ollama serve

# Or check if it's on a different port/host
ps aux | grep ollama
```

### "llama3 model not found"
**Problem:** llama3 not downloaded
**Solution:**
```bash
ollama pull llama3
ollama list  # Verify it's installed
```

### Slow responses (>30 seconds)
**Problem:** LLM is slow (normal for CPU-only machines)
**Solution:**
1. Increase timeout in .env: `LLM_TIMEOUT_SECONDS=120`
2. Use smaller model: `OLLAMA_MODEL=mistral` (faster, less accurate)
3. Close other applications to free RAM

### "Bind address already in use"
**Problem:** Port 8000 or 8501 already in use
**Solution:**
```bash
# Change ports
uvicorn main:app --port 8001
streamlit run frontend/app.py --server.port 8502
```

### Network connectivity issues
**Problem:** Frontend can't reach backend on different PC
**Solution:**
1. Set BACKEND_URL correctly in frontend:
   ```bash
   export BACKEND_URL=http://192.168.1.100:8000
   streamlit run frontend/app.py
   ```
2. Check firewall allows port 8000
3. Verify backend is listening on 0.0.0.0 not 127.0.0.1

## Project Structure
```
FastAPIProject/
├── main.py                    # FastAPI entry point
├── pyproject.toml            # Project metadata
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── app/
│   ├── __init__.py
│   ├── routers/
│   │   └── analyze.py        # /analyze endpoint
│   ├── services/
│   │   ├── llm_client.py     # Ollama LLM interface
│   │   ├── extract_text.py   # PDF/image text extraction
│   │   ├── ocr_service.py    # Tesseract OCR
│   │   └── preprocess.py     # Text preprocessing
│   ├── schemas/
│   │   └── analysis.py       # Pydantic models
│   └── utils/
│       └── json_safe.py      # JSON parsing helpers
├── frontend/
│   └── app.py                # Streamlit UI
└── docker/
    └── Dockerfile            # Docker build file (optional)
```

## No Secrets Required! ✅
This project has **NO API keys, passwords, or secrets** to manage:
- All LLM processing is local (Ollama)
- No external API calls
- No database credentials
- No authentication tokens

Just ensure Ollama and llama3 are installed on the target PC!

## Performance Tips

### For Faster Analysis
1. Use smaller model: `OLLAMA_MODEL=mistral`
2. Reduce tokens: `OLLAMA_NUM_PREDICT=100`
3. Reduce timeout: `LLM_TIMEOUT_SECONDS=30`
4. Reduce input: `MAX_INPUT_CHARS=2000`

### For Better Accuracy
1. Use larger model: `OLLAMA_MODEL=neural-chat`
2. Increase tokens: `OLLAMA_NUM_PREDICT=500`
3. Increase timeout: `LLM_TIMEOUT_SECONDS=120`
4. Increase input: `MAX_INPUT_CHARS=6000`

## Testing the Setup
```bash
# 1. Check Ollama connection
curl http://localhost:11434/api/tags

# 2. Test backend health
curl http://localhost:8000/docs

# 3. Test a sample analysis via API
curl -X POST http://localhost:8000/analyze \
  -F "file=@sample_report.pdf"

# 4. Open UI and upload a report
# http://localhost:8501
```

## Summary
✅ No secrets to manage
✅ All local processing
✅ Works offline
✅ Portable to any PC with Ollama
✅ Environment variables are optional (sensible defaults provided)

**Just copy the project and ensure Ollama + llama3 are installed on the target PC!**

