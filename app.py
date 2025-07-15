#!/usr/bin/env python3
import os
import sys
import hashlib
import subprocess
from pathlib import Path
import shutil
import tempfile
import requests

# Function to check if 7z is installed
def check_7z_installed():
    try:
        subprocess.run(["7z", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("❌ 7z (7zip) is not installed. Please install it to proceed.")
        sys.exit(1)

# Function to calculate SHA256 hash
def sha256sum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

# Function to extract the BIOS .exe file using 7z
def extract_exe(exe_path, extract_dir):
    print(f"\n📦 Extracting {exe_path} ...")
    result = subprocess.run(["7z", "x", str(exe_path), f"-o{extract_dir}"], capture_output=True)
    if result.returncode != 0:
        print("❌ Extraction failed:")
        print(result.stderr.decode())
        sys.exit(1)
    print("✅ Extraction complete.\n")

# Function to find firmware files (.fd, .bin, .rom, .cap)
def find_firmware(extract_dir):
    print("🔍 Searching for firmware files...")
    firmwares = []
    for root, _, files in os.walk(extract_dir):
        for file in files:
            if file.lower().endswith(('.fd', '.bin', '.rom', '.cap')):
                firmwares.append(Path(root) / file)
    if not firmwares:
        print("⚠️ No firmware files found.")
    else:
        print(f"✅ Found {len(firmwares)} firmware file(s):\n")
        for fw in firmwares:
            print(f"  📁 {fw.name} - SHA256: {sha256sum(fw)}")
    return firmwares

# Function to copy firmware files to the output directory
def copy_to_output(firmwares, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)
    for f in firmwares:
        shutil.copy2(f, output_dir / f.name)
    print(f"\n📤 Firmware copied to: {output_dir}")

# Function to download BIOS file from a URL
def download_file(url, target_path):
    print(f"🌐 Downloading BIOS from: {url}")
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        with open(target_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"✅ Downloaded to: {target_path}")
    except Exception as e:
        print(f"❌ Failed to download: {e}")
        sys.exit(1)

# Function to verify the integrity of firmware files (optional)
def verify_firmware_integrity(firmware_files, expected_hashes):
    for fw in firmware_files:
        file_hash = sha256sum(fw)
        if file_hash != expected_hashes.get(fw.name, ''):
            print(f"❌ Hash mismatch for {fw.name}: expected {expected_hashes[fw.name]}, found {file_hash}")
            sys.exit(1)
        else:
            print(f"✅ {fw.name} hash verified.")

# Main function to guide the user through the process
def main():
    print("📁 BIOS Flash Tool (Headless + Interactive)\n")

    # Check if 7z is installed
    check_7z_installed()

    # Ask user for source (local file or URL)
    choice = input("Do you want to (1) use a local file or (2) download from a URL? [1/2]: ").strip()
    if choice == '1':
        path = input("Enter path to the BIOS .exe file: ").strip()
        exe_path = Path(path).expanduser().resolve()
        if not exe_path.exists():
            print("❌ File not found.")
            sys.exit(1)
    elif choice == '2':
        url = input("Enter URL to the BIOS .exe file: ").strip()
        temp_dir = Path(tempfile.mkdtemp())
        exe_path = temp_dir / url.split("/")[-1]
        download_file(url, exe_path)
    else:
        print("❌ Invalid choice.")
        sys.exit(1)

    # Ask output path
    output_folder = input("Enter output directory [default: bios_output]: ").strip()
    if not output_folder:
        output_folder = "bios_output"

    output_dir = Path(output_folder).resolve()

    # Temporary working directory for extracting BIOS files
    work_dir = Path("/tmp/bios_extract")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()

    # Extract the BIOS .exe
    extract_exe(exe_path, work_dir)

    # Find the firmware files
    firmwares = find_firmware(work_dir)
    if firmwares:
        copy_to_output(firmwares, output_dir)

        print("\n💡 To launch FreeDOS with QEMU and run the BIOS EXE:")
        print(f"""
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
        print("⚠️ No firmware files extracted. Nothing to do.")

if __name__ == "__main__":
    main()
