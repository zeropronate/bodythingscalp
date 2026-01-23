import json
import re


def parse_json_safe(s: str):
    s = s.strip()

    # Remove markdown code fences if present
    if s.startswith("```"):
        # Find the end of the first line (which might be ```json or just ```)
        first_newline = s.find('\n')
        if first_newline != -1:
            s = s[first_newline + 1:]
        else:
            s = s[3:]  # Remove ```

        if s.endswith("```"):
            s = s[:-3]
        s = s.strip()

    # Try direct parse first
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass

    # Try to extract JSON object from text
    # Find the outermost { and } pair
    start = s.find('{')
    end = s.rfind('}')

    if start != -1 and end != -1 and end > start:
        fragment = s[start:end + 1]
        try:
            return json.loads(fragment)
        except json.JSONDecodeError:
            pass

    # Last resort: try to fix common JSON issues
    # Replace single quotes with double quotes (but carefully)
    fragment_cleaned = re.sub(r"'([^']*)':", r'"\1":', fragment if 'fragment' in locals() else s)
    try:
        return json.loads(fragment_cleaned)
    except json.JSONDecodeError:
        pass

    # If all else fails, raise the original error
    raise ValueError(f"Could not parse JSON from LLM output. First 500 chars: {s[:500]}")
