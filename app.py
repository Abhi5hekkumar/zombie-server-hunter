from __future__ import annotations

import io
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import pandas as pd
import requests
import streamlit as st
from core import classify, savings

APP_NAME = "Zombie Server Hunter"
PROM_URL_DEFAULT = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

st.set_page_config(page_title=APP_NAME, page_icon="🧟", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
:root { --zh-blue:#1a73e8; --zh-ink:#202124; --zh-muted:#5f6368; --zh-line:#dadce0; --zh-bg:#f8fafd; }
html, body, [class*="css"] { font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.stApp { background: #f8fafd; color: var(--zh-ink); }
.block-container { max-width: 1440px; padding-top: 4.25rem !important; padding-bottom: 2.5rem; }
[data-testid="stHeader"] { background: rgba(248,250,253,.96); height: 3.25rem; }
[data-testid="stToolbar"] { right: 1rem; }
[data-testid="stAppViewContainer"] > .main { overflow: visible; }
[data-testid="stSidebar"] { background:#fff; border-right:1px solid #e8eaed; }
[data-testid="stSidebar"] > div:first-child { padding-top:1.2rem; }
[data-testid="stMetric"] { background:#fff; border:1px solid #e8eaed; padding:1rem 1.1rem; border-radius:14px; box-shadow:0 1px 2px rgba(60,64,67,.04); }
[data-testid="stMetricLabel"] { color:#5f6368; font-size:.82rem; font-weight:600; }
[data-testid="stMetricValue"] { color:#202124; font-size:1.75rem; font-weight:700; }
h1,h2,h3 { color:#202124; letter-spacing:-.035em; }
h1 { font-size:2rem !important; font-weight:750 !important; }
h2 { font-size:1.3rem !important; font-weight:700 !important; }
h3 { font-size:1.05rem !important; font-weight:650 !important; }
p, li { color:#3c4043; }
[data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid #e8eaed; border-radius:12px; overflow:hidden; }
.stButton > button, .stDownloadButton > button { border-radius:999px; border:1px solid #dadce0; padding:.55rem 1rem; font-weight:600; background:#fff; color:#1a73e8; transition:all .15s ease; }
.stButton > button:hover, .stDownloadButton > button:hover { border-color:#1a73e8; color:#174ea6; background:#f1f6fe; }
.stDownloadButton > button { background:#1a73e8; color:#fff; border-color:#1a73e8; }
.stDownloadButton > button:hover { background:#174ea6; color:#fff; }
div[data-baseweb="select"] > div, div[data-baseweb="input"] > div { border-radius:9px; }
[data-testid="stAlert"] { border-radius:12px; }
hr { border-color:#e8eaed; }
.zh-topbar { display:flex; justify-content:space-between; align-items:center; gap:20px; padding:0 0 .9rem; border-bottom:1px solid #e8eaed; margin-bottom:1.1rem; min-height:54px; box-sizing:border-box; }
.zh-brand { display:flex; align-items:center; gap:12px; }
.zh-logo { width:42px; height:42px; border-radius:13px; display:flex; align-items:center; justify-content:center; background:#e8f0fe; color:#1967d2; }
.zh-name { font-size:1.1rem; font-weight:750; letter-spacing:-.025em; color:#202124; }
.zh-subname { font-size:.75rem; color:#5f6368; margin-top:2px; }
.zh-pill { font-size:.75rem; color:#137333; background:#e6f4ea; border:1px solid #ceead6; padding:6px 10px; border-radius:999px; font-weight:650; white-space:nowrap; }
.zh-hero { padding:1.25rem 1.4rem; background:linear-gradient(115deg,#fff 0%,#f1f6fe 100%); border:1px solid #e8eaed; border-radius:16px; margin-bottom:.9rem; }
.zh-eyebrow { font-size:.72rem; text-transform:uppercase; letter-spacing:.12em; color:#1967d2; font-weight:750; margin-bottom:.5rem; }
.zh-hero-title { font-size:clamp(1.35rem, 2.2vw, 1.85rem); font-weight:750; letter-spacing:-.04em; line-height:1.22; color:#202124; margin:0 0 .45rem; overflow-wrap:anywhere; }
.zh-hero-copy { color:#5f6368; font-size:.9rem; max-width:900px; line-height:1.55; margin:0; }
.zh-note { font-size:.8rem; color:#5f6368; margin-top:.8rem; }
.zh-section { margin-top:1.25rem; }
@media (max-width: 900px) { .block-container { padding-left:1.25rem; padding-right:1.25rem; } .zh-topbar { flex-wrap:wrap; } }
@media (max-width: 700px) { .block-container { padding-top:3.8rem !important; padding-left:1rem; padding-right:1rem; } .zh-topbar { align-items:flex-start; } .zh-pill { display:none; } .zh-hero { padding:1.1rem; } .zh-hero-title { font-size:1.35rem; } }

</style>
<div class="zh-topbar">
  <div class="zh-brand">
    <div class="zh-logo">
      <svg width="25" height="25" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path d="M4 17.5V6.5l8 6 8-6v11" stroke="#1967d2" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M7.5 17.5h9" stroke="#1967d2" stroke-width="2" stroke-linecap="round"/>
        <circle cx="12" cy="4.5" r="2" fill="#34a853"/>
      </svg>
    </div>
    <div><div class="zh-name">Zombie Server Hunter</div><div class="zh-subname">Infrastructure efficiency console</div></div>
  </div>
  <div class="zh-pill">● Local-first · Free & open source</div>
</div>
<div class="zh-hero">
  <div class="zh-eyebrow">Fleet intelligence</div>
  <div class="zh-hero-title">Find idle infrastructure. Make every watt count.</div>
  <p class="zh-hero-copy">Identify servers with sustained low activity, prioritize candidates for engineering review, and model potential monthly energy, cost and carbon savings from one clear workspace.</p>
  <div class="zh-note">Recommendations are investigation signals—not proof that a server is safe to shut down.</div>
</div>
""", unsafe_allow_html=True)


def demo_data() -> pd.DataFrame:
    """Deterministic demo inventory. Values are illustrative, never real measurements."""
    rows = [
        {"instance": "api-node-01:9100", "cpu_avg_pct": 2.2, "cpu_p95_pct": 5.1, "memory_avg_pct": 28, "network_avg_kbps": 1.8, "disk_avg_kbps": 0.4, "uptime_days": 46, "role": "unknown"},
        {"instance": "batch-worker-03:9100", "cpu_avg_pct": 3.8, "cpu_p95_pct": 8.7, "memory_avg_pct": 42, "network_avg_kbps": 2.4, "disk_avg_kbps": 1.2, "uptime_days": 19, "role": "unknown"},
        {"instance": "db-replica-02:9100", "cpu_avg_pct": 1.4, "cpu_p95_pct": 3.2, "memory_avg_pct": 76, "network_avg_kbps": 24, "disk_avg_kbps": 18, "uptime_days": 120, "role": "database-replica"},
        {"instance": "web-prod-04:9100", "cpu_avg_pct": 26.4, "cpu_p95_pct": 68.2, "memory_avg_pct": 63, "network_avg_kbps": 82, "disk_avg_kbps": 34, "uptime_days": 63, "role": "unknown"},
        {"instance": "old-staging-01:9100", "cpu_avg_pct": 0.7, "cpu_p95_pct": 1.8, "memory_avg_pct": 19, "network_avg_kbps": 0.2, "disk_avg_kbps": 0.1, "uptime_days": 91, "role": "staging"},
        {"instance": "security-monitor-01:9100", "cpu_avg_pct": 1.1, "cpu_p95_pct": 4.1, "memory_avg_pct": 35, "network_avg_kbps": 13, "disk_avg_kbps": 2.1, "uptime_days": 78, "role": "security"},
    ]
    return pd.DataFrame(rows)


def prom_query_range(base_url: str, query: str, start: datetime, end: datetime, step: str) -> list[dict[str, Any]]:
    url = base_url.rstrip("/") + "/api/v1/query_range"
    response = requests.get(url, params={
        "query": query,
        "start": start.timestamp(),
        "end": end.timestamp(),
        "step": step,
    }, timeout=20)
    response.raise_for_status()
    payload = response.json()
    if payload.get("status") != "success":
        raise RuntimeError(payload.get("error", "Prometheus query failed"))
    return payload.get("data", {}).get("result", [])


def series_stats(base_url: str, query: str, start: datetime, end: datetime, step: str) -> dict[str, dict[str, float]]:
    series = prom_query_range(base_url, query, start, end, step)
    output: dict[str, dict[str, float]] = {}
    for item in series:
        labels = item.get("metric", {})
        instance = labels.get("instance") or labels.get("nodename") or "unknown"
        values = []
        for point in item.get("values", []):
            try:
                value = float(point[1])
                if pd.notna(value) and value >= 0:
                    values.append(value)
            except (ValueError, TypeError, IndexError):
                continue
        if values:
            output[instance] = {"avg": sum(values) / len(values), "p95": float(pd.Series(values).quantile(.95))}
    return output


def fetch_live_data(base_url: str, hours: int, step_minutes: int) -> pd.DataFrame:
    end = datetime.now(timezone.utc)
    start = end - timedelta(hours=hours)
    step = f"{step_minutes * 60}s"
    # PromQL is evaluated across the requested window via the Prometheus range-query API.
    cpu = series_stats(base_url, '100 * (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))', start, end, step)
    memory = series_stats(base_url, '100 * (1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes))', start, end, step)
    network = series_stats(base_url, 'sum by (instance) (rate(node_network_receive_bytes_total[5m]) + rate(node_network_transmit_bytes_total[5m]))', start, end, step)
    disk = series_stats(base_url, 'sum by (instance) (rate(node_disk_read_bytes_total[5m]) + rate(node_disk_written_bytes_total[5m]))', start, end, step)
    uptime = series_stats(base_url, 'time() - node_boot_time_seconds', start, end, step)
    instances = sorted(set(cpu) | set(memory) | set(network) | set(disk))
    rows = []
    for instance in instances:
        rows.append({
            "instance": instance,
            "cpu_avg_pct": round(cpu.get(instance, {}).get("avg", 100), 2),
            "cpu_p95_pct": round(cpu.get(instance, {}).get("p95", 100), 2),
            "memory_avg_pct": round(memory.get(instance, {}).get("avg", 100), 2),
            "network_avg_kbps": round(network.get(instance, {}).get("avg", 0) / 1024, 3),
            "disk_avg_kbps": round(disk.get(instance, {}).get("avg", 0) / 1024, 3),
            "uptime_days": round(uptime.get(instance, {}).get("avg", 0) / 86400, 1),
            "role": "unknown",
        })
    if not rows:
        raise RuntimeError("No matching node_exporter metrics found. Check the scrape target and metric names.")
    return pd.DataFrame(rows)



with st.sidebar:
    st.markdown("### Workspace settings")
    st.caption("Choose your data source and tune the analysis.")
    mode = st.radio("Data source", ["Demo data (free, no server needed)", "Live Prometheus"], index=0)
    prom_url = st.text_input("Prometheus URL", PROM_URL_DEFAULT, disabled=mode.startswith("Demo"))
    window_hours = st.select_slider("Observation window", options=[6, 12, 24, 48, 72, 168], value=24, format_func=lambda x: f"{x} hours" if x < 168 else "7 days")
    step_minutes = st.select_slider("Query resolution", options=[1, 5, 10, 15], value=5, format_func=lambda x: f"{x} min")
    st.divider()
    st.markdown("### Detection rules")
    cpu_threshold = st.slider("Average CPU max (%)", 0.5, 15.0, 5.0, 0.5)
    p95_threshold = st.slider("CPU p95 max (%)", 1.0, 30.0, 15.0, 1.0)
    memory_threshold = st.slider("Average memory max (%)", 10.0, 80.0, 70.0, 5.0)
    network_threshold = st.number_input("Network max (KB/s)", 0.0, 1000.0, 10.0, 1.0)
    disk_threshold = st.number_input("Disk I/O max (KB/s)", 0.0, 1000.0, 10.0, 1.0)
    min_hours = st.number_input("Minimum observation window for higher confidence (hours)", 1, 168, 24, 6)
    st.divider()
    st.markdown("### Savings model")
    watts = st.number_input("Estimated average server power (W)", 10.0, 2000.0, 250.0, 10.0, help="Use measured power if available. This is not inferred from CPU utilization.")
    pue = st.number_input("Datacenter PUE multiplier", 1.0, 3.0, 1.5, 0.05, help="Set to 1.0 for no cooling/overhead multiplier.")
    hours_month = st.number_input("Hours per month", 1.0, 744.0, 730.0, 1.0)
    price = st.number_input("Electricity price per kWh", 0.0, 1000.0, 8.0, 0.25)
    carbon = st.number_input("Grid carbon intensity (kg CO₂/kWh)", 0.0, 3.0, 0.70, 0.01, help="Editable assumption. Replace with a current, region-specific published factor for reporting.")

try:
    if mode.startswith("Demo"):
        data = demo_data()
        source_note = "Illustrative synthetic data — not connected to a real fleet."
    else:
        data = fetch_live_data(prom_url, int(window_hours), int(step_minutes))
        source_note = f"Live Prometheus metrics queried over the last {window_hours} hours. Role labels are not inferred; unknown roles are treated conservatively."
except Exception as exc:
    st.error(f"Could not load metrics: {exc}")
    st.info("For live mode, confirm Prometheus is reachable from this app and node_exporter targets are being scraped. Demo mode works without a Prometheus server.")
    st.stop()

results = data.copy()
classified = results.apply(lambda row: classify(row, cpu_threshold, p95_threshold, memory_threshold, network_threshold, disk_threshold, int(window_hours), int(min_hours)), axis=1)
results[["status", "reason", "confidence_score"]] = pd.DataFrame(classified.tolist(), index=results.index)
results["confidence"] = results["confidence_score"].map({3: "Higher", 2: "Medium", 1: "Low"})
assumptions = results.apply(lambda row: savings(row, watts, pue, hours_month, price, carbon), axis=1, result_type="expand")
results = pd.concat([results, assumptions], axis=1)
results["monthly_kwh"] = results["monthly_kwh"].round(1)
results["monthly_cost"] = results["monthly_cost"].round(2)
results["monthly_co2_kg"] = results["monthly_co2_kg"].round(2)
results["review_recommended"] = results["status"].isin(["High-priority candidate", "Candidate — more history needed", "Protected role — review"])

candidates = results[results["status"].isin(["High-priority candidate", "Candidate — more history needed"])]
monthly_kwh = float(candidates["monthly_kwh"].sum())
monthly_cost = float(candidates["monthly_cost"].sum())
monthly_co2 = float(candidates["monthly_co2_kg"].sum())

st.caption("DATA SOURCE  ·  " + source_note)
if mode.startswith("Demo"):
    st.warning("Demo mode is for validating the workflow. Do not present its figures as measured savings.")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Servers scanned", f"{len(results):,}")
m2.metric("Candidates to review", f"{len(candidates):,}")
m3.metric("Potential energy / month", f"{monthly_kwh:,.1f} kWh")
m4.metric("Potential monthly savings", f"₹{monthly_cost:,.0f}")
st.metric("Potential avoided emissions / month", f"{monthly_co2:,.1f} kg CO₂", help="Scenario estimate based on editable power, PUE and grid-intensity assumptions.")

left, right = st.columns([1.3, 1])
with left:
    st.subheader("Fleet activity")
    chart_df = results.set_index("instance")[["cpu_avg_pct", "cpu_p95_pct", "memory_avg_pct"]]
    st.bar_chart(chart_df, height=300)
with right:
    st.subheader("Findings summary")
    counts = results["status"].value_counts().rename_axis("Status").reset_index(name="Servers")
    st.dataframe(counts, use_container_width=True, hide_index=True)

st.subheader("Server inventory & findings")
show_cols = ["instance", "role", "status", "confidence", "cpu_avg_pct", "cpu_p95_pct", "memory_avg_pct", "network_avg_kbps", "disk_avg_kbps", "uptime_days", "monthly_kwh", "monthly_cost", "monthly_co2_kg"]
view = results[show_cols].rename(columns={
    "instance": "Instance", "role": "Role", "status": "Finding", "confidence": "Confidence",
    "cpu_avg_pct": "CPU avg %", "cpu_p95_pct": "CPU p95 %", "memory_avg_pct": "Memory avg %",
    "network_avg_kbps": "Network KB/s", "disk_avg_kbps": "Disk KB/s", "uptime_days": "Uptime days",
    "monthly_kwh": "Est. kWh/month", "monthly_cost": "Est. ₹/month", "monthly_co2_kg": "Est. kg CO₂/month"
})
st.dataframe(view, use_container_width=True, hide_index=True)

with st.expander("Why was a server flagged?", expanded=True):
    for _, row in results.iterrows():
        if row["review_recommended"]:
            st.markdown(f"**{row['instance']} — {row['status']}**\n\n{row['reason']}")

st.subheader("Operational safety checklist")
st.markdown("""
- [ ] Confirm the service owner and business purpose.
- [ ] Check scheduled jobs, month-end/batch workloads and seasonal traffic.
- [ ] Verify redundancy, failover, disaster-recovery and compliance requirements.
- [ ] Review application dependencies, alerts, logs and deployment configuration.
- [ ] Validate power assumptions against measured server or rack power where possible.
- [ ] Test in staging and use an approved change window; do not automate shutdown from this report.
""")

report = results.copy()
report["analysis_window_hours"] = int(window_hours)
report["data_source"] = "demo" if mode.startswith("Demo") else "prometheus"
report["power_assumption_watts"] = watts
report["pue_assumption"] = pue
report["hours_per_month_assumption"] = hours_month
report["electricity_price_per_kwh"] = price
report["carbon_intensity_kg_per_kwh"] = carbon
csv = report.to_csv(index=False).encode("utf-8")
st.download_button("↓  Export findings (CSV)", data=csv, file_name=f"zombie-server-hunter-{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv")

st.caption("Estimates assume the candidate server is fully powered down for the modeled hours. They exclude migration costs, service impact, embodied carbon, and possible shared-capacity effects. Actual savings depend on measured power draw and operational decisions.")

