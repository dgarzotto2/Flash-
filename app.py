import os
import hashlib
import shutil
import tempfile
import requests
import streamlit as st
from pathlib import Path
import subprocess

def sha256sum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_exe(exe_path, extract_dir):
    st.write(f"📦 Extracting {exe_path} ...")
    result = subprocess.run(["7z", "x", str(exe_path), f"-o{extract_dir}"], capture_output=True)
    if result.returncode != 0:
        st.error("❌ Extraction failed:")
        st.text(result.stderr.decode())
        return False
    st.success("✅ Extraction complete.")
    return True

def find_firmware(extract_dir):
    st.write("🔍 Searching for firmware files...")
    firmwares = []
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.lower().endswith(('.fd', '.bin', '.rom', '.cap')):
                firmwares.append(Path(root) / file)
    if not firmwares:
        st.warning("⚠️ No firmware files found.")
    else:
        st.success(f"✅ Found {len(firmwares)} firmware file(s):")
        for fw in firmwares:
            st.write(f"  📁 {fw.name} - SHA256: {sha256sum(fw)}")
    return firmwares

def copy_to_output(firmwares, output_dir):
    output_dir.mkdir(exist_ok=True)
    for f in firmwares:
        shutil.copy2(f, output_dir / f.name)
    st.write(f"\n📤 Firmware copied to: {output_dir}")

def download_file(url, target_path):
    st.write(f"🌐 Downloading BIOS from: {url}")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        st.success(f"✅ Downloaded to: {target_path}")
    except Exception as e:
        st.error(f"❌ Failed to download: {e}")
        return False
    return True

# Streamlit layout configuration
st.title("📁 BIOS Flash Tool (Interactive)")

# Option 1: File Upload (Local File)
uploaded_file = st.file_uploader("Upload BIOS .exe file", type=['exe'])

# Option 2: Download from URL
url_input = st.text_input("Or enter the URL to download BIOS .exe file")

# If the user has selected to download from URL
if url_input:
    if st.button("Download BIOS"):
