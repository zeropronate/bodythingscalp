from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class Parameter(BaseModel):
    name: str = Field(default="")
    value: Optional[str] = None
    unit: Optional[str] = None
    normal_range: Optional[str] = None
    status: str = Field(default="normal", pattern=r"^(normal|high|low)$")
    risk: Optional[str] = None
    explanation: Optional[str] = None

    @field_validator('name', mode='before')
    @classmethod
    def convert_parameter_to_name(cls, v):
        """Map 'parameter' field to 'name' for LLM consistency"""
        if v is None or v == "":
            return ""
        return str(v)

    @field_validator('status', mode='before')
    @classmethod
    def convert_result_to_status(cls, v):
        """Map 'result' field to 'status' and normalize to lowercase"""
        if v is None or v == "":
            return "normal"
        v_str = str(v).lower().strip()
        # Normalize common variations
        if v_str in ("normal", "high", "low"):
            return v_str
        # Default to normal if unknown
        return "normal"

    @field_validator('value', mode='before')
    @classmethod
    def convert_none_to_empty_string(cls, v):
        """Convert None values to empty string and any other type to string"""
        if v is None:
            return ""
        if not isinstance(v, str):
            return str(v)
        return v

    @model_validator(mode='before')
    @classmethod
    def map_alternative_fields(cls, data):
        """Map alternative field names that LLM might use"""
        if isinstance(data, dict):
            # Map 'parameter' to 'name'
            if 'parameter' in data and 'name' not in data:
                data['name'] = data.pop('parameter')
            # Map 'result' to 'status'
            if 'result' in data and 'status' not in data:
                data['status'] = data.pop('result')
            # Map 'range' to 'normal_range'
            if 'range' in data and 'normal_range' not in data:
                data['normal_range'] = data.pop('range')
            # If status is missing but we have value and normal_range, infer it
            if 'status' not in data or data.get('status') is None:
                data['status'] = 'normal'  # Default value
        return data

class Summary(BaseModel):
    abnormal_count: int
    risk_level: str = Field(..., pattern=r"^(low|medium|high)$")

class AnalysisResult(BaseModel):
    summary: Summary
    parameters: List[Parameter]

