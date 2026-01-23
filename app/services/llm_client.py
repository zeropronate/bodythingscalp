import os
import subprocess
import time
import requests

BASE_PROMPT = (
    "You are a medical lab analyzer. Extract ALL blood test parameters with their normal ranges.\n"
    "\n"
    "EXTRACTION RULES:\n"
    "For EACH parameter in the report:\n"
    "1. Parameter name: extract the test name (e.g., 'Hemoglobin', 'RBC Count', 'WBC Count')\n"
    "2. Value: extract ONLY the numeric value (e.g., '9.6', '3.4', '13800')\n"
    "3. Unit: extract the measurement unit (e.g., 'g/dL', 'million/uL', '/uL', 'mg/dL', '%')\n"
    "4. Normal range: EXTRACT THE RANGE IN PARENTHESES or after text like 'Normal:', 'normal:', 'Range:'\n"
    "   Examples: '(12.0 - 15.5)', '(4.2 - 5.4)', '(< 200)', '(> 50)', '(70 - 100)'\n"
    "5. Status: Compare value to range:\n"
    "   - 'normal' if value is within the range\n"
    "   - 'high' if value is above the range or upper limit\n"
    "   - 'low' if value is below the range or lower limit\n"
    "\n"
    "CRITICAL INSTRUCTIONS:\n"
    "- MUST extract normal_range for EVERY parameter - do not use null\n"
    "- Search for ranges in: parentheses (12.0 - 15.5), after 'Normal:', comparisons (< 200), (> 50)\n"
    "- Value must be NUMERIC ONLY: '9.6' not '9.6 g/dL'\n"
    "- Unit must be separate from value: unit='g/dL', NOT part of value\n"
    "- Status MUST be one of: 'normal', 'high', 'low' (lowercase)\n"
    "- Count how many are 'high' or 'low' for abnormal_count\n"
    "- risk_level: 'high' if >= 6 abnormal, 'medium' if 1-5 abnormal, 'low' if 0 abnormal\n"
    "- Return ONLY valid JSON, no markdown, no explanations\n"
    "\n"
    "JSON Format:\n"
    '{"summary":{"abnormal_count":<int>,"risk_level":"low|medium|high"},"parameters":[{"name":"<name>","value":"<numeric>","unit":"<unit>","normal_range":"<range>","status":"normal|high|low","risk":null,"explanation":null}]}\n'
)

MODEL = os.getenv("OLLAMA_MODEL", "llama3")
OLLAMA_API_URL = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
OLLAMA_NUM_PREDICT = int(os.getenv("OLLAMA_NUM_PREDICT", "200"))
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.0"))
# Base timeout, configurable via env
BASE_TIMEOUT_SECONDS = int(os.getenv("LLM_BASE_TIMEOUT_SECONDS", "30"))
# Hard cap for input size to avoid excessive prompt lengths
MAX_INPUT_CHARS = int(os.getenv("MAX_INPUT_CHARS", "4000"))


def _calculate_timeout(text_length: int) -> int:
    """Calculate dynamic timeout based on text length.

    Note: llama3 on this system is slow (~45s per request minimum).
    Using conservative, generous timeouts.
    """
    if text_length < 1000:
        return 60  # Minimum 60s
    if text_length < 2000:
        return 90
    return 120


def _truncate_text(text: str) -> str:
    if len(text) <= MAX_INPUT_CHARS:
        return text
    # Keep start and end parts to preserve headers and values
    head = text[: MAX_INPUT_CHARS // 2]
    tail = text[-MAX_INPUT_CHARS // 2 :]
    return head + "\n...\n" + tail


def build_prompt(text: str) -> str:
    t = _truncate_text(text)
    return (
        BASE_PROMPT
        + "\nInput report text:\n"
        + "---\n"
        + t
        + "\n---\n"
        + "Return ONLY the JSON object, nothing else:\n"
    )


def _clean_llm_output(output: str) -> str:
    """Clean common issues from LLM output"""
    output = output.strip()

    # Remove common prefixes (more comprehensive list)
    prefixes_to_remove = [
        "here is the extracted data in the required json format:",
        "Here is the extracted data in the required JSON format:",
        "Here is the extracted JSON:",
        "Here is the JSON:",
        "Here's the JSON:",
        "Here is the analysis:",
        "Here's the analysis:",
        "Here is the result:",
        "JSON:",
        "Output:",
        "Result:",
    ]

    for prefix in prefixes_to_remove:
        if output.lower().startswith(prefix.lower()):
            output = output[len(prefix):].strip()
            break

    # Remove markdown code blocks
    if output.startswith("```"):
        lines = output.split('\n')
        # Remove first line (```json or ```)
        lines = lines[1:]
        # Remove last line if it's ```
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        output = '\n'.join(lines).strip()

    # Fix escaped forward slashes that might cause JSON issues
    # But be careful not to break actual escaped quotes
    output = output.replace('\\/', '/')

    return output


def _call_ollama_api(prompt: str, timeout: int) -> str:
    """Call Ollama via HTTP API (faster than subprocess)."""
    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": OLLAMA_TEMPERATURE,
                    "num_predict": OLLAMA_NUM_PREDICT,
                },
            },
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Ollama API unavailable: {e}")


def _call_ollama_subprocess(prompt: str, timeout: int) -> str:
    """Call Ollama via subprocess (fallback method)."""
    process = subprocess.Popen(
        ["ollama", "run", MODEL],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(input=prompt, timeout=timeout)
    except subprocess.TimeoutExpired:
        # Gracefully terminate first, then force kill if needed
        try:
            process.terminate()
            process.wait(timeout=2)  # Wait 2 seconds for graceful shutdown
        except subprocess.TimeoutExpired:
            process.kill()  # Force kill if still running
        raise

    if process.returncode != 0:
        err = stderr.strip()
        if "model not found" in err.lower():
            err += " (hint: run 'ollama pull %s')" % MODEL
        raise RuntimeError(err or "LLM error")

    return stdout.strip()


def analyze_text_with_llm(text: str, max_retries: int = 1) -> str:
    """Analyze text with LLM, with retry logic for transient failures."""
    import logging
    logger = logging.getLogger("llm_client")

    prompt = build_prompt(text)
    # Dynamic timeout with env override if provided
    timeout_seconds = int(
        os.getenv("LLM_TIMEOUT_SECONDS", str(_calculate_timeout(len(text))))
    )

    logger.info(f"LLM call with timeout={timeout_seconds}s for text_length={len(text)}")
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            logger.info(f"LLM attempt {attempt + 1}/{max_retries + 1}")
            # Use subprocess directly (more reliable than API for this setup)
            output = _call_ollama_subprocess(prompt, timeout_seconds)
            output = _clean_llm_output(output)
            logger.info(f"LLM call succeeded on attempt {attempt + 1}")
            return output

        except subprocess.TimeoutExpired:
            logger.warning(f"LLM timeout on attempt {attempt + 1} (timeout={timeout_seconds}s)")
            last_error = RuntimeError(f"LLM timeout (after {timeout_seconds}s)")
            if attempt < max_retries:
                wait_time = 1
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
        except RuntimeError as e:
            logger.error(f"LLM error on attempt {attempt + 1}: {e}")
            last_error = e
            if attempt < max_retries:
                wait_time = 1
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue

    logger.error(f"All LLM attempts failed. Last error: {last_error}")
    raise last_error or RuntimeError("LLM error after retries")
