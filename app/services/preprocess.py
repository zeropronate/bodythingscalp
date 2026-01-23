import re

PARAM_HINTS = [
    "hemoglobin", "hb", "wbc", "rbc", "platelet", "platelets",
    "hematocrit", "mcv", "mch", "mchc", "rdw", "neutrophil", "lymphocyte",
    "monocyte", "eosinophil", "basophil", "glucose", "cholesterol", "hdl",
    "ldl", "triglyceride", "creatinine", "urea", "bilirubin", "alt", "ast",
    "alkaline phosphatase", "sodium", "potassium", "calcium", "vitamin b12",
    "vitamin d", "tsh", "t3", "t4", "iron", "ferritin"
]

UNIT_PATTERN = re.compile(r"\b(%|mg/dl|g/dl|mmol/l|10\^\d+/u?l|10\^\d+/?l|g/l|ng/ml|pg/ml|fl|u/l|iu/l|k/u?l|m/u?l|cells/u?l)\b", re.I)
NUMBER_PATTERN = re.compile(r"[-+]?\b\d+(?:\.\d+)?\b")


def compress_report_text(text: str, max_chars: int = 3000) -> str:
    """
    Reduce long report text by keeping lines likely to contain parameters and values.
    Heuristics: lines with numbers and units, or lines containing known parameter hints.
    """
    lines = [l.strip() for l in text.splitlines()]
    keep = []
    for l in lines:
        if not l:
            continue
        lower = l.lower()
        has_number = bool(NUMBER_PATTERN.search(lower))
        has_unit = bool(UNIT_PATTERN.search(lower))
        has_hint = any(h in lower for h in PARAM_HINTS)
        if (has_number and has_unit) or has_hint:
            keep.append(l)
    # Fallback: if too few lines, include lines with colon (label: value)
    if len(keep) < 10:
        keep.extend([l for l in lines if ":" in l])
    # Deduplicate while preserving order
    seen = set()
    filtered = []
    for l in keep:
        if l not in seen:
            seen.add(l)
            filtered.append(l)
    result = "\n".join(filtered)
    if len(result) <= max_chars:
        return result
    return result[:max_chars]

