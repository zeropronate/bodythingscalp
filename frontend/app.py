import streamlit as st
import requests
import os

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Blood Report Analyzer")

uploaded = st.file_uploader("Upload blood test report (PDF/JPG/PNG)", type=["pdf", "jpg", "jpeg", "png"])

if uploaded is not None:
    if uploaded.size > 10 * 1024 * 1024:
        st.error("File too large. Max 10 MB")
    else:
        if st.button("Analyze"):
            with st.spinner("Analyzing (this may take 1-2 minutes)..."):
                files = {"file": (uploaded.name, uploaded.getvalue())}
                try:
                    resp = requests.post(f"{BACKEND_URL}/analyze", files=files, timeout=120)
                except Exception as e:
                    st.error(f"Request failed: {e}")
                else:
                    if resp.status_code != 200:
                        st.error(f"Error {resp.status_code}: {resp.text}")
                    else:
                        data = resp.json()
                        summary = data.get("summary", {})
                        st.subheader("Summary")
                        st.write(summary)
                        st.subheader("Parameters")
                        for p in data.get("parameters", []):
                            status = p.get("status", "")
                            color = "green" if status == "normal" else "red"
                            st.markdown(f"**{p.get('name','')}**: <span style='color:{color}'>{status.upper()}</span>", unsafe_allow_html=True)
                            st.write({k: v for k, v in p.items() if k not in ("name", "status")})
