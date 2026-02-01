#!/usr/bin/env python3
"""Test full pipeline with potentially problematic LLM outputs"""

from app.utils.json_safe import parse_json_safe
from app.schemas.analysis import AnalysisResult

# Simulate various problematic LLM outputs
test_outputs = [
    # Output 1: Clean JSON (should work)
    {
        "name": "Clean JSON",
        "output": '{"summary": {"abnormal_count": 2, "risk_level": "medium"}, "parameters": [{"name": "Hemoglobin", "value": "10.5", "unit": "g/dL", "normal_range": "12-16", "status": "low", "risk": "Anemia", "explanation": "Low hemoglobin"}]}'
    },

    # Output 2: JSON with markdown (common LLM behavior)
    {
        "name": "JSON with markdown",
        "output": '```json\n{"summary": {"abnormal_count": 2, "risk_level": "medium"}, "parameters": [{"name": "Hemoglobin", "value": "10.5", "unit": "g/dL", "normal_range": "12-16", "status": "low", "risk": "Anemia", "explanation": "Low hemoglobin"}]}\n```'
    },

    # Output 3: JSON with prefix text (what we saw in the logs)
    {
        "name": "JSON with prefix",
        "output": 'Here is the extracted JSON:\n\n{"summary": {"abnormal_count": 2, "risk_level": "medium"}, "parameters": [{"name": "Hemoglobin", "value": "10.5", "unit": "g/dL", "normal_range": "12-16", "status": "low", "risk": "Anemia", "explanation": "Low hemoglobin"}]}'
    },

    # Output 4: Multi-line with extra whitespace
    {
        "name": "Multi-line with whitespace",
        "output": '''
        
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
                }
            ]
        }
        
        '''
    }
]

print("Testing full pipeline with various LLM output formats...")
print("=" * 70)

for i, test_case in enumerate(test_outputs, 1):
    print(f"\n{i}. Testing: {test_case['name']}")
    print("-" * 70)

    try:
        # Step 1: Parse JSON
        parsed = parse_json_safe(test_case['output'])
        print(f"   ✅ JSON parsed successfully")

        # Step 2: Validate against schema
        result = AnalysisResult(**parsed)
        print(f"   ✅ Schema validation passed")
        print(f"   📊 Found {result.summary.abnormal_count} abnormal parameters")
        print(f"   🎯 Risk level: {result.summary.risk_level}")

    except Exception as e:
        print(f"   ❌ FAILED: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 70)
print("Pipeline test complete!")

