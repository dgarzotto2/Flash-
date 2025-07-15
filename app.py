import os
import sys
import hashlib
import subprocess
import shutil
from pathlib import Path
import tempfile
import requests
import psutil

def sha256sum(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_exe(exe_path, extract_dir):
    print(f"\n📦 Extracting {exe_path} ...")
    try:
        with py7zr.SevenZipFile(exe_path, mode='r') as archive:
            archive.extractall(path=extract_dir)
        print("✅ Extraction complete.\n")
    except Exception as e:
        print(f"❌ Error extracting file: {e}")
        sys.exit(1)

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

def format_usb(usb_path):
    print(f"\n🔧 Formatting USB drive at {usb_path}...")
    try:
        # Format the USB drive (ext4 or FAT32 depending on the OS)
        subprocess.run(["mkfs.vfat", "-F", "32", usb_path], check=True)
        print("✅ USB drive formatted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error formatting USB: {e}")
        sys.exit(1)

def mount_usb(usb_path, mount_point):
    print(f"\n📂 Mounting USB drive at {usb_path} to {mount_point}...")
    try:
        subprocess.run(["mount", usb_path, mount_point], check=True)
        print(f"✅ USB drive mounted at {mount_point}.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error mounting USB: {e}")
        sys.exit(1)

def burn_bios_to_usb(firmwares, usb_mount_point):
    print("\n💾 Burning BIOS to USB...")
    usb_bios_dir = Path(usb_mount_point) / "BIOS"
    usb_bios_dir.mkdir(parents=True, exist_ok=True)

    for f in firmwares:
        shutil.copy2(f, usb_bios_dir / f.name)

    print(f"✅ BIOS files copied to USB at {usb_bios_dir}")

def unmount_usb(usb_mount_point):
    print(f"\n📤 Unmounting USB drive from {usb_mount_point}...")
    try:
        subprocess.run(["umount", usb_mount_point], check=True)
        print("✅ USB unmounted successfully.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error unmounting USB: {e}")
        sys.exit(1)

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

        # Ask for USB device path
        usb_path = input("Enter USB drive path (e.g., /dev/sdb1): ").strip()

        # Format, mount, and burn BIOS to USB
        mount_point = "/mnt/usb"
        format_usb(usb_path)
        mount_usb(usb_path, mount_point)
        burn_bios_to_usb(firmwares, mount_point)
        unmount_usb(mount_point)

        print("\n💡 The BIOS has been successfully burned to the USB drive.")

    else:
        print("⚠️ No firmware files extracted. Nothing to do.")

if __name__ == "__main__":
    main()
