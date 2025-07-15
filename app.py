#!/usr/bin/env python3
import os
import sys
import hashlib
import subprocess
from pathlib import Path
import shutil
import tempfile
import requests

def sha256sum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_exe(exe_path, extract_dir):
    print(f"\n📦 Extracting {exe_path} ...")
    result = subprocess.run(["7z", "x", str(exe_path), f"-o{extract_dir}"], capture_output=True)
    if result.returncode != 0:
        print("❌ Extraction failed:")
        print(result.stderr.decode())
        sys.exit(1)
    print("✅ Extraction complete.\n")

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

def copy_to_output(firmwares, output_dir):
    output_dir.mkdir(exist_ok=True)
    for f in firmwares:
        shutil.copy2(f, output_dir / f.name)
    print(f"\n📤 Firmware copied to: {output_dir}")

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

def main():
    print("📁 BIOS Flash Tool (Headless + Interactive)\n")

    # Ask user for source
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

    # Extract and find firmware
    work_dir = Path("/tmp/bios_extract")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()

    extract_exe(exe_path, work_dir)
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
