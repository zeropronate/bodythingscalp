#!/usr/bin/env python3
"""Test JSON parsing with various LLM output formats"""

from app.utils.json_safe import parse_json_safe

test_cases = [
    # Test 1: Clean JSON
    ('{"summary": {"abnormal_count": 1, "risk_level": "low"}, "parameters": []}', "Clean JSON"),

    # Test 2: JSON with markdown code blocks
    ('```json\n{"summary": {"abnormal_count": 1, "risk_level": "low"}, "parameters": []}\n```', "JSON with markdown"),

    # Test 3: JSON with text before
    ('Here is the result:\n{"summary": {"abnormal_count": 1, "risk_level": "low"}, "parameters": []}', "JSON with prefix text"),

    # Test 4: JSON with text before and after
    ('Analysis complete:\n{"summary": {"abnormal_count": 1, "risk_level": "low"}, "parameters": []}\nEnd of analysis', "JSON with prefix and suffix"),

    # Test 5: Markdown without json tag
    ('```\n{"summary": {"abnormal_count": 1, "risk_level": "low"}, "parameters": []}\n```', "Markdown without json tag"),
]

print("Testing JSON parsing with various formats...")
print("=" * 60)

for i, (test_input, description) in enumerate(test_cases, 1):
    print(f"\nTest {i}: {description}")
    print("-" * 60)
    try:
        result = parse_json_safe(test_input)
        print(f"✅ SUCCESS: Parsed {len(str(result))} chars")
        print(f"   Summary: abnormal_count={result['summary']['abnormal_count']}")
    except Exception as e:
        print(f"❌ FAILED: {e}")

print("\n" + "=" * 60)
print("Test complete!")

