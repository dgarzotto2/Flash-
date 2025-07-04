import os
import subprocess
import sqlite3
import threading
import time

import streamlit as st
import pandas as pd
import psutil
from scapy.all import ARP, Ether, srp, sniff
import cymruwhois
import shodan
from geopy.geocoders import Nominatim
import folium
from folium.plugins import AntPath
from streamlit_folium import st_folium
from datetime import datetime

# ─── CONFIG & ENV ──────────────────────────────────────────────────────────────
from dotenv import load_dotenv
load_dotenv()  # loads SHODAN_API_KEY from .env

SHODAN_API_KEY = os.getenv("SHODAN_API_KEY")
API_SHODAN     = shodan.Shodan(SHODAN_API_KEY)
CYMRU          = cymruwhois.Client()
GEOCODER       = Nominatim(user_agent="streamlit_mitm_v2")

HOME_LAT, HOME_LON = 15.172488, 120.522452
NETWORK            = "192.168.1.0/24"
LOG_PATH           = r"C:\Windows\System32\LogFiles\Firewall\pfirewall.log"
DB_PATH            = "flows.db"

# ─── DATABASE SETUP ─────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
      CREATE TABLE IF NOT EXISTS flows (
        ts           TEXT,
        src_ip       TEXT,
        dst_ip       TEXT,
        pid          INTEGER,
        exe          TEXT,
        asn          TEXT,
        org          TEXT,
        lat          REAL,
        lon          REAL,
        UNIQUE(ts, src_ip, dst_ip, pid)
      )
    """)
    conn.commit()
    return conn

db = init_db()

# ─── HELPERS ────────────────────────────────────────────────────────────────────
def scan_lan(net=NETWORK):
    pkt = Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=net)
    ans, _ = srp(pkt, timeout=2, verbose=False)
    return [{"IP": r.psrc, "MAC": r.hwsrc} for _, r in ans]

def tail_flows(path, lines=500):
    cmd = f"powershell -Command \"Get-Content '{path}' -Tail {lines}\""
    raw = subprocess.getoutput(cmd).splitlines()
    return [l for l in raw if "ALLOW" in l and " 3544 " in l]

def parse_line(line):
    cols = line.split()
    return {
      "ts":   f"{cols[0]} {cols[1]}",
      "src_ip": cols[4],
      "dst_ip": cols[5],
      "pid":   int(cols[-1]),
    }

def enrich_and_store(records):
    for rec in records:
        # process path lookup
        try:
            proc = psutil.Process(rec["pid"])
            rec["exe"] = proc.exe()
        except:
            rec["exe"] = None

        # ASN & Org
        try:
            a = CYMRU.lookup(rec["dst_ip"])
            rec["asn"], rec["org"] = a.asn, a.owner
        except:
            rec["asn"], rec["org"] = None, None

        # Geo
        try:
            info = API_SHODAN.host(rec["dst_ip"])
            rec["lat"], rec["lon"] = info.get("latitude"), info.get("longitude")
        except:
            rec["lat"], rec["lon"] = None, None

        # write to DB
        c = db.cursor()
        c.execute("""
          INSERT OR IGNORE INTO flows
            (ts, src_ip, dst_ip, pid, exe, asn, org, lat, lon)
          VALUES
            (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(rec[k] for k in ("ts","src_ip","dst_ip","pid","exe","asn","org","lat","lon")))
    db.commit()

def load_flows(limit=1000):
    df = pd.read_sql_query(
      "SELECT * FROM flows ORDER BY ts DESC LIMIT ?", db, params=(limit,)
    )
    df["ts"] = pd.to_datetime(df["ts"])
    return df

def background_sniffer():
    # optional: live UDP‐3544 sniffing—in parallel
    def handler(pkt):
        if pkt.haslayer('UDP') and pkt['UDP'].dport==3544:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            enrich_and_store([{"ts":now, "src_ip":pkt.src, "dst_ip":pkt.dst, "pid":0}])
    sniff(filter="udp port 3544", prn=handler, store=False)

# start background thread
threading.Thread(target=background_sniffer, daemon=True).start()

# ─── STREAMLIT LAYOUT ──────────────────────────────────────────────────────────
st.set_page_config(layout="wide", page_title="MITM Monitor v2")

# auto-refresh every 30s
count = st_autorefresh(interval=30*1000, limit=None, key="refresh")

# Sidebar controls
st.sidebar.title("Controls")
if st.sidebar.button("🔍 Scan LAN"):
    st.session_state["devices"] = scan_lan()

if st.sidebar.button("📜 Refresh Flows"):
    raw = tail_flows(LOG_PATH)
    recs = [parse_line(l) for l in raw]
    enrich_and_store(recs)
    st.sidebar.success("Flows refreshed.")

# Filters
flows_df = load_flows()
asns      = sorted(flows_df["asn"].dropna().unique())
selected  = st.sidebar.multiselect("Filter by ASN", asns, default=asns)

# Main page
st.title("MITM Monitor – Production Forensics Console")
col1, col2 = st.columns([2,3])

with col1:
    st.subheader("Nearby LAN Devices")
    devs = st.session_state.get("devices", [])
    if devs:
        st.dataframe(pd.DataFrame(devs), height=300)
    else:
        st.info("Click “Scan LAN”")

with col2:
    st.subheader("Recent Teredo Flows")
    filt = flows_df[flows_df["asn"].isin(selected)]
    st.dataframe(
      filt[["ts","src_ip","dst_ip","exe","pid","asn","org"]],
      height=300
    )
    st.line_chart(
      filt.set_index("ts").resample("1Min").size(),
      height=150,
      use_container_width=True,
      title="Flows per Minute"
    )

st.markdown("---")
st.subheader("Flow Map")
center = [HOME_LAT, HOME_LON]
m = folium.Map(location=center, zoom_start=4)
folium.Marker(center, tooltip="You", icon=folium.Icon(color="blue")).add_to(m)

for _, r in filt.iterrows():
    if pd.notna(r.lat) and pd.notna(r.lon):
        folium.Marker(
            [r.lat, r.lon],
            tooltip=f"{r.dst_ip} (ASN {r.asn})",
            icon=folium.Icon(color="red")
        ).add_to(m)
        AntPath(locations=[center, [r.lat, r.lon]], color="red", weight=2).add_to(m)

st_folium(m, width="100%", height=450)