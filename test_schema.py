#!/usr/bin/env python3
"""Test the updated schema that handles None values"""

import sys
sys.path.insert(0, '/home/nkro/PycharmProjects/FastAPIProject')

from app.schemas.analysis import Parameter, AnalysisResult

# Test 1: Parameter with None value
print("Test 1: Parameter with None value")
try:
    param = Parameter(
        name="Hemoglobin",
        value=None,  # This should be converted to ""
        unit="g/dL",
        normal_range="12-16",
        status="low",
        risk="Anemia",
        explanation="Low hemoglobin"
    )
    print(f"✅ SUCCESS: value={repr(param.value)}")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 2: Parameter with numeric value
print("\nTest 2: Parameter with numeric value")
try:
    param = Parameter(
        name="Glucose",
        value=95,  # This should be converted to "95"
        unit="mg/dL",
        normal_range="70-100",
        status="normal"
    )
    print(f"✅ SUCCESS: value={repr(param.value)} (type: {type(param.value).__name__})")
except Exception as e:
    print(f"❌ FAILED: {e}")

# Test 3: Full AnalysisResult with None values
print("\nTest 3: Full AnalysisResult with None values")
try:
    data = {
        "summary": {"abnormal_count": 2, "risk_level": "medium"},
        "parameters": [
            {
                "name": "Hemoglobin",
                "value": None,  # Should be converted
                "unit": "g/dL",
                "normal_range": "12-16",
                "status": "low"
            },
            {
                "name": "WBC",
                "value": None,  # Should be converted
                "unit": "cells/µL",
                "normal_range": "4000-11000",
                "status": "high"
            },
            {
                "name": "Glucose",
                "value": "95",  # Already a string
                "unit": "mg/dL",
                "normal_range": "70-100",
                "status": "normal"
            }
        ]
    }
    result = AnalysisResult(**data)
    print(f"✅ SUCCESS: Created AnalysisResult with {len(result.parameters)} parameters")
    for i, p in enumerate(result.parameters):
        print(f"   Parameter {i+1}: {p.name} = {repr(p.value)}")
except Exception as e:
    print(f"❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
print("All schema tests complete!")

