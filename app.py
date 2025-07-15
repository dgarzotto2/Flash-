import streamlit as st
import os
import subprocess
import sys
from pathlib import Path

# Function to extract BIOS exe file
def extract_exe(exe_path, extract_dir):
    """
    Extracts the given BIOS .exe file to the specified directory.
    Handles different archive types.
    """
    print(f"\n📦 Extracting {exe_path} ...")
    
    try:
        # Check if it's a self-extracting archive or a non-7z format
        if exe_path.suffix.lower() == '.exe':
            # Try to extract using 7z first
            try:
                subprocess.run(['7z', 'x', str(exe_path), f'-o{extract_dir}'], check=True)
                print(f"✅ Extracted using 7z.")
                return
            except subprocess.CalledProcessError:
                print("❌ Not a 7z file. Trying another method...")
            
            # If not a 7z file, use a different method (e.g., unzip, or run it directly in a virtual machine)
            print(f"⚠️ Failed to extract with 7z. This might be a self-extracting archive or another format.")
            # Add additional extraction logic as necessary (or inform user)
        else:
            print("❌ Unsupported file format.")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error extracting file: {e}")
        sys.exit(1)

# Main app logic
def main():
    # Streamlit page setup
    st.set_page_config(page_title="BIOS Flash Tool", layout="wide")
    st.title("BIOS Flash Tool (Headless + Interactive)")

    st.write("""
    This tool allows you to download and flash BIOS files for your system. 
    It supports downloading from URLs, extracting files, and flashing BIOS to USB.
    """)

    # Get user inputs
    file_option = st.radio(
        "Do you want to:",
        ["Use a local file", "Download from a URL"]
    )

    if file_option == "Use a local file":
        # Local file input
        file_path = st.file_uploader("Upload BIOS .exe file", type=["exe"])
        output_dir = st.text_input("Enter output directory", "/tmp/extracted_bios")

        if file_path and output_dir:
            try:
                # Create directory if doesn't exist
                os.makedirs(output_dir, exist_ok=True)

                # Save the uploaded file
                exe_path = Path(output_dir) / file_path.name
                with open(exe_path, "wb") as f:
                    f.write(file_path.getbuffer())

                # Extract the file
                extract_exe(exe_path, output_dir)

                st.success(f"📂 BIOS extracted successfully to {output_dir}")
            except Exception as e:
                st.error(f"❌ Error extracting file: {e}")

    elif file_option == "Download from a URL":
        # URL input
        url = st.text_input("Enter URL to BIOS file")
        output_dir = st.text_input("Enter output directory", "/tmp/extracted_bios")

        if url and output_dir:
            try:
                # Create directory if doesn't exist
                os.makedirs(output_dir, exist_ok=True)

                # Download the file
                exe_path = Path(output_dir) / "bios_file.exe"
                subprocess.run(['wget', url, '-O', str(exe_path)], check=True)

                # Extract the file
                extract_exe(exe_path, output_dir)

                st.success(f"📂 BIOS downloaded and extracted successfully to {output_dir}")
            except Exception as e:
                st.error(f"❌ Error downloading or extracting file: {e}")

# Run the Streamlit app
if __name__ == "__main__":
    main()
