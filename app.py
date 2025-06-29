# app.py
import streamlit as st
import subprocess, shlex
import tempfile, os
from datetime import datetime
from pathlib import Path

@st.cache_data
def prepare_dump_script():
    # Build your old bash script inline:
    dump = r"""#!/usr/bin/env bash
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
OUTDIR="$HOME/Desktop/forensics_$TIMESTAMP"
mkdir -p "$OUTDIR"

ss -tulpan  > "$OUTDIR/network_$TIMESTAMP.txt"
ps auxf       > "$OUTDIR/processes_$TIMESTAMP.txt"
timeout 60 tcpdump -i "$(ip route|awk '/default/ {print $5}')" -w "$OUTDIR/traffic_$TIMESTAMP.pcap"
journalctl -xe> "$OUTDIR/journal_$TIMESTAMP.txt"
dmesg        > "$OUTDIR/dmesg_$TIMESTAMP.txt"
mount        > "$OUTDIR/mounts_$TIMESTAMP.txt"
ip addr      > "$OUTDIR/ips_$TIMESTAMP.txt"
ip route     > "$OUTDIR/routes_$TIMESTAMP.txt"
ip neigh     > "$OUTDIR/arp_$TIMESTAMP.txt"
chmod -R 600 "$OUTDIR"
echo "Dump complete in $OUTDIR"
"""
    tf = Path(tempfile.gettempdir()) / "forensics_dump.sh"
    tf.write_text(dump)
    tf.chmod(0o700)
    return str(tf)

st.title("Forensics Dump Dashboard")

if st.button("🚀 Run Forensics Dump"):
    script = prepare_dump_script()
    # Run it and stream output
    proc = subprocess.Popen(shlex.split(script), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    for line in proc.stdout:
        st.text(line)
    proc.wait()
    if proc.returncode == 0:
        st.success("All done!")
    else:
        st.error(f"Exited with {proc.returncode}")
