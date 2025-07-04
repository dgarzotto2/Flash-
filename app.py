import os
import subprocess

import streamlit as st
import pandas as pd
from scapy.all import ARP, Ether, srp
import cymruwhois
import shodan
from geopy.geocoders import Nominatim
import folium
from folium.plugins import AntPath
from streamlit_folium import st_folium

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="MITM Monitor", layout="wide")
SHODAN_API_KEY = "K79zhLTXa4jLQZ9Mq8jLKZYse4FPQeE1"
API_SHODAN     = shodan.Shodan(SHODAN_API_KEY)
GEOCODER       = Nominatim(user_agent="streamlit_mitm")
CYMRU          = cymruwhois.Client()
LOG_PATH       = r"C:\Windows\System32\LogFiles\Firewall\pfirewall.log"
YOUR_LOCATION  = GEOCODER.geocode("MehrMau Apartments, Angeles City, Pampanga, Philippines")
NETWORK        = "192.168.1.0/24"

# ─── HELPERS ────────────────────────────────────────────────────────────────────
def scan_lan(net=NETWORK, iface=None):
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=net)
    ans, _ = srp(pkt, timeout=2, iface=iface, verbose=False)
    return [{"IP": r.psrc, "MAC": r.hwsrc} for _, r in ans]

def tail_log(path, lines=200):
    cmd = f"powershell -Command \"Get-Content -Path '{path}' -Tail {lines}\""
    raw = subprocess.getoutput(cmd).splitlines()
    return [l for l in raw if "ALLOW" in l and " 3544 " in l]

def parse_flows(raw_lines):
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
    try:
        r = CYMRU.lookup(ip)
        return r.asn, r.owner
    except:
        return None, None

def geo_shodan(ip):
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
        lines = tail_log(LOG_PATH)
        df = parse_flows(lines)
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

# Center the map on your location
center = [YOUR_LOCATION.latitude, YOUR_LOCATION.longitude]
m = folium.Map(location=center, zoom_start=5)

# Mark your location
folium.Marker(center, tooltip="You", icon=folium.Icon(color="blue")).add_to(m)

# Plot each Teredo flow endpoint
for _, r in flows.iterrows():
    if pd.notna(r.Lat) and pd.notna(r.Lon):
        folium.Marker(
            [r.Lat, r.Lon],
            tooltip=f"{r.dst_ip} (ASN {r.ASN})",
            icon=folium.Icon(color="red")
        ).add_to(m)
        AntPath(locations=[center, [r.Lat, r.Lon]], color="red", weight=2).add_to(m)

st_folium(m, width="100%", height=500)