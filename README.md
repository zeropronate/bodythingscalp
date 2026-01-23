# Blood Report Analyzer

LLM-powered medical document processing: upload blood test reports (PDF or image), extract parameters, detect abnormal values, and get structured insights using a local LLM (Ollama).

## Stack
- FastAPI backend
- Streamlit frontend
- OCR: Tesseract via `pytesseract`
- PDF: `pdfplumber`
- LLM: Ollama (`llama3` configurable)

## Run Locally
1. Install system deps: Tesseract + Poppler (Linux)
2. Install Python deps:
```
pip install -r app/requirements.txt
```
3. Start Ollama and pull model:
```
ollama pull llama3
```
4. Run backend:
```
uvicorn main:app --reload
```
5. Run frontend:
```
streamlit run frontend/app.py
```

Set `BACKEND_URL` in Streamlit secrets if backend is remote.

## API
POST /analyze
- multipart/form-data: file
- returns structured JSON with summary and parameters

## Docker
Build and run backend:
```
docker build -t blood-analyzer -f docker/Dockerfile .
docker run -p 8000:8000 blood-analyzer
```
Note: container needs access to Ollama on host or within container; recommend running Ollama on host and calling from backend.

## Notes
- Max upload 10 MB; allowed types: PDF/JPG/PNG
- Handles malformed PDFs/pages gracefully
- Strict JSON parsing and Pydantic schema validation

## Disclaimer
This application provides informational insights only and is not a substitute for professional medical advice.

