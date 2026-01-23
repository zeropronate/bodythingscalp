from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from pathlib import Path

OUTPUT_DIR = Path("sample_reports")
OUTPUT_DIR.mkdir(exist_ok=True)

styles = getSampleStyleSheet()

SAMPLE_REPORTS = [
    {
        "filename": "report_normal.pdf",
        "content": """
Patient Name: Rahul Sharma
Age: 32
Gender: Male
Report Date: 12-Jan-2026

Complete Blood Count (CBC)

Hemoglobin: 14.8 g/dL (13.0 - 17.0)
RBC Count: 5.1 million/uL (4.5 - 5.9)
WBC Count: 6,500 /uL (4,000 - 11,000)
Platelet Count: 245000 /uL (150000 - 450000)

Blood Sugar (Fasting): 92 mg/dL (70 - 100)
Blood Sugar (Postprandial): 128 mg/dL (< 140)

Serum Creatinine: 0.9 mg/dL (0.7 - 1.3)

Total Cholesterol: 178 mg/dL (< 200)
HDL Cholesterol: 48 mg/dL (> 40)
LDL Cholesterol: 102 mg/dL (< 130)
Triglycerides: 135 mg/dL (< 150)

Remarks: All parameters within normal limits.
"""
    },
    {
        "filename": "report_abnormal.pdf",
        "content": """
Patient Name: Anita Verma
Age: 45
Gender: Female
Report Date: 10-Jan-2026

Hemoglobin: 9.6 g/dL (12.0 - 15.5)
RBC Count: 3.4 million/uL (4.2 - 5.4)
WBC Count: 13800 /uL (4000 - 11000)
Platelet Count: 580000 /uL (150000 - 450000)

Blood Sugar (Fasting): 162 mg/dL (70 - 100)
Blood Sugar (Postprandial): 248 mg/dL (< 140)
HbA1c: 7.8 % (4.0 - 5.6)

Total Cholesterol: 242 mg/dL (< 200)
HDL Cholesterol: 32 mg/dL (> 50)
LDL Cholesterol: 168 mg/dL (< 130)
Triglycerides: 310 mg/dL (< 150)

SGPT (ALT): 86 U/L (7 - 56)
SGOT (AST): 74 U/L (10 - 40)

Remarks: Clinical correlation advised.
"""
    },
    {
        "filename": "report_mixed.pdf",
        "content": """
ABC Diagnostics Laboratory
Report ID: LAB-2026-01982

Patient: Mohit Gupta
Age/Gender: 28 / Male
Collection Date: 15-Jan-2026

HAEMATOLOGY

Hemoglobin (Hb): 12.1 g/dL (13.0 - 17.0)
Total WBC Count: 7.2 x10^3/uL (4.0 - 11.0)
Platelets: 1.32 x10^5/uL (1.5 - 4.5)

BIOCHEMISTRY

Fasting Glucose: 108 mg/dL (70 - 100)
Urea: 24 mg/dL (15 - 40)
Creatinine: 1.4 mg/dL (0.7 - 1.3)

LIPID PROFILE

Total Cholesterol: 196 mg/dL (<200)
HDL: 38 mg/dL (>40)
LDL: 122 mg/dL (<130)
Triglycerides: 182 mg/dL (<150)

Notes:
Mild thrombocytopenia observed.
Borderline fasting glucose levels.
"""
    }
]


def create_pdf(filename: str, text: str):
    filepath = OUTPUT_DIR / filename
    doc = SimpleDocTemplate(str(filepath), pagesize=A4)  # Convert to string

    story = []
    for line in text.strip().split("\n"):
        if line.strip() == "":
            story.append(Spacer(1, 12))
        else:
            story.append(Paragraph(line.replace("&", "&amp;"), styles["Normal"]))
            story.append(Spacer(1, 6))

    doc.build(story)
    print(f"Generated: {filepath}")


def main():
    for report in SAMPLE_REPORTS:
        create_pdf(report["filename"], report["content"])


if __name__ == "__main__":
    main()
