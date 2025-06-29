# app.py
import streamlit as st
import subprocess
import shlex
import os
from pathlib import Path

st.set_page_config("Live Forensics", layout="wide")
st.title("🕵️‍♂️ Forensics Dump Dashboard")

SCRIPT_PATH = Path(__file__).parent / "forensics_dump.sh"
DUMP_DIR = Path.home() / "Desktop" / "forensics_dump"

def run_dump():
    """Runs the forensics_dump.sh script and yields its stdout in real time."""
    cmd = f"bash {SCRIPT_PATH}"
    with subprocess.Popen(shlex.split(cmd),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT,
                           text=True,
                           bufsize=1) as proc:
        for line in proc.stdout:
            yield line
    return

if st.button("🚀 Run Forensics Dump"):
    st.sidebar.info("Dump started… this can take up to a minute.")
    log_area = st.empty()
    for chunk in run_dump():
        # append each new line
        log_area.text(log_area.text_area("", value="") + chunk)
    st.sidebar.success("✅ Dump complete!")

# If dump dir exists, let user explore it
if DUMP_DIR.exists():
    st.header("🔍 Collected Artifacts")
    files = sorted(DUMP_DIR.glob("*"), key=os.path.getmtime, reverse=True)
    for f in files:
        col1, col2 = st.columns([3,1])
        col1.write(f.name)
        col2.download_button(
            label="Download",
            data=open(f, "rb").read(),
            file_name=f.name
        )
