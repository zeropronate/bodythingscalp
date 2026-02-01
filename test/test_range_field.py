#!/usr/bin/env python3
"""Test schema handles LLM output with 'range' instead of 'normal_range'"""

import sys
sys.path.insert(0, '/')

from app.schemas.analysis import AnalysisResult

# Simulate actual LLM output from the error
llm_output_dict = {
    "summary": {
        "abnormal_count": 7,
        "risk_level": "high"
    },
    "parameters": [
        {
            "name": "Hemoglobin",
            "value": "9.6 g/dL",
            "range": "12.0 - 15.5"  # Using 'range' instead of 'normal_range'
            # Missing 'status' field
        },
        {
            "name": "RBC Count",
            "value": "3.4 million/uL",
            "range": "4.2 - 5.4"
        },
        {
            "name": "WBC Count",
            "value": "13800 /uL",
            "range": "4000 - 11000"
        }
    ]
}

print("Testing schema with 'range' field instead of 'normal_range'...")
print("=" * 70)

try:
    result = AnalysisResult(**llm_output_dict)
    print("✅ SUCCESS! Schema handled alternative field names")
    print(f"\nParsed {len(result.parameters)} parameters:")
    for i, param in enumerate(result.parameters, 1):
        print(f"  {i}. {param.name}")
        print(f"     value: {param.value}")
        print(f"     normal_range: {param.normal_range}")
        print(f"     status: {param.status}")
    print(f"\nSummary: {result.summary.abnormal_count} abnormal, risk={result.summary.risk_level}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)

