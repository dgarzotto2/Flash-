import streamlit as st
import os
import tempfile
import hashlib
import subprocess
from pathlib import Path

st.set_page_config(page_title="BIOS Extractor", layout="wide")
st.title("🧬 HP BIOS Extractor & Verifier")
st.markdown("Upload a BIOS `.exe` file to extract and verify firmware contents.")

uploaded_file = st.file_uploader("📤 Upload HP BIOS .exe", type=["exe"])

if uploaded_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        bios_path = Path(tmpdir) / uploaded_file.name
        with open(bios_path, "wb") as f:
            f.write(uploaded_file.read())
        st.success(f"✅ Uploaded: {uploaded_file.name}")

        # Extract BIOS EXE using 7z
        extract_dir = Path(tmpdir) / "extracted"
        extract_dir.mkdir(exist_ok=True)
        result = subprocess.run(["7z", "x", str(bios_p_]()
