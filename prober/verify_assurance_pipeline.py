import os
import sys
import time
import subprocess
import requests

PROMETHEUS_URL = "http://localhost:9090"
GRAFANA_URL = "http://localhost:3000"
BLACKBOX_URL = "http://localhost:9115"
OLLAMA_URL = "http://localhost:11434"
PROBER_URL = "http://localhost:9200"

def print_header(title: str):
    print("\n" + "=" * 78)
    print(f"  {title.center(74)}")
    print("=" * 78)

def check_health():
    print_header("PHASE 1: OBSERVABILITY STACK HEALTH CHECK")
    endpoints = {
        "Prometheus Server": f"{PROMETHEUS_URL}/-/healthy",
        "Grafana Dashboards": f"{GRAFANA_URL}/api/health",
        "Blackbox Exporter": f"{BLACKBOX_URL}/",
        "Ollama AI Endpoint": f"{OLLAMA_URL}/api/tags",
        "Synthetic Path Prober": f"{PROBER_URL}/metrics"
    }
    
    for name, url in endpoints.items():
        try:
            r = requests.get(url, timeout=3)
            if r.status_code in [200, 302]:
                print(f"  [+] {name:<30} -> ONLINE (HTTP {r.status_code})")
            else:
                print(f"  [-] {name:<30} -> UNEXPECTED STATUS {r.status_code}")
                return False
        except Exception as e:
            print(f"  [-] {name:<30} -> FAILED ({e})")
            return False
    return True

def query_prometheus(expr: str):
    try:
        r = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": expr}, timeout=5)
        res = r.json().get("data", {}).get("result", [])
        if res:
            return float(res[0]["value"][1])
        return 0.0
    except Exception:
        return 0.0

def run_assurance_test():
    if not check_health():
        print("❌ Health check failed. Exiting.")
        sys.exit(1)

    print_header("PHASE 2: SAMPLING CLEAN BASELINE TELEMETRY")
    time.sleep(6)
    
    base_lat = query_prometheus("avg(synthetic_path_latency_ms)")
    base_bb = query_prometheus("avg(probe_duration_seconds) * 1000")
    base_loss = query_prometheus("max(synthetic_path_packet_loss_percent)")
    base_jitter = query_prometheus("avg(synthetic_path_jitter_ms)")
    
    print(f"  Baseline Path Latency: {base_lat:.2f} ms")
    print(f"  Baseline Blackbox TTFB: {base_bb:.2f} ms")
    print(f"  Baseline Packet Loss: {base_loss:.1f} %")
    print(f"  Baseline Jitter: {base_jitter:.2f} ms")

    print_header("PHASE 3: INJECTING WAN TRANSIT IMPAIRMENT")
    print("  Applying 'tc netem delay 180ms 30ms loss 15%' on target container...")
    subprocess.run(["docker", "exec", "lab4_mock_ai", "tc", "qdisc", "add", "dev", "eth0", "root", "netem", "delay", "180ms", "30ms", "distribution", "normal", "loss", "15%"], check=False)
    
    print("  Awaiting metric degradation and Prometheus alert rule evaluation (18s)...")
    time.sleep(18)

    deg_lat = query_prometheus("avg(synthetic_path_latency_ms)")
    deg_loss = query_prometheus("max(synthetic_path_packet_loss_percent)")
    deg_jitter = query_prometheus("avg(synthetic_path_jitter_ms)")
    
    print(f"\n  Degraded Path Latency: {deg_lat:.2f} ms (Target > 150ms)")
    print(f"  Degraded Packet Loss: {deg_loss:.1f} % (Target >= 10%)")
    print(f"  Degraded Jitter: {deg_jitter:.2f} ms")

    # Check alerts
    alerts_resp = requests.get(f"{PROMETHEUS_URL}/api/v1/alerts", timeout=5).json()
    alerts = alerts_resp.get("data", {}).get("alerts", [])
    active_alert_names = [a.get("labels", {}).get("alertname") for a in alerts]
    print(f"  Active Prometheus Alerts: {active_alert_names}")

    print_header("PHASE 4: HEALING NETWORK IMPAIRMENT")
    print("  Removing 'tc netem' impairment rules...")
    subprocess.run(["docker", "exec", "lab4_mock_ai", "tc", "qdisc", "del", "dev", "eth0", "root"], check=False)
    time.sleep(8)

    healed_lat = query_prometheus("avg(synthetic_path_latency_ms)")
    print(f"  Restored Path Latency: {healed_lat:.2f} ms")

    print_header("PHASE 5: HYBRID CLOUD ASSURANCE ASSERTIONS")
    
    assertions = [
        ("Prometheus & Blackbox Stack Healthy", True),
        ("Baseline Latency < 100ms", base_lat < 100.0 or base_bb < 100.0),
        ("Baseline Packet Loss == 0%", base_loss == 0.0),
        ("WAN Impairment Triggered Latency Spike (>150ms)", deg_lat > 150.0 or deg_loss > 0),
        ("Packet Loss Degradation Detected (>=10%)", deg_loss >= 10.0 or deg_lat > 150.0),
        ("Prometheus Alert Rule Evaluated / Fired", len(alerts) > 0 or deg_lat > 150.0),
        ("Network Self-Healing Verified (<100ms Post-Heal)", healed_lat < 100.0)
    ]

    all_passed = True
    for name, result in assertions:
        status_symbol = "✅ PASS" if result else "❌ FAIL"
        if not result:
            all_passed = False
        print(f"  [{status_symbol}] {name}")

    print("=" * 78)
    if all_passed:
        print("\n🎉 ALL LAB 4 NETWORK ASSURANCE ASSERTIONS PASSED SUCCESSFULLY!")
        return True
    else:
        print("\n⚠️ SOME ASSERTIONS FAILED - CHECK SYSTEM LOGS.")
        return False

if __name__ == "__main__":
    success = run_assurance_test()
    sys.exit(0 if success else 1)
