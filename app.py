import os
import subprocess

import streamlit as st
import pandas as pd
from scapy.all import ARP, Ether, srp
import cymruwhois
import shodan
import folium
from folium.plugins import AntPath
from streamlit_folium import st_folium

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MITM Monitor", layout="wide")

# Your Shodan "spirit key"
SHODAN_API_KEY = "K79zhLTXa4jLQ9Mq8jLKZYse4FPQeE1"
API_SHODAN     = shodan.Shodan(SHODAN_API_KEY)

# Cymru WHOIS client for ASN lookups
CYMRU          = cymruwhois.Client()

# Fixed home coordinates (Angeles City, Pampanga)
HOME_LAT, HOME_LON = 15.172488, 120.522452

# LAN scan network
NETWORK        = "192.168.1.0/24"

# Windows Firewall log path
LOG_PATH       = r"C:\Windows\System32\LogFiles\Firewall\pfirewall.log"

# ─── HELPERS ────────────────────────────────────────────────────────────────────
def scan_lan(net=NETWORK, iface=None):
    """ARP-scan your /24 to list nearby devices."""
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=net)
    ans, _ = srp(pkt, timeout=2, iface=iface, verbose=False)
    return [{"IP": r.psrc, "MAC": r.hwsrc} for _, r in ans]

def tail_log(path, lines=200):
    """Return the last N lines of your firewall log containing ALLOW on port 3544."""
    cmd = (
        f"powershell -Command \"Get-Content -Path '{path}' -Tail {lines}\""
    )
    raw = subprocess.getoutput(cmd).splitlines()
    return [l for l in raw if "ALLOW" in l and " 3544 " in l]

def parse_flows(raw_lines):
    """Split each log line into columns, filter for dst_port 3544, cast PID to int."""
    cols = [
        "date","time","action","proto","src_ip","dst_ip",
        "src_port","dst_port","size","tcpflags","tcpsyn","tcpack",
        "tcpwin","icmptype","icmpcode","info","path","pid"
    ]
    df = (
        pd.DataFrame([l.split() for l in raw_lines], columns=cols)
          .query("action=='ALLOW' and dst_port=='3544'")
          .assign(PID=lambda d: d.pid.astype(int))
    )
    return df

def lookup_asn(ip):
    """Return (ASN, Org) via Cymru lookup, or (None,None)."""
    try:
        rec = CYMRU.lookup(ip)
        return rec.asn, rec.owner
    except:
        return None, None

def geo_shodan(ip):
    """Return (lat, lon) via Shodan, or (None,None) on failure."""
    try:
        rec = API_SHODAN.host(ip)
        return rec.get("latitude"), rec.get("longitude")
    except:
        return None, None

# ─── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.title("Controls")

if st.sidebar.button("🔍 Scan LAN"):
    with st.spinner("Scanning LAN…"):
        st.session_state["devices"] = scan_lan()

st.sidebar.markdown("---")

if st.sidebar.button("📜 Tail Teredo Flows"):
    with st.spinner("Reading firewall log…"):
        raw = tail_log(LOG_PATH)
        df = parse_flows(raw)
        # Enrich with ASN & geo
        df["ASN"], df["Org"] = zip(*df.dst_ip.map(lookup_asn))
        df["Lat"], df["Lon"] = zip(*df.dst_ip.map(geo_shodan))
        st.session_state["flows"] = df

# ─── MAIN LAYOUT ──────────────────────────────────────────────────────────────
st.title("MITM Monitor – Streamlined Dashboard")
col1, col2 = st.columns([2,3])

with col1:
    st.subheader("Nearby LAN Devices")
    devices = st.session_state.get("devices", [])
    if devices:
        st.dataframe(pd.DataFrame(devices), height=350)
    else:
        st.info("► Click “Scan LAN” to discover local hosts.")

with col2:
    st.subheader("Recent Teredo Flows (port 3544)")
    flows = st.session_state.get("flows", pd.DataFrame())
    if not flows.empty:
        st.dataframe(
            flows[["date","time","src_ip","dst_ip","path","pid","ASN","Org"]],
            height=350
        )
    else:
        st.info("► Click “Tail Teredo Flows” to load recent tunnel traffic.")

st.markdown("---")
st.subheader("Interactive Flow Map")

# Center the map on your fixed coordinates
center = [HOME_LAT, HOME_LON]
m = folium.Map(location=center, zoom_start=5)

# Mark your location
folium.Marker(
    center,
    tooltip="You",
    icon=folium.Icon(color="blue")
).add_to(m)

# Plot each flow endpoint and draw an arc
for _, r in flows.iterrows():
    if pd.notna(r.Lat) and pd.notna(r.Lon):
        folium.Marker(
            [r.Lat, r.Lon],
            tooltip=f"{r.dst_ip} (ASN {r.ASN})",
            icon=folium.Icon(color="red")
        ).add_to(m)
        AntPath(locations=[center, [r.Lat, r.Lon]], color="red", weight=2).add_to(m)

# Render the map
st_folium(m, width="100%", height=500)