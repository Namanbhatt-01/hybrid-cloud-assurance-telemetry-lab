#!/usr/bin/env python3
import json
import time
import subprocess
import requests
from datetime import datetime

PROMETHEUS_URL = "http://localhost:9090"
ALERTMANAGER_URL = "http://localhost:9093"
BLACKBOX_URL = "http://localhost:9115"
PROBER_URL = "http://localhost:9200/metrics"

def query_prometheus(promql: str):
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": promql}, timeout=5)
        return resp.json().get("data", {}).get("result", [])
    except Exception as e:
        return [{"error": str(e)}]

def get_alerts():
    try:
        resp = requests.get(f"{PROMETHEUS_URL}/api/v1/alerts", timeout=5)
        return resp.json().get("data", {}).get("alerts", [])
    except Exception as e:
        return [{"error": str(e)}]

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip()

print(f"[{datetime.utcnow().isoformat()}Z] Starting Live Real-Time Assurance Telemetry Proof Collection")
evidence = {
    "timestamp_utc": datetime.utcnow().isoformat() + "Z",
    "host_system": run_cmd("uname -a"),
    "docker_ps": run_cmd("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"),
    "phases": {}
}

# 1. BASELINE PHASE
print(">> Capturing Phase 1: Clean Baseline Telemetry...")
time.sleep(4)
baseline_latency = query_prometheus("synthetic_path_latency_ms")
baseline_loss = query_prometheus("synthetic_path_packet_loss_percent")
baseline_jitter = query_prometheus("synthetic_path_jitter_ms")
baseline_ttfb = query_prometheus("synthetic_http_ttfb_ms")

evidence["phases"]["baseline"] = {
    "prom_latency_ms": baseline_latency,
    "prom_loss_percent": baseline_loss,
    "prom_jitter_ms": baseline_jitter,
    "prom_ttfb_ms": baseline_ttfb,
    "blackbox_http_probe": requests.get(f"{BLACKBOX_URL}/probe?target=http://lab4_mock_ai:11434/api/generate&module=http_2xx_ai_api").text.splitlines()[:20],
    "active_alerts": get_alerts()
}

# 2. WAN IMPAIRMENT INJECTION
print(">> Capturing Phase 2: Injecting Linux tc netem WAN Impairment (180ms delay, 15% loss)...")
inj_out = run_cmd("bash impairment_injection/simulate_wan_degradation.sh lab4_mock_ai inject")
print(f"Injection output:\n{inj_out}")
print("Awaiting metric degradation and Prometheus alert rule evaluation (18s)...")
time.sleep(18)

impaired_latency = query_prometheus("synthetic_path_latency_ms")
impaired_loss = query_prometheus("synthetic_path_packet_loss_percent")
impaired_jitter = query_prometheus("synthetic_path_jitter_ms")
impaired_ttfb = query_prometheus("synthetic_http_ttfb_ms")
impaired_alerts = get_alerts()

evidence["phases"]["impaired"] = {
    "injection_command_output": inj_out,
    "tc_qdisc_status": run_cmd("docker exec lab4_mock_ai tc -s qdisc show dev eth0"),
    "prom_latency_ms": impaired_latency,
    "prom_loss_percent": impaired_loss,
    "prom_jitter_ms": impaired_jitter,
    "prom_ttfb_ms": impaired_ttfb,
    "active_alerts": impaired_alerts,
    "alertmanager_alerts": requests.get(f"{ALERTMANAGER_URL}/api/v2/alerts").json() if requests.get(f"{ALERTMANAGER_URL}/api/v2/alerts").status_code == 200 else []
}

# 3. SELF-HEALING PHASE
print(">> Capturing Phase 3: Self-Healing Network Remediation...")
heal_out = run_cmd("bash impairment_injection/simulate_wan_degradation.sh lab4_mock_ai heal")
print(f"Healing output:\n{heal_out}")
time.sleep(10)

restored_latency = query_prometheus("synthetic_path_latency_ms")
restored_loss = query_prometheus("synthetic_path_packet_loss_percent")
restored_jitter = query_prometheus("synthetic_path_jitter_ms")
restored_alerts = get_alerts()

evidence["phases"]["restored"] = {
    "healing_command_output": heal_out,
    "tc_qdisc_status": run_cmd("docker exec lab4_mock_ai tc -s qdisc show dev eth0"),
    "prom_latency_ms": restored_latency,
    "prom_loss_percent": restored_loss,
    "prom_jitter_ms": restored_jitter,
    "active_alerts": restored_alerts
}

# Summary Table
evidence["summary_telemetry_table"] = {
    "metric": ["Path Latency (ms)", "Packet Loss (%)", "Jitter (ms)", "Active Alert Count"],
    "baseline": [
        baseline_latency[0].get("value", [0, "0"])[1] if baseline_latency else "N/A",
        baseline_loss[0].get("value", [0, "0"])[1] if baseline_loss else "0",
        baseline_jitter[0].get("value", [0, "0"])[1] if baseline_jitter else "0",
        len(evidence["phases"]["baseline"]["active_alerts"])
    ],
    "degraded_wan": [
        impaired_latency[0].get("value", [0, "0"])[1] if impaired_latency else "N/A",
        impaired_loss[0].get("value", [0, "0"])[1] if impaired_loss else "N/A",
        impaired_jitter[0].get("value", [0, "0"])[1] if impaired_jitter else "N/A",
        len(impaired_alerts)
    ],
    "post_healing": [
        restored_latency[0].get("value", [0, "0"])[1] if restored_latency else "N/A",
        restored_loss[0].get("value", [0, "0"])[1] if restored_loss else "0",
        restored_jitter[0].get("value", [0, "0"])[1] if restored_jitter else "0",
        len(restored_alerts)
    ]
}

with open("poc/live_assurance_telemetry_evidence.json", "w") as f:
    json.dump(evidence, f, indent=2)

print("\n" + "="*80)
print("             REAL-TIME TELEMETRY PROOF SUMMARY             ")
print("="*80)
print(f"  Metric                     Baseline       Degraded WAN       Post-Healing")
print(f"  --------------------------------------------------------------------------")
for i, name in enumerate(evidence["summary_telemetry_table"]["metric"]):
    b = evidence["summary_telemetry_table"]["baseline"][i]
    d = evidence["summary_telemetry_table"]["degraded_wan"][i]
    r = evidence["summary_telemetry_table"]["post_healing"][i]
    print(f"  {name:<25} {str(b):<14} {str(d):<18} {str(r):<12}")
print("="*80)
print(f"\n[+] Active Prometheus Alert Rules Triggered During Degradation:")
for alt in impaired_alerts:
    lbls = alt.get("labels", {})
    state = alt.get("state", "firing")
    print(f"    - Alert: {lbls.get('alertname')} | Severity: {lbls.get('severity')} | State: {state}")

print("\n>> Evidence written to poc/live_assurance_telemetry_evidence.json")
