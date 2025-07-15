import subprocess
import sys
import os
import streamlit as st

# Function to install packages using pip
def install_package(package_name):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

# Try installing required packages
required_packages = ["streamlit", "py7zr", "rich", "pycryptodomex", "brotli", "psutil", "pyzstd", "pyppmd", "pybcj", "multivolumefile", "inflate64"]

for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        st.warning(f"Package '{package}' not found. Installing...")
        install_package(package)

# After installing, import the packages
import py7zr  # We will use py7zr to extract 7z files
import shutil
import hashlib
import tempfile
import requests
from pathlib import Path

# Function to calculate sha256 checksum
def sha256sum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

# Function to extract .exe files
def extract_exe(exe_path, extract_dir):
    st.write(f"📦 Extracting {exe_path} ...")
    result = subprocess.run(["7z", "x", str(exe_path), f"-o{extract_dir}"], capture_output=True)
    if result.returncode != 0:
        st.error(f"❌ Extraction failed: {result.stderr.decode()}")
        sys.exit(1)
    st.write("✅ Extraction complete.\n")

# Function to find firmware files
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
        st.write(f"✅ Found {len(firmwares)} firmware file(s):\n")
        for fw in firmwares:
            st.write(f"  📁 {fw.name} - SHA256: {sha256sum(fw)}")
    return firmwares

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

def main():
    st.title("📁 BIOS Flash Tool (Headless + Interactive)")

    # Ask user for source
    choice = st.radio("Do you want to:", ("Use a local file", "Download from a URL"))
    if choice == "Use a local file":
        path = st.text_input("Enter path to the BIOS .exe file:")
        exe_path = Path(path).expanduser().resolve()
        if not exe_path.exists():
            st.error("❌ File not found.")
            return
    elif choice == "Download from a URL":
        url = st.text_input("Enter URL to the BIOS .exe file:")
        temp_dir = Path(tempfile.mkdtemp())
        exe_path = temp_dir / url.split("/")[-1]
        download_file(url, exe_path)

    # Ask output path
    output_folder = st.text_input("Enter output directory", "bios_output")
    output_dir = Path(output_folder).resolve()

    # Extract and find firmware
    work_dir = Path("/tmp/bios_extract")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()

    extract_exe(exe_path, work_dir)
    firmwares = find_firmware(work_dir)
    if firmwares:
        # Copy firmware files to output directory
        output_dir.mkdir(exist_ok=True)
        for f in firmwares:
            shutil.copy2(f, output_dir / f.name)
        st.write(f"📤 Firmware copied to: {output_dir}")

        # Display QEMU FreeDOS instructions
        st.write("\n💡 To launch FreeDOS with QEMU and run the BIOS EXE:")
        st.code(f"""
qemu-system-i386 \\
  -m 256 \\
  -cdrom FD14-full.iso \\
  -hda freedos.img \\
  -boot d \\
  -hdb fat:rw:{output_dir} \\
  -nographic

📦 Inside FreeDOS, type:
  {exe_path.name}
        """)
    else:
        st.warning("⚠️ No firmware files extracted. Nothing to do.")

if __name__ == "__main__":
    main()
