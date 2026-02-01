import os
import time
import requests
import logging

logger = logging.getLogger("llm_client")

# ========================
# Configuration
# ========================

MODEL = os.getenv("OLLAMA_MODEL", "mistral")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")

OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.0"))
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "120"))
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "2048"))

MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "2000"))
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "40"))

# ========================
# Prompt
# ========================

BASE_PROMPT = (
    "You are a medical lab analyzer. Extract ALL blood test parameters with their normal ranges.\n\n"

    "EXTRACTION RULES:\n"
    "For EACH parameter:\n"
    "1. name\n"
    "2. numeric value only\n"
    "3. unit\n"
    "4. normal_range from report\n"
    "5. status: normal/high/low\n\n"

    "CRITICAL:\n"
    "- normal_range must NOT be null\n"
    "- value must be numeric only\n"
    "- status must be lowercase\n"
    "- calculate abnormal_count\n"
    "- risk_level: low(0), medium(1-5), high(>=6)\n\n"

    "Return ONLY valid JSON in this format:\n"
    '{"summary":{"abnormal_count":0,"risk_level":"low"},"parameters":[{"name":"","value":"","unit":"","normal_range":"","status":"","risk":null,"explanation":null}]}\n'
)

# ========================
# Utilities
# ========================

def _truncate_text(text: str) -> str:
    if len(text) <= MAX_INPUT_CHARS:
        return text
    half = MAX_INPUT_CHARS // 2
    return text[:half] + "\n...\n" + text[-half:]


def build_prompt(report_text: str) -> str:
    report_text = _truncate_text(report_text)
    return (
        BASE_PROMPT
        + "\nInput report text:\n---\n"
        + report_text
        + "\n---\nReturn ONLY the JSON object:\n"
    )


def _clean_llm_output(output: str) -> str:
    output = output.strip()

    prefixes = [
        "here is", "json:", "output:", "result:"
    ]

    for p in prefixes:
        if output.lower().startswith(p):
            output = output[len(p):].strip()

    if output.startswith("```"):
        lines = output.splitlines()
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        output = "\n".join(lines).strip()

    return output.replace("\\/", "/")


# ========================
# Ollama HTTP Call
# ========================

def _call_ollama_api(prompt: str, timeout: int) -> str:
    response = requests.post(
        f"{OLLAMA_API_URL}/api/generate",
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": OLLAMA_TEMPERATURE,
                "num_predict": OLLAMA_NUM_PREDICT,
                "num_ctx": OLLAMA_NUM_CTX,
            }
        },
        timeout=timeout,
    )

    response.raise_for_status()
    return response.json().get("response", "")


# ========================
# Public API
# ========================

def analyze_text_with_llm(report_text: str, max_retries: int = 1) -> str:
    prompt = build_prompt(report_text)

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"LLM request attempt {attempt + 1}")
            output = _call_ollama_api(prompt, LLM_TIMEOUT_SECONDS)
            return _clean_llm_output(output)

        except Exception as e:
            logger.warning(f"LLM failure attempt {attempt + 1}: {e}")
            if attempt >= max_retries:
                raise
            time.sleep(1)


# ========================
# Warmup (optional)
# ========================

def warmup_model():
    try:
        _call_ollama_api("Hello", 20)
        logger.info("LLM warmup completed")
    except Exception as e:
        logger.warning(f"LLM warmup failed: {e}")
