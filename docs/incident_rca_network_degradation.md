# Root Cause Analysis (RCA): Hybrid Cloud Transit Latency Spike & Packet Loss

**Incident Reference:** RCA-NET-2026-0927-02  
**Severity:** P2 (High Priority Service Degradation)  
**Impact:** AI Model Inference Time-To-First-Token (TTFT) degraded from 45ms to 220ms  
**Affected Path:** On-Prem GPU Cluster (`172.30.0.50`) -> Hybrid Transit Gateway (`172.30.0.40`) -> AI Inference Gateway (`172.30.0.30:11434`)  
**Lead Network Reliability Engineer:** Naman Bhatt  

---

## 1. Executive Summary

At 10:14:00 UTC, automated Prometheus Blackbox synthetic probes detected a sudden breach of the 150ms Latency SLO on our primary AI inference API (`http://172.30.0.30:11434/api/tags`), with latency spiking to **215ms** alongside **15.2% packet loss** and elevated jitter (**28.4ms**).

The Synthetic Path Telemetry engine pinpointed the degradation to intermediate transit hop `172.30.0.40` (WAN Transit Gateway) rather than the AI application itself. Application processing time (TTFB) remained flat at 42ms, while TCP handshake latency increased by 165ms, confirming an underlay network transit impairment.

---

## 2. Telemetry Timeline & Multi-Layer Dissection

| Timestamp (UTC) | Telemetry Source | Metric | Observed Value | Baseline Threshold | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `10:13:55` | Blackbox Exporter | `probe_duration_seconds` | 42.5 ms | < 150 ms | ✅ Normal |
| `10:14:02` | `synthetic_prober` | `synthetic_tcp_handshake_ms` | **182.4 ms** | < 15 ms | ⚠️ Degraded |
| `10:14:05` | `synthetic_prober` | `synthetic_path_packet_loss_percent`| **15.0%** | < 1.0% | 🚨 Critical Alert |
| `10:14:15` | Prometheus Alertmanager | `AI_Inference_Latency_Degraded` | **FIRING** | N/A | Webhook Dispatched |
| `10:14:18` | Prometheus Alertmanager | `WAN_Transit_Packet_Loss_High` | **FIRING** | N/A | Webhook Dispatched |
| `10:16:30` | Network Automation | `tc qdisc del dev eth0 root` | Clean | Clean | 🌿 Restored |
| `10:16:45` | Blackbox Exporter | `probe_duration_seconds` | 43.1 ms | < 150 ms | ✅ Resolved |

---

## 3. Root Cause Analysis (RCA)

```
+--------------------------------------------------------------------------------------------------+
| MULTI-LAYER LATENCY DISSECTION (ThousandEyes / Blackbox Telemetry)                               |
|                                                                                                  |
| [DNS Resolution: 2.4ms] ---> [TCP Connect: 182.4ms] ---> [HTTP Processing TTFB: 42.1ms]         |
|                                         |                                                        |
|                         (UNDERLAY TRANSIT IMPAIRMENT)                                            |
|                         - Injected Netem: Delay 180ms +- 30ms, 15% Packet Loss                   |
|                         - Root Cause: Intermediate transit link buffer overrun / degradation     |
+--------------------------------------------------------------------------------------------------+
```

1. **Failure Domain Isolation:** Because DNS lookup duration (2.4ms) and application processing TTFB (42.1ms) remained constant, the application and DNS authoritative servers were exonerated immediately.
2. **Transit Degradation:** The entire 175ms latency increase originated in the TCP SYN-ACK handshake and packet loss over intermediate hop `172.30.0.40`.

---

## 4. Remediation & Action Items

- [x] **Automated Alerting:** Verified Prometheus Alertmanager fired within 10 seconds of underlay degradation.
- [x] **Path Visualizer Dashboard:** Grafana dashboard accurately displayed latency divergence between TCP connect and HTTP TTFB.
- [ ] **BGP Dynamic Path Reroute:** Implement automated BGP path prepending / MED adjustments to divert traffic away from degraded WAN transit links when packet loss exceeds 5%.
