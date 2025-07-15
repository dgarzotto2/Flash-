import subprocess
import sys

# Function to install the required package if not already installed
def install(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError as e:
        print(f"Error installing {package}: {e}")
        sys.exit(1)

# Install required dependencies
install('py7zr')
install('requests')
install('streamlit')

# Now, proceed with the rest of your Streamlit app code
import streamlit as st
import py7zr
import os
from pathlib import Path
import shutil
import tempfile
import hashlib

# Function to compute the SHA256 hash of a file
def sha256sum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

# Function to extract the BIOS .exe file using py7zr
def extract_exe(exe_path, extract_dir):
    st.write(f"📦 Extracting {exe_path} ...")
    try:
        with py7zr.SevenZipFile(exe_path, mode='r') as z:
            z.extractall(path=extract_dir)
        st.write("✅ Extraction complete.")
    except Exception as e:
        st.error(f"❌ Extraction failed: {e}")
        sys.exit(1)

# Function to find firmware files in the extracted directory
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
        st.write(f"✅ Found {len(firmwares)} firmware file(s):")
        for fw in firmwares:
            st.write(f"  📁 {fw.name} - SHA256: {sha256sum(fw)}")
    return firmwares

# Function to copy the firmware files to the output directory
def copy_to_output(firmwares, output_dir):
    output_dir.mkdir(exist_ok=True)
    for f in firmwares:
        shutil.copy2(f, output_dir / f.name)
    st.write(f"📤 Firmware copied to: {output_dir}")

# Function to download a file from a URL
def download_file(url, target_path):
    st.write(f"🌐 Downloading BIOS from: {url}")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        st.write(f"✅ Downloaded to: {target_path}")
    except Exception as e:
        st.error(f"❌ Failed to download: {e}")
        sys.exit(1)

# Main Streamlit app function
def main():
