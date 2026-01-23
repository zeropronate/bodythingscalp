import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.schemas.analysis import AnalysisResult
from app.services.extract_text import extract_text_from_upload
from app.services.llm_client import analyze_text_with_llm
from app.services.preprocess import compress_report_text
from app.utils.json_safe import parse_json_safe
import time

logger = logging.getLogger("api.analyze")

router = APIRouter()

MAX_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_EXTS = {"pdf", "jpg", "jpeg", "png"}

@router.post("/analyze", response_model=AnalysisResult)
def analyze(file: UploadFile = File(...)):
    filename = file.filename or "upload"
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    logger.info(f"Analyze request: filename={filename}, ext={ext}")
    if ext not in ALLOWED_EXTS:
        logger.warning(f"Rejected file type: {ext}")
        raise HTTPException(status_code=400, detail="Invalid file type. Allowed: PDF, JPG, PNG")
    content = file.file.read()
    size = len(content)
    logger.info(f"File size: {size} bytes")
    if size > MAX_SIZE_BYTES:
        logger.warning(f"File too large: {size} bytes")
        raise HTTPException(status_code=400, detail="File too large. Max 10 MB")

    # Extract text
    try:
        text = extract_text_from_upload(ext, content)
        logger.info(f"Extracted text length: {len(text)} chars")
        text = compress_report_text(text, max_chars=3000)
        logger.info(f"Preprocessed text length: {len(text)} chars")
    except Exception as e:
        logger.exception(f"Failed to parse file: {e}")
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    if not text or not text.strip():
        logger.warning("No readable text extracted from file")
        raise HTTPException(status_code=400, detail="No readable text extracted from file")

    # Call LLM
    try:
        t0 = time.time()
        llm_output = analyze_text_with_llm(text)
        dt = (time.time() - t0) * 1000
        logger.info(f"LLM call completed in {dt:.1f} ms, output length={len(llm_output)}")
        # Optionally log a small prefix of output for debugging
        logger.debug(f"LLM output (prefix): {llm_output[:200]}")
    except Exception as e:
        logger.exception(f"LLM failure: {e}")
        raise HTTPException(status_code=500, detail=f"LLM failure: {e}")

    # Validate JSON
    try:
        parsed = parse_json_safe(llm_output)

        # Ensure required fields exist with defaults if missing
        if "summary" not in parsed:
            parsed["summary"] = {"abnormal_count": 0, "risk_level": "low"}
        if "parameters" not in parsed:
            parsed["parameters"] = []

        # Clean up parameters to ensure value is always a string
        for param in parsed.get("parameters", []):
            if "value" not in param or param["value"] is None:
                param["value"] = ""
            elif not isinstance(param["value"], str):
                param["value"] = str(param["value"])

        result = AnalysisResult(**parsed)
    except Exception as e:
        logger.error(f"Invalid JSON output from LLM: {e}")
        logger.error(f"LLM output was:\n{llm_output}")
        raise HTTPException(status_code=500, detail=f"Invalid JSON output from LLM: {e}")

    return JSONResponse(content=result.model_dump())
