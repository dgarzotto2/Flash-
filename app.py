import streamlit as st
import os
import requests
import subprocess
from pathlib import Path
import py7zr

# Streamlit only required dependencies
def install_requirements():
    # Ensure Streamlit is installed
    try:
        import streamlit
    except ImportError:
        st.error("Streamlit not found! Installing Streamlit...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit==1.22.0"])
        
def download_file(url, target_path):
    """Download a file from the URL."""
    try:
        st.write(f"Downloading file from {url}...")
        response = requests.get(url)
        response.raise_for_status()  # Raise an error if the download fails
        with open(target_path, 'wb') as f:
            f.write(response.content)
        st.success(f"Download completed: {target_path}")
    except Exception as e:
        st.error(f"Error downloading file: {e}")
        raise

def extract_exe(file_path, extract_dir):
    """Extract the BIOS EXE."""
    try:
        st.write(f"Extracting {file_path} into {extract_dir}...")
        with py7zr.SevenZipFile(file_path, mode='r') as archive:
            archive.extractall(path=extract_dir)
        st.success(f"Extraction complete")
    except Exception as e:
        st.error(f"Error extracting file: {e}")
        raise

def main():
    st.title("BIOS Flash Tool")
    
    # Check if Streamlit is working
    install_requirements()

    # Input URL or Local File Path
    file_choice = st.selectbox("Choose your BIOS file source:", ["Download from URL", "Use Local File"])
    file_path = ""
    
    if file_choice == "Download from URL":
        url = st.text_input("Enter the URL for the BIOS file:")
        if url:
            target_path = Path(f"/tmp/{url.split('/')[-1]}")
            download_file(url, target_path)
            file_path = target_path
    elif file_choice == "Use Local File":
        uploaded_file = st.file_uploader("Upload BIOS .exe file", type=["exe"])
        if uploaded_file:
            target_path = Path(f"/tmp/{uploaded_file.name}")
            with open(target_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            file_path = target_path
    
    # Extract the EXE to a working directory
    if file_path:
        extract_dir = Path(f"/tmp/extracted_bios")
        if not extract_dir.exists():
            os.makedirs(extract_dir)

        extract_exe(file_path, extract_dir)

        st.write(f"Extracted files available at {extract_dir}")
    
    st.write("🚀 Your BIOS Flash Tool is ready!")

if __name__ == "__main__":
    main()
