#!/usr/bin/env python3
import os
import sys
import hashlib
import subprocess
from pathlib import Path
import shutil
import argparse
import tempfile
import requests

def sha256sum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_exe(exe_path, extract_dir):
    print(f"📦 Extracting {exe_path} ...")
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
    parser = argparse.ArgumentParser(description="Offline BIOS Flash Tool (headless)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--input', '-i', help='Path to local BIOS .exe file')
    group.add_argument('--url', '-u', help='URL to download BIOS .exe from')
    parser.add_argument('--output', '-o', default='bios_output', help='Output directory')
    args = parser.parse_args()

    if args.url:
        temp_dir = tempfile.mkdtemp()
        bios_name = args.url.split("/")[-1]
        exe_path = Path(temp_dir) / bios_name
        download_file(args.url, exe_path)
    else:
        exe_path = Path(args.input).resolve()
        if not exe_path.exists():
            print("❌ BIOS .exe not found.")
            sys.exit(1)

    work_dir = Path("/tmp/bios_extract")
    if work_dir.exists():
        shutil.rmtree(work_dir)
    work_dir.mkdir()

    extract_exe(exe_path, work_dir)
    firmwares = find_firmware(work_dir)
    if firmwares:
        output_dir = Path(args.output)
        copy_to_output(firmwares, output_dir)

        print("\n💡 To launch the BIOS EXE in FreeDOS via QEMU:")
        print(f"""
qemu-system-i386 \\
  -m 256 \\
  -cdrom FD14-full.iso \\
  -hda freedos.img \\
  -boot d \\
  -hdb fat:rw:{output_dir.resolve()} \\
  -nographic

📦 Inside FreeDOS:
  {exe_path.name}
        """)
    else:
        print("⚠️ Nothing to prepare. No firmware found.")

if __name__ == "__main__":
    main()
