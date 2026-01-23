#!/usr/bin/env python3
"""Test schema handles alternative field names from LLM"""

import sys
sys.path.insert(0, '/home/nkro/PycharmProjects/FastAPIProject')

from app.schemas.analysis import AnalysisResult

# Simulate LLM output with alternative field names
llm_output_dict = {
    "summary": {
        "abnormal_count": 2,
        "risk_level": "medium"
    },
    "parameters": [
        {
            "parameter": "Yeast",  # Using 'parameter' instead of 'name'
            "value": "",
            "result": "Negative",  # Using 'result' instead of 'status'
            "normal_range": "Negative"
        },
        {
            "parameter": "RBC casts",
            "value": "",
            "result": "0.00 /hpf",  # Non-standard status value
            "normal_range": "0.00 /hpf"
        }
    ]
}

print("Testing schema with alternative field names...")
print("=" * 70)

try:
    result = AnalysisResult(**llm_output_dict)
    print("✅ SUCCESS! Schema accepted alternative field names")
    print(f"\nParsed {len(result.parameters)} parameters:")
    for i, param in enumerate(result.parameters, 1):
        print(f"  {i}. name='{param.name}', status='{param.status}', value='{param.value}'")
    print(f"\nSummary: {result.summary.abnormal_count} abnormal, risk={result.summary.risk_level}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)

