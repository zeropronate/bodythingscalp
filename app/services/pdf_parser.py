import io
import pdfplumber

def extract_text_from_pdf_bytes(data: bytes) -> str:
    text_parts = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            try:
                text = page.extract_text() or ""
                text_parts.append(text)
            except Exception:
                # Skip problematic pages
                continue
    return "\n".join(t for t in text_parts if t)

