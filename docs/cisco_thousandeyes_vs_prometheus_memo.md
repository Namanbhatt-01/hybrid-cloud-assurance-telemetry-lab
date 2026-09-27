# Comparative Engineering Memo: Cisco ThousandEyes vs. Open-Source Synthetic Path Assurance

**Author:** Naman Bhatt  
**Date:** September 2026  
**Document ID:** MEMO-ASSURANCE-ENNA-2026-04  
**Classification:** Enterprise Network Observability & Assurance (Cisco 300-445 ENNA Blueprint)  

---

## Executive Summary

As enterprise AI workloads migrate to hybrid multi-cloud architectures (e.g. distributed GPU clusters querying HuggingFace, OpenAI, or hybrid on-premises vLLM/Ollama inference nodes), network performance across intermediate WAN, Internet Exchange Points (IXPs), and cloud transit backbones directly dictates inference time-to-first-token (TTFT) and application SLOs.

This memorandum evaluates the operational parity, telemetry models, and engineering trade-offs between **Cisco ThousandEyes** (Enterprise, Cloud, and Endpoint Agents) and an **Open-Source Synthetic Telemetry Stack** (Prometheus Blackbox Exporter + `mtr` / `smokeping` + Grafana + Linux `tc netem`).

---

## 1. Architectural Model & Component Mapping

```
+--------------------------------------------------------------------------------------------------+
| CISCO THOUSANDEYES ASSURANCE ARCHITECTURE (300-445 ENNA)                                         |
|                                                                                                  |
| [Enterprise Agent] ---> [Synthetic Test Engine] ---> [ThousandEyes Cloud Platform]              |
|        |                  - Page Load / Web Layer             |                                  |
|        |                  - Network Path Vis (Paris Traceroute)                                  |
|        v                  - BGP Route / ASN Hops              v                                  |
| [On-Prem Compute Node]                              [ThousandEyes Dashboards & Webhook Alerts]   |
+--------------------------------------------------------------------------------------------------+

+--------------------------------------------------------------------------------------------------+
| OPEN-SOURCE HYBRID CLOUD ASSURANCE STACK (Deployed in Lab 4)                                     |
|                                                                                                  |
| [Synthetic Prober] ---> [Prometheus Blackbox Exporter] ---> [Prometheus TSDB]                    |
|        |                  - HTTP 2xx / POST Inference         |                                  |
|        |                  - TCP Connect / DNS Timing          v                                  |
|        v                  - Hop-by-Hop mtr Latency & Jitter [Grafana Dashboards & Alertmanager]  |
| [AI Compute Host]         - Linux tc netem Impairments        (SLA Violations / Latency Heatmap) |
+--------------------------------------------------------------------------------------------------+
```

---

## 2. Cisco 300-445 ENNA Blueprint Topic Mapping

| Cisco 300-445 ENNA Topic | Cisco ThousandEyes Implementation | Lab 4 Open-Source Implementation |
| :--- | :--- | :--- |
| **Section 1.1: Synthetic Network Tests** | Network Agent-to-Server and Agent-to-Agent ICMP/TCP Probing | Prometheus Blackbox `tcp_connect` + `icmp_probe` + Python synthetic prober |
| **Section 1.2: Path Visualization** | Paris Traceroute calculating per-hop packet loss, delay, and link capacity | `mtr` (My Traceroute) / Python hop-by-hop latency and packet loss tracking |
| **Section 1.3: Web & HTTP Probing** | HTTP Server Tests (TTFB, Connect Time, DNS Time, SSL Negotiation) | Prometheus Blackbox `http_2xx` + `probe_http_duration_seconds` phases |
| **Section 1.4: Multi-Layer Degradation** | Alert Rules based on percentage loss and latency threshold deviations | Prometheus Alertmanager YAML rules (`AI_Inference_Latency_Degraded`, `WAN_Transit_Loss`) |
| **Section 2.1: Multi-Cloud Transit Monitoring** | Cloud Agents deployed in AWS/GCP/Azure measuring SaaS reachability | Distributed containerized probes targeting public & local AI endpoints (Ollama / HuggingFace) |
| **Section 2.2: Root Cause Analysis (RCA)** | ThousandEyes Path Visualization isolating faulty ISP/AS hops | Intermediate hop `tc netem` impairment injection and Grafana latency degradation panels |

---

## 3. Protocol & Telemetry Metric Translation

| Metric / Stage | Cisco ThousandEyes Metric | Prometheus / Blackbox Metric |
| :--- | :--- | :--- |
| **DNS Resolution** | `dns_time` (ms) | `probe_dns_lookup_time_seconds` |
| **TCP Handshake** | `connect_time` (ms) | `probe_duration_seconds{phase="connect"}` / `synthetic_tcp_handshake_ms` |
| **Time-To-First-Byte (TTFB)** | `wait_time` (ms) | `probe_http_duration_seconds{phase="processing"}` |
| **Total Response Time** | `response_time` (ms) | `probe_duration_seconds` |
| **Hop-by-Hop Jitter** | `network_jitter` (ms) | `synthetic_path_jitter_ms` |
| **Packet Loss %** | `packet_loss` (%) | `synthetic_path_packet_loss_percent` |
| **Availability SLO** | `test_availability` (%) | `probe_success` |

---

## 4. Operational Comparison & Cost-Efficiency

| Operational Dimension | Cisco ThousandEyes | Open-Source Stack (Lab 4) |
| :--- | :--- | :--- |
| **Deployment Complexity** | SaaS Portal + Lightweight Agent packages | Zero-install Docker Compose stack |
| **Hardware Overhead** | ~1 GB RAM per Enterprise Agent | **~750 MB total RAM for entire Prometheus + Grafana stack** |
| **Licensing** | Unit-based consumption ($/test/agent/month) | **$0 / 100% Free & Open Source (Apache 2.0)** |
| **Data Retention** | Standard 30–90 days (SaaS tier dependent) | Configurable Prometheus TSDB retention (`--storage.tsdb.retention.time=3d`) |
| **Apple Silicon M1 Compatibility** | Limited local agent emulation | **Native ARM64 container binaries** |

---

## 5. Engineering Conclusion & Recommendations

1. **Continuous Active Probing vs. Passive Telemetry:** Streaming telemetry (gNMI/IPFIX) only captures observed user traffic. Synthetic probing actively measures underlay health during idle periods, detecting fiber cuts and routing flaps *before* user-facing AI inference is degraded.
2. **Mean-Time-To-Identify (MTTI):** By disaggregating latency into DNS, TCP Connect, and HTTP processing, NetOps engineers can instantly distinguish between application slowdowns (high TTFB) and network transit congestion (high TCP connect / packet loss).
3. **Open Standards Portability:** The metrics, alerting logic, and dashboard structures designed in this laboratory map 1:1 to production Cisco ThousandEyes Enterprise Agent deployments.
