#!/usr/bin/env python3
"""Test full pipeline with LLM output that has None values"""

import sys
sys.path.insert(0, '/')

from app.utils.json_safe import parse_json_safe
from app.schemas.analysis import AnalysisResult

# Simulate LLM output with None values (this is what was causing the error)
llm_output_with_none = '''
{
  "summary": {
    "abnormal_count": 2,
    "risk_level": "medium"
  },
  "parameters": [
    {
      "name": "Hemoglobin",
      "value": "10.5",
      "unit": "g/dL",
      "normal_range": "12-16",
      "status": "low",
      "risk": "Anemia",
      "explanation": "Low hemoglobin"
    },
    {
      "name": "WBC Count",
      "value": null,
      "unit": "cells/µL",
      "normal_range": "4000-11000",
      "status": "high",
      "risk": null,
      "explanation": null
    },
    {
      "name": "Platelets",
      "value": null,
      "unit": "/µL",
      "normal_range": "150000-400000",
      "status": "low",
      "risk": null,
      "explanation": null
    }
  ]
}
'''

print("Testing full pipeline with None values in LLM output...")
print("=" * 70)

try:
    # Step 1: Parse JSON
    print("\n1. Parsing JSON...")
    parsed = parse_json_safe(llm_output_with_none)
    print(f"   ✅ JSON parsed successfully")

    # Step 2: Apply post-processing (like in the router)
    print("\n2. Post-processing parameters...")
    for param in parsed.get("parameters", []):
        if "value" not in param or param["value"] is None:
            param["value"] = ""
        elif not isinstance(param["value"], str):
            param["value"] = str(param["value"])
    print(f"   ✅ Post-processing complete")

    # Step 3: Validate against schema
    print("\n3. Validating against Pydantic schema...")
    result = AnalysisResult(**parsed)
    print(f"   ✅ Schema validation passed")

    # Step 4: Display results
    print(f"\n4. Results:")
    print(f"   Summary: {result.summary.abnormal_count} abnormal, risk: {result.summary.risk_level}")
    print(f"   Parameters:")
    for i, p in enumerate(result.parameters, 1):
        value_display = repr(p.value) if p.value else "''"
        print(f"      {i}. {p.name}: value={value_display}, status={p.status}")

    print("\n" + "=" * 70)
    print("✅ SUCCESS! Pipeline handles None values correctly")

except Exception as e:
    print(f"\n❌ FAILED: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 70)
    print("❌ Pipeline test failed")

