#!/usr/bin/env python3
"""Quick test of LLM integration"""

from app.services.llm_client import analyze_text_with_llm

sample_text = """
BLOOD TEST REPORT
Patient: John Doe

COMPLETE BLOOD COUNT
Hemoglobin: 10.5 g/dL (Normal: 12-16 g/dL)
WBC Count: 8500 cells/µL (Normal: 4000-11000 cells/µL)
Platelets: 250000 /µL (Normal: 150000-400000 /µL)

LIPID PROFILE
Total Cholesterol: 240 mg/dL (Normal: <200 mg/dL)
HDL: 35 mg/dL (Normal: >40 mg/dL)
LDL: 160 mg/dL (Normal: <100 mg/dL)
"""

print("Testing LLM with sample blood report...")
print("-" * 50)

try:
    result = analyze_text_with_llm(sample_text)
    print("SUCCESS!")
    print("LLM Output:")
    print(result)
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

