import os
import sys
import hashlib
import subprocess
from pathlib import Path
import shutil
import tempfile
import requests
import py7zr  # Added for 7z extraction

def sha256sum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_exe(exe_path, extract_dir):
    st.write(f"📦 Extracting {exe_path} ...")
    
    try:
        # Use py7zr to extract 7z files
        with py7zr.SevenZipFile(exe_path, mode='r') as archive:
            archive.extractall(path=str(extract_dir))
        st.success("✅ Extraction complete.\n")
    except Exception as e:
        st.error(f"❌ Extraction failed: {e}")
        sys.exit(1)

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
        st.success(f"✅ Found {len(firmwares)} firmware file(s):\n")
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
        sys.exit(1)

def main():
    st.title("📁 BIOS Flash Tool (Headless + Interactive)\n")

    # Ask user for source
    choice = st.radio("Do you want to:", ['Use a local file', 'Download from a URL'])
    
    if choice == 'Use a local file':
        path = st.text_input("Enter path to the BIOS .exe file:")
        exe_pat_
