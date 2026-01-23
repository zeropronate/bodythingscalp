import io
from typing import Literal

from app.services.pdf_parser import extract_text_from_pdf_bytes
from app.services.ocr_service import extract_text_from_image_bytes

Ext = Literal["pdf", "jpg", "jpeg", "png"]

def extract_text_from_upload(ext: Ext, data: bytes) -> str:
    if ext == "pdf":
        return extract_text_from_pdf_bytes(data)
    else:
        return extract_text_from_image_bytes(data)

