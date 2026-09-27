# Lab 4: End-to-End Hybrid Cloud Assurance & Synthetic Path Telemetry

[![CI/CD Network Assurance](https://github.com/Namanbhatt-01/hybrid-cloud-assurance-telemetry-lab/actions/workflows/assurance_ci.yml/badge.svg)](https://github.com/Namanbhatt-01/hybrid-cloud-assurance-telemetry-lab/actions/workflows/assurance_ci.yml)
[![Prometheus](https://img.shields.io/badge/Prometheus-v2.48-E6522C?logo=prometheus&logoColor=white)](https://prometheus.io/)
[![Grafana](https://img.shields.io/badge/Grafana-v10.2-F46800?logo=grafana&logoColor=white)](https://grafana.com/)
[![Blackbox Exporter](https://img.shields.io/badge/Blackbox_Exporter-v0.24-black)](https://github.com/prometheus/blackbox_exporter)
[![Cisco 300-445 ENNA](https://img.shields.io/badge/Cisco_ENNA-300--445_Aligned-049fd9?logo=cisco&logoColor=white)](https://www.cisco.com/c/en/us/training-events/training-certifications/exams/current-list/enna-300-445.html)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Architecture](https://img.shields.io/badge/Architecture-ARM64_%2F_M1_Optimized-FF6F00)]()
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

> **Enterprise NetDevOps & SecOps Portfolio — Laboratory 4 of 6**  
> *Continuous active synthetic probing, multi-layer latency breakdown, hop-by-hop jitter tracking, and SLO assurance targeting hybrid multi-cloud AI inference infrastructure (Cisco 300-445 ENNA blueprint aligned).*

---

## 📑 Executive Overview

As enterprise AI systems scale across hybrid topologies (on-premises GPU nodes querying cloud inference endpoints such as HuggingFace, OpenAI, and local Ollama clusters), network underlay degradation across intermediate WAN links directly degrades **Time-To-First-Token (TTFT)** and breaches application Service Level Objectives (SLOs).

This laboratory establishes an **open-source, production-grade synthetic network assurance and path telemetry framework** implementing the exact monitoring paradigms of **Cisco ThousandEyes Enterprise and Cloud Agents**:
1. **Multi-Layer Synthetic Probing:** Disaggregating network round-trip time into DNS Resolution, TCP 3-way handshake, TLS negotiation, and HTTP application processing (TTFB).
2. **Hop-by-Hop Underlay Path Telemetry:** Continuous measurement of packet loss percentage and latency jitter across intermediate transit gateways.
3. **Automated Impairment Simulation:** Injecting controlled subsea fiber degradation (180ms latency jitter, 15% packet loss) using Linux `tc netem`.
4. **SLO Alerting & Automated Root Cause Analysis (RCA):** Prometheus Alertmanager rules firing within 10 seconds of SLA breach and auto-populating Grafana path assurance heatmaps.

---

## 🏛️ End-to-End System Architecture

```
+--------------------------------------------------------------------------------------------------------------------+
|                                HYBRID CLOUD AI PATH ASSURANCE TOPOLOGY                                             |
+--------------------------------------------------------------------------------------------------------------------+

     [ On-Premises Compute Node / Synthetic Agent (172.30.0.50) ]
                    |
                    | (Multi-Layer Synthetic Probes: ICMP, TCP Connect, DNS, HTTP/S)
                    v
    +========================================================================================+
    |                         HYBRID MULTI-CLOUD TRANSIT PATH (Docker Bridge)                |
    |                                                                                        |
    |  +-------------------------------------+      +-------------------------------------+  |
    |  |       Intermediate WAN Gateway      | ---> |       AI Model Inference Node       |  |
    |  |     (172.30.0.40: IP Transit Hop)   |      |     (172.30.0.30: Ollama / HF)      |  |
    |  |  * Linux tc netem Impairment Point  |      |   - Port 11434: Local Ollama        |  |
    |  |  - 180ms Delay + 15% Loss Injection |      |   - Port 8088: Cloud HuggingFace    |  |
    |  +-------------------------------------+      +-------------------------------------+  |
    +========================================================================================+
                    |                                                          |
                    | (Active Scrape: Every 3s)                                |
                    v                                                          v
    +========================================================================================+
    |                         OBSERVABILITY & ASSURANCE CONTROL PLANE                        |
    |                                                                                        |
    |   +------------------------------------+      +-------------------------------------+  |
    |   |      Blackbox Exporter (9115)      |      |      Synthetic Path Prober (9200)   |  |
    |   |   - Module: `http_2xx_ai_api`      |      |   - TCP 3-Way Handshake SYN-ACK     |  |
    |   |   - Module: `http_post_inference`  |      |   - Hop-by-Hop Path Jitter (ms)     |  |
    |   |   - Module: `tcp_connect`          |      |   - Transit Packet Loss %           |  |
    |   +------------------+-----------------+      +------------------+------------------+  |
    |                      |                                           |                     |
    |                      +--------------------+----------------------+                     |
    |                                           v                                            |
    |                         +----------------------------------+                           |
    |                         |      Prometheus TSDB (9090)      |                           |
    |                         |  - 5s Scrape / Evaluation Cycle  |                           |
    |                         |  - Retention: 3 Days (TSDB Capped|                           |
    |                         +-----------------+----------------+                           |
    |                                           |                                            |
    |                      +--------------------+--------------------+                       |
    |                      v                                         v                       |
    |     +----------------------------------+     +----------------------------------+      |
    |     |      Grafana 10.2 Dashboards     |     |     Prometheus Alertmanager      |      |
    |     |  - Path Heatmaps & Stat Gauges   |     |  - Latency Degradation Alerting  |      |
    |     |  - Multi-Layer Stage Breakdown   |     |  - Webhook Dispatch within 10s   |      |
    |     |  - Port 3000 (Auto-Provisioned)  |     |  - Port 9093                     |      |
    |     +----------------------------------+     +----------------------------------+      |
    +========================================================================================+
```

---

## 🔬 Multi-Layer Telemetry Decomposition

To isolate whether performance degradation stems from application slow-down, DNS resolution failure, or WAN underlay congestion, synthetic probes disaggregate latency into discrete stages:

```
+--------------------------------------------------------------------------------------------------+
| TOTAL TRANSACTION LATENCY BREAKDOWN (ThousandEyes / Prometheus Blackbox Model)                  |
|                                                                                                  |
| [DNS Lookup] --------> [TCP Handshake] --------> [TLS Negotiation] --------> [HTTP Server TTFB]  |
|  (2.4 ms)               (182.4 ms - DEGRADED)      (0.0 ms - HTTP)            (42.1 ms)          |
|                                 |                                                                |
|                     * UNDERLAY WAN IMPAIRMENT DETECTED *                                         |
|                     - Location: Intermediate Hop 172.30.0.40                                     |
|                     - Exonerated: Application Layer & DNS Name Servers                           |
+--------------------------------------------------------------------------------------------------+
```

---

## 📊 Live Verification & Real-Time Telemetry Proof

This laboratory was validated in real-time on an **Apple Silicon macOS host** (`Darwin 24.3.0 ARM64`) across three operational phases. Complete raw telemetry captures and logs are saved in [`poc/REALTIME_EVIDENCE.md`](poc/REALTIME_EVIDENCE.md) and [`poc/live_assurance_telemetry_evidence.json`](poc/live_assurance_telemetry_evidence.json).

### 📈 Phase-by-Phase Real-Time Telemetry Matrix

| Telemetry Dimension | Phase 1: Baseline Clean Path | Phase 2: Impaired WAN Transit (`tc netem`) | Phase 3: Post-Healing Remediation | SLO Target | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Synthetic Path Latency** | **`6.01 ms`** | **`1555.11 ms`** (180ms + jitter + retransmits) | **`4.23 ms`** | `< 100 ms` baseline / `< 100 ms` restored | **PASS** |
| **Network Packet Loss** | **`0.00 %`** | **`15.00 %`** | **`0.00 %`** | `0%` baseline / `≥ 10%` impaired | **PASS** |
| **Path Jitter ($\Delta	ext{RTT}$)** | **`3.55 ms`** | **`1198.66 ms`** | **`1.54 ms`** | `< 10 ms` clean / `> 100 ms` degraded | **PASS** |
| **Prometheus Active Alerts** | **`0 critical`** | **`11 firing`** (Latency, Loss, Jitter) | **`0 critical`** | Zero SLA breach alerts on clean state | **PASS** |
| **Mean-Time-To-Detect (MTTD)**| N/A | **`< 15 seconds`** | N/A | Alert evaluation cycle `< 30s` | **PASS** |
| **Self-Healing Recovery Time** | N/A | Degradation active | **`< 2.8 seconds`** | Immediate metric recovery | **PASS** |

---

### 🔍 Live Blackbox Exporter Trace (Multi-Layer HTTP Timing Decomposition)
```promql
# Blackbox synthetic probe metrics (Ollama /api/generate):
probe_http_status_code{instance="http://lab4_mock_ai:11434/api/generate"} 200
probe_http_duration_seconds{phase="resolve"}    0.000412  # DNS Resolution: 0.41ms
probe_http_duration_seconds{phase="connect"}    0.000845  # TCP 3-Way Handshake: 0.85ms
probe_http_duration_seconds{phase="tls"}        0.000000  # TLS Handshake (HTTP local): 0.00ms
probe_http_duration_seconds{phase="processing"} 0.005120  # Server Processing (TTFB): 5.12ms
probe_http_duration_seconds{phase="transfer"}   0.000105  # Content Transfer: 0.11ms
probe_duration_seconds                          0.006482  # Total Transaction Time: 6.48ms
probe_success                                   1
```

---

### 🚨 Real-Time Prometheus Alert Rule Trigger (WAN Degradation)
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
  }
]
```

---

### 🧪 Automated Test Suite Output (`python3 prober/verify_assurance_pipeline.py`)

```text
==============================================================================
                  PHASE 1: OBSERVABILITY STACK HEALTH CHECK                 
==============================================================================
  [+] Prometheus Server              -> ONLINE (HTTP 200)
  [+] Grafana Dashboards             -> ONLINE (HTTP 200)
  [+] Blackbox Exporter              -> ONLINE (HTTP 200)
  [+] Ollama AI Endpoint             -> ONLINE (HTTP 200)
  [+] Synthetic Path Prober          -> ONLINE (HTTP 200)

==============================================================================
                  PHASE 2: SAMPLING CLEAN BASELINE TELEMETRY                
==============================================================================
  Baseline Path Latency: 3.69 ms
  Baseline Blackbox TTFB: 522.42 ms
  Baseline Packet Loss: 0.0 %
  Baseline Jitter: 1.46 ms

==============================================================================
                  PHASE 3: INJECTING WAN TRANSIT IMPAIRMENT                 
==============================================================================
  Applying 'tc netem delay 180ms 30ms loss 15%' on target container...
  Awaiting metric degradation and Prometheus alert rule evaluation (18s)...

  Degraded Path Latency: 411.76 ms (Target > 150ms)
  Degraded Packet Loss: 15.0 % (Target >= 10%)
  Degraded Jitter: 693.33 ms
  Active Prometheus Alerts: ['AI_API_Endpoint_Unreachable', 'AI_Inference_Latency_Degraded', 'WAN_Transit_Packet_Loss_High', 'Network_Path_Jitter_Elevated']

==============================================================================
                     PHASE 4: HEALING NETWORK IMPAIRMENT                    
==============================================================================
  Removing 'tc netem' impairment rules...
  Restored Path Latency: 2.81 ms

==============================================================================
                  PHASE 5: HYBRID CLOUD ASSURANCE ASSERTIONS                
==============================================================================
  [✅ PASS] Prometheus & Blackbox Stack Healthy
  [✅ PASS] Baseline Latency < 100ms
  [✅ PASS] Baseline Packet Loss == 0%
  [✅ PASS] WAN Impairment Triggered Latency Spike (>150ms)
  [✅ PASS] Packet Loss Degradation Detected (>=10%)
  [✅ PASS] Prometheus Alert Rule Evaluated / Fired
  [✅ PASS] Network Self-Healing Verified (<100ms Post-Heal)
==============================================================================

🎉 ALL LAB 4 NETWORK ASSURANCE ASSERTIONS PASSED SUCCESSFULLY!
```

---

## 🧭 Cisco 300-445 ENNA Blueprint Alignment

| Cisco 300-445 ENNA Domain | Cisco ThousandEyes Implementation | Lab 4 Open-Source Implementation |
| :--- | :--- | :--- |
| **Synthetic Network Tests** | Agent-to-Server and Agent-to-Agent ICMP/TCP Probing | Prometheus Blackbox `tcp_connect` + `icmp_probe` |
| **Path Visualization** | Paris Traceroute calculating per-hop delay and loss | `mtr` / Python hop-by-hop latency and packet loss tracking |
| **Web & API Probing** | HTTP Server Tests (TTFB, Connect, SSL, DNS) | Prometheus Blackbox `http_2xx` + `probe_http_duration_seconds` |
| **SLO Violation Alerting** | Alert Rules based on deviation thresholds | Prometheus Alertmanager YAML rules (`AI_Inference_Latency_Degraded`) |
| **Multi-Cloud Assurance** | Cloud Agents measuring SaaS and public AI APIs | Distributed synthetic probes targeting Ollama and HuggingFace endpoints |
| **Root Cause Analysis (RCA)** | ThousandEyes Path Visualization isolating faulty hops | Intermediate hop `tc netem` impairment + Grafana path heatmaps |

*For in-depth architectural comparisons, see [docs/cisco_thousandeyes_vs_prometheus_memo.md](docs/cisco_thousandeyes_vs_prometheus_memo.md).*  
*For a production Root Cause Analysis incident walkthrough, see [docs/incident_rca_network_degradation.md](docs/incident_rca_network_degradation.md).*

---

## 🚀 Quickstart & Reproduction

### Prerequisites
- Docker & Docker Compose (Docker Desktop for Mac / Linux)
- Python 3.11+
- `curl` and `jq`

### 1. Launch the Observability Stack
```bash
git clone https://github.com/Namanbhatt-01/hybrid-cloud-assurance-telemetry-lab.git
cd hybrid-cloud-assurance-telemetry-lab

# Build and start Prometheus, Grafana, Blackbox, and AI endpoints
make up
```

### 2. View Real-Time Grafana Dashboards
Navigate to `http://localhost:3000` (pre-provisioned credentials `admin` / `admin`).  
Open the **"Hybrid Cloud AI Path Assurance & Synthetic Telemetry"** dashboard.

### 3. Run Automated End-to-End Verification
```bash
# Runs health checks, captures baseline, injects tc netem impairment, asserts alert firing, and heals
make test
```

### 4. Manual Impairment Testing
```bash
# Inject 180ms delay and 15% packet loss
make impair

# Inspect Prometheus active alerts
make status

# Restore baseline
make heal
```

### 5. Clean Teardown
```bash
make clean
```

---

## 📂 Repository Structure

```
├── .github/
│   └── workflows/
│       └── assurance_ci.yml              # Automated CI/CD pipeline verifying path assurance
├── config/
│   ├── alertmanager/
│   │   └── alertmanager.yml              # Prometheus Alertmanager notification config
│   ├── blackbox/
│   │   └── blackbox.yml                  # Blackbox exporter HTTP, TCP, DNS modules
│   ├── grafana/
│   │   ├── dashboards/
│   │   │   └── path_assurance_dashboard.json # Production Grafana assurance dashboard
│   │   └── provisioning/
│   │       ├── dashboards/dashboards.yml # Automatic dashboard provider
│   │       └── datasources/prometheus.yml# Prometheus data source definition
│   └── prometheus/
│       ├── alert_rules.yml               # Latency SLO and packet loss alert rules
│       └── prometheus.yml                # Prometheus TSDB scrape configurations
├── docs/
│   ├── cisco_thousandeyes_vs_prometheus_memo.md # Cisco 300-445 ENNA comparative memo
│   └── incident_rca_network_degradation.md     # Production P2 RCA incident report
├── impairment_injection/
│   └── simulate_wan_degradation.sh       # Linux tc netem delay & packet loss injector
├── mock_endpoints/
│   ├── Dockerfile                        # Container with iproute2 & FastAPI
│   └── main.py                           # Mock Ollama & HuggingFace inference API
├── prober/
│   ├── Dockerfile                        # Synthetic prober container with mtr
│   ├── path_prober.py                    # Multi-layer synthetic probing daemon
│   └── verify_assurance_pipeline.py      # Automated assertion and verification runner
├── docker-compose.yml                    # Multi-container assurance stack
├── Makefile                              # Lifecycle automation targets
├── requirements.txt                      # Python dependencies for CI & local probers
├── run_lab4_experiment.sh                # Local one-command experiment runner
└── README.md                             # Comprehensive technical documentation
```

---

## 🛡️ License

This project is open-source software licensed under the [Apache-2.0 License](LICENSE).
