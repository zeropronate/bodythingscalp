#!/usr/bin/env python3
"""Test the improved LLM prompt with explicit instructions for value comparison"""

import sys
sys.path.insert(0, '/home/nkro/PycharmProjects/FastAPIProject')

from app.services.llm_client import build_prompt, _clean_llm_output
import subprocess
import time

sample_report = """
Patient: Anita Verma
Age: 45
Gender: Female

Hemoglobin: 9.6 g/dL (Normal: 12.0 - 15.5)
RBC Count: 3.4 million/uL (Normal: 4.2 - 5.4)
WBC Count: 13800 /uL (Normal: 4000 - 11000)
Blood Sugar (Fasting): 162 mg/dL (Normal: 70 - 100)
Total Cholesterol: 242 mg/dL (Normal: < 200)
HDL Cholesterol: 32 mg/dL (Normal: > 50)
"""

print("Testing improved LLM prompt for value comparison...")
print("=" * 70)

try:
    prompt = build_prompt(sample_report)
    print("Prompt preview:")
    print(prompt[:500])
    print("\n" + "=" * 70)
    print("Sending to LLM...")

    # Call LLM
    process = subprocess.Popen(
        ["ollama", "run", "llama3"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    stdout, stderr = process.communicate(input=prompt, timeout=120)

    if process.returncode != 0:
        print(f"❌ LLM Error: {stderr}")
    else:
        output = stdout.strip()
        cleaned = _clean_llm_output(output)
        print("LLM Response (cleaned):")
        print(cleaned[:1000])

        # Try to parse as JSON to verify format
        import json
        try:
            data = json.loads(cleaned)
            print("\n✅ Valid JSON!")
            print(f"Abnormal count: {data['summary']['abnormal_count']}")
            print(f"Risk level: {data['summary']['risk_level']}")
            print(f"Parameters: {len(data['parameters'])}")
            for p in data['parameters'][:3]:
                print(f"  - {p['name']}: {p['status']} (value={p['value']}, range={p['normal_range']})")
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON Parse Error: {e}")
            print(f"First 500 chars: {cleaned[:500]}")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)

