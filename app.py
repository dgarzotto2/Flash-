#!/usr/bin/env python3

import os
import sys
import hashlib
import subprocess
from pathlib import Path
import shutil
import tempfile
import requests
import streamlit as st

def sha256sum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_exe(exe_path, extract_dir):
    st.write(f"\n📦 Extracting {exe_path} using Wine...")
    result = subprocess.run([
        "wine", str(exe_path), "/s", f"/extract:{extract_dir}"
    ], capture_output=True)
    if result.returncode != 0:
        st.error("❌ Extraction failed:")
        st.text(result.stderr.decode())
        sys.exit(1)
    st.success("✅ Extraction complete.")

def find_firmware(extract_dir):
    st.write("🔍 Searching for firmware files...")
    firmwares = []
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.lower().endswith(('.fd', '.bin', '.rom', '.cap')):
                path = Path(root) / file
                firmwares.append(path)
    if not firmwares:
        st.warning("⚠️ No firmware files found.")
    else:
        st.success(f"✅ Found {len(firmwares)} firmware file(s):")
        for fw in firmwares:
            st.write(f"📁 `{fw.name}` - SHA256: `{sha256sum(fw)}`")
    return firmwares

def copy_to_output(firmwares, output_dir):
    output_dir.mkdir(exist_ok=True)
    for f in firmwares:
        shutil.copy2(f, output_dir / f.name)
    st.success(f"📤 Firmware copied to: `{output_dir}`")

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
    st.title("📁 BIOS Flash Tool (Wine Extraction + Firmware Finder)")

    option = st.radio("Do you want to:", ("Use a local file", "Download from a URL"))

    file_path = None

    if option == "Use a local file":
        uploaded_file = st.file_uploader("Upload BIOS .exe file", type=['exe'])
        if uploaded_file is not None:
            temp_dir = Path(tempfile.mkdtemp())
            file_path = temp_dir / uploaded_file.name
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())

    elif option == "Download from a URL":
        url = st.text_input("Enter URL to the BIOS .exe file:")
        if url:
            temp_dir = Path(tempfile.mkdtemp())
            file_path = temp_dir / url.split("/")[-1]
            download_file(url, file_path)

    output_folder = st.text_input("Enter output directory", value="bios_output")
    extract_dir = Path(tempfile.mkdtemp())
    output_dir = Path(output_folder).resolve()

    if st.button("Extract BIOS and Find Firmware") and file_path:
        extract_exe(file_path, extract_dir)
        firmwares = find_firmware(extract_dir)
        if firmwares:
            copy_to_output(firmwares, output_dir)
            st.code(f"qemu-system-i386 \\Extracting /tmp/sp93414.exe into /tmp/extracted_bios...

Error extracting file: not a 7z file
Bad7zFile: not a 7z file
Traceback:

File "/home/vscode/.local/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 565, in _run_script
    exec(code, module.__dict__)
File "/workspaces/Flash-/app.py", line 78, in <module>
    main()
File "/workspaces/Flash-/app.py", line 71, in main
    extract_exe(file_path, extract_dir)
File "/workspaces/Flash-/app.py", line 34, in extract_exe
    with py7zr.SevenZipFile(file_path, mode='r') as archive:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/vscode/.local/lib/python3.11/site-packages/py7zr/py7zr.py", line 415, in __init__
    raise e
File "/home/vscode/.local/lib/python3.11/site-packages/py7zr/py7zr.py", line 396, in __init__
    self._real_get_contents(password)
File "/home/vscode/.local/lib/python3.11/site-packages/py7zr/py7zr.py", line 432, in _real_get_contents
    raise Bad7zFile("not a 7z file")Extracting /tmp/sp93414.exe into /tmp/extracted_bios...

Error extracting file: not a 7z file
Bad7zFile: not a 7z file
Traceback:

File "/home/vscode/.local/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py", line 565, in _run_script
    exec(code, module.__dict__)
File "/workspaces/Flash-/app.py", line 78, in <module>
    main()
File "/workspaces/Flash-/app.py", line 71, in main
    extract_exe(file_path, extract_dir)
File "/workspaces/Flash-/app.py", line 34, in extract_exe
    with py7zr.SevenZipFile(file_path, mode='r') as archive:
         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/vscode/.local/lib/python3.11/site-packages/py7zr/py7zr.py", line 415, in __init__
    raise e
File "/home/vscode/.local/lib/python3.11/site-packages/py7zr/py7zr.py", line 396, in __init__
    self._real_get_contents(password)
File "/home/vscode/.local/lib/python3.11/site-packages/py7zr/py7zr.py", line 432, in _real_get_contents
    raise Bad7zFile("not a 7z file")
  -m 256 \\
  -cdrom FD14-full.iso \\
  -hda freedos.img \\
  -boot d \\
  -hdb fat:rw:{output_dir} \\
  -nographic")

if __name__ == "__main__":
    main()
