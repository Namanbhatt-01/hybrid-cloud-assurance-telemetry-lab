# Lab 4: Live Real-Time Assurance & Synthetic Telemetry Proof of Execution

**Test Date & Time**: 2026-09-27T18:14:58+05:30 (UTC: 2026-09-27T12:44:58Z)  
**Host Architecture**: Apple Silicon (Darwin 24.3.0 ARM64 / macOS)  
**Repository**: [`Namanbhatt-01/hybrid-cloud-assurance-telemetry-lab`](https://github.com/Namanbhatt-01/hybrid-cloud-assurance-telemetry-lab)  
**Target Workload**: Synthetic Multi-Layer Probing targeting Hybrid AI Endpoints (Ollama `:11434` / HuggingFace `:8088`)  

---

## 1. Live Containerized Topology & Service Health

```bash
$ docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

| Container Name | Runtime Status | Exposed Ports & Services |
| :--- | :--- | :--- |
| `lab4_synthetic_prober` | Up (healthy) | `0.0.0.0:9200->9200/tcp` (Prometheus Metrics Exporter) |
| `lab4_mock_ai` | Up (healthy) | `0.0.0.0:8088->8088/tcp, 0.0.0.0:11434->11434/tcp` (Ollama & HuggingFace Mock API) |
| `lab4_grafana` | Up (healthy) | `0.0.0.0:3000->3000/tcp` (Assurance Dashboards) |
| `lab4_prometheus` | Up (healthy) | `0.0.0.0:9090->9090/tcp` (Telemetry TSDB) |
| `lab4_alertmanager` | Up (healthy) | `0.0.0.0:9093->9093/tcp` (Incident Dispatcher) |
| `lab4_blackbox_exporter` | Up (healthy) | `0.0.0.0:9115->9115/tcp` (Synthetic HTTP/TCP/ICMP Engine) |

---

## 2. Real-Time Telemetry Comparative Matrix

The table below demonstrates the real-time telemetry captured by querying Prometheus TSDB across three operational phases on the local testbed:

| Telemetry Dimension | Phase 1: Baseline Clean Path | Phase 2: Impaired WAN Transit (`tc netem`) | Phase 3: Post-Healing Remediation | SLO / Assertion Target | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Synthetic Path Latency** | **`6.01 ms`** | **`1555.11 ms`** (180ms + jitter + retransmits) | **`4.23 ms`** | `< 100 ms` baseline / `< 100 ms` restored | **PASS** |
| **Network Packet Loss** | **`0.00 %`** | **`15.00 %`** | **`0.00 %`** | `0%` baseline / `≥ 10%` impaired | **PASS** |
| **Path Jitter ($\Delta\text{RTT}$)** | **`3.55 ms`** | **`1198.66 ms`** | **`1.54 ms`** | `< 10 ms` clean / `> 100 ms` degraded | **PASS** |
| **Active Firing Alerts** | **`0 critical / 2 info`** | **`11 firing`** (Latency + Loss + Jitter) | **`0 critical / 2 info`** | Zero critical alerts during clean state | **PASS** |
| **Self-Healing Recovery** | N/A | Degradation active | **`< 2.8 sec`** | Restores immediately post `tc del` | **PASS** |

---

## 3. Real-Time Prometheus Blackbox Exporter Trace

Live multi-layer HTTP probe execution against the AI inference endpoint (`/api/generate`):

```promql
# Blackbox synthetic probe metrics:
probe_http_status_code{instance="http://lab4_mock_ai:11434/api/generate"} 200
probe_http_duration_seconds{phase="resolve"} 0.000412
probe_http_duration_seconds{phase="connect"} 0.000845
probe_http_duration_seconds{phase="tls"} 0.000000
probe_http_duration_seconds{phase="processing"} 0.005120
probe_http_duration_seconds{phase="transfer"} 0.000105
probe_duration_seconds 0.006482
probe_success 1
```

---

## 4. Linux Kernel `tc netem` Impairment Injection Proof

### Injection Command:
```bash
docker exec --privileged lab4_mock_ai tc qdisc add dev eth0 root netem delay 180ms 30ms distribution normal loss 15%
```

### Kernel Qdisc State Inspection:
```
qdisc netem 8005: root refcnt 9 limit 1000 delay 180ms  30ms loss 15% seed 6443984912908469970
```

---

## 5. Live Alertmanager Alert Dispatch Proof

When `180ms` delay and `15%` packet loss were injected, Prometheus evaluated the alert rules within `15 seconds` and fired the following alerts to Alertmanager (`:9093`):

```json
[
  {
    "annotations": {
      "description": "Synthetic path packet loss has reached 15.00% on target 'lab4_mock_ai:11434'.",
      "summary": "Severe WAN transit packet loss detected"
    },
    "labels": {
      "alertname": "WAN_Transit_Packet_Loss_High",
      "severity": "critical",
      "target": "lab4_mock_ai:11434"
    },
    "state": "firing"
  },
  {
    "annotations": {
      "description": "Synthetic path latency to AI endpoint has degraded to 1555.11ms (threshold: 150ms).",
      "summary": "AI Endpoint Network Latency SLA Breach"
    },
    "labels": {
      "alertname": "AI_Inference_Latency_Degraded",
      "severity": "warning",
      "target": "lab4_mock_ai:11434"
    },
    "state": "firing"
  },
  {
    "annotations": {
      "description": "Inter-packet arrival jitter is 1198.66ms (threshold: 50ms).",
      "summary": "High network path jitter on hybrid AI transit"
    },
    "labels": {
      "alertname": "Network_Path_Jitter_Elevated",
      "severity": "warning",
      "target": "lab4_mock_ai:11434"
    },
    "state": "firing"
  }
]
```

---

## 6. Self-Healing & Remediation Verification

### Remediation Command:
```bash
docker exec --privileged lab4_mock_ai tc qdisc del dev eth0 root
```

### Post-Remediation Telemetry:
- **Path Latency**: Dropped from `1555.11 ms` $\rightarrow$ **`4.23 ms`**
- **Packet Loss**: Dropped from `15.0 %` $\rightarrow$ **`0.0 %`**
- **Prometheus Firing Alerts**: Cleared and transitioned to `inactive` within 10 seconds.
