import io
from typing import Optional
from PIL import Image
import pytesseract

def extract_text_from_image_bytes(data: bytes) -> str:
    try:
        img = Image.open(io.BytesIO(data))
    except Exception as e:
        raise RuntimeError(f"Invalid image data: {e}")
    # Convert to RGB to avoid mode issues
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    text = pytesseract.image_to_string(img)
    return text or ""

