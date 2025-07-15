#!/usr/bin/env python3
import os
import sys
import hashlib
import subprocess
from pathlib import Path
import shutil
import argparse

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

def main():
    parser = argparse.ArgumentParser(description="Offline BIOS Flash Tool (headless)")
    parser.add_argument('--input', '-i', required=True, help='Path to BIOS .exe file')
    parser.add_argument('--output', '-o', default='bios_output', help='Output directory')
    args = parser.parse_args()

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

        print("\n💡 You can run the BIOS EXE inside FreeDOS using QEMU like this:")
        print(f"""
qemu-system-i386 \\
  -m 256 \\
  -cdrom FD14-full.iso \\
  -hda freedos.img \\
  -boot d \\
  -hdb fat:rw:{output_dir.resolve()} \\
  -nographic

📦 Then run this inside FreeDOS:
  {exe_path.name}
        """)
    else:
        print("⚠️ Nothing to prepare. No firmware found.")

if __name__ == "__main__":
    main()
