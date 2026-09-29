# LAB 03: Hybrid Cloud Path Assurance & Synthetic Telemetry

[![CI/CD Assurance Pipeline](https://github.com/Namanbhatt-01/hybrid-cloud-assurance-telemetry-lab/actions/workflows/assurance_ci.yml/badge.svg)](https://github.com/Namanbhatt-01/hybrid-cloud-assurance-telemetry-lab/actions/workflows/assurance_ci.yml)
[![Prometheus Blackbox](https://img.shields.io/badge/Prober-Prometheus_Blackbox_v0.24-orange?logo=prometheus&logoColor=white)](https://github.com/prometheus/blackbox_exporter)
[![Grafana](https://img.shields.io/badge/Grafana-v10.2-F46800?logo=grafana&logoColor=white)](https://grafana.com/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

A reproducible laboratory for evaluating active synthetic path probing (DNS, TCP, TLS, HTTP latency decomposition) and SLO breach detection across distributed hybrid-cloud AI inference endpoints under injected WAN impairments (`tc netem`).

---

## 1. Problem Statement

Distributed AI applications rely on multi-cloud API endpoints (e.g. centralized embedding engines, remote LLM token streaming APIs). Traditional passive monitoring only observes traffic when requests fail, making it impossible to detect degraded WAN transit latency before user transactions suffer timeout spikes.

This laboratory implements:
1. **Active Synthetic Path Probing**: Prometheus Blackbox prober executing sub-minute health and latency checks across distributed endpoints.
2. **Layered Latency Breakdown**: Decomposing total round-trip time into DNS resolution, TCP handshake, TLS negotiation, and HTTP time-to-first-byte (TTFB).
3. **Controlled Impairment Injection**: Injecting synthetic WAN jitter, latency, and packet loss using Linux `tc netem`.
4. **SLO Breach Evaluation**: Automated threshold alerting and machine-readable evidence emission.

---

## 2. Experiment Structure: Baseline vs Injected vs Observed

The laboratory explicitly separates observed natural network behavior from synthetically injected impairment:

```text
Experiment: WAN-LATENCY-001

Baseline (Natural Network):
  p50 RTT: 22.4 ms
  p95 RTT: 28.1 ms
  packet loss: 0.0%

Injected Impairment (tc netem):
  delay: 180 ms
  jitter: 20 ms
  loss: 15%

Observed (Degraded State):
  p50 RTT: 204.3 ms
  p95 RTT: 248.1 ms
  packet loss: 14.8%

Detection:
  SLO threshold: 50.0 ms
  SLO breach: YES (Triggered alert)
```

---

## 3. Architecture

```
┌────────────────────────────────────────────────────────┐
│     Prometheus Server (:9090) & Grafana (:3000)        │
└───────────────────────────┬────────────────────────────┘
                            │ Scrapes 5s cadence
                            ▼
┌────────────────────────────────────────────────────────┐
│        Prometheus Blackbox Exporter (:9115)            │
│  - http_2xx (DNS / TCP / TLS / HTTP breakdown)         │
│  - tcp_connect / icmp probes                           │
└───────────────────────────┬────────────────────────────┘
                            │ Synthetic probes
    ┌───────────────────────┼───────────────────────┐
    ▼                       ▼                       ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Mock AWS    │    │  Mock Azure  │    │  Mock Local  │
│  Endpoint    │    │  Endpoint    │    │  GPU Mesh    │
│  (:8001)     │    │  (:8002)     │    │  (:11434)    │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 4. Evidence Envelope Output

The verification suite runs the impairment test and records results to `poc/evidence.json`:

```json
{
  "schema_version": "1.0",
  "experiment": {
    "id": "wan-latency-001",
    "name": "Synthetic Multi-Cloud AI Endpoint Latency Probing & Impairment"
  },
  "execution": {
    "run_id": "assurance-20260929-151000",
    "timestamp": "2026-09-29T15:10:00Z",
    "environment": "docker-compose",
    "platform": "darwin-arm64"
  },
  "measurements": [
    { "metric": "baseline_path_latency_ms", "value": 22.4, "mode": "measured" },
    { "metric": "degraded_path_latency_ms", "value": 204.3, "mode": "measured" },
    { "metric": "injected_wan_delay_ms", "value": 180.0, "mode": "simulated" }
  ],
  "assertions": [
    { "id": "ASSURANCE-ASSERT-001", "name": "Multi-Cloud Inference SLO Compliance", "passed": true }
  ],
  "result": "passed"
}
```

---

## 5. Quickstart & Local Reproduction

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### Execute Verification Suite
```bash
# 1. Start Stack
make up

# 2. Run automated testbed
python3 verify_path_assurance.py

# 3. Teardown
make down
```

---

## 6. Known Limitations

1. **Mock Endpoints**: Cloud endpoints (AWS us-east, Azure eu-west) are containerized mock HTTP servers within Docker rather than live global SaaS endpoints.
2. **Network Impairment Boundary**: WAN impairment is injected on container egress using `tc netem` in the local network namespace rather than traversing physical WAN undersea cables.

---

## 7. License

Apache 2.0 License. See [LICENSE](LICENSE) for details.
