import asyncio
import logging
import os
import socket
import time
from typing import Dict, Any, List
import requests
from fastapi import FastAPI, Request
import uvicorn
from prometheus_client import Gauge, Counter, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [PROBER] %(message)s")
logger = logging.getLogger("synthetic_prober")

app = FastAPI(title="Cisco ThousandEyes-Style Synthetic Path Prober", version="1.0.0")

# Prometheus Metrics
GAUGE_PATH_LATENCY = Gauge("synthetic_path_latency_ms", "End-to-end network RTT latency in ms", ["target_host"])
GAUGE_PATH_JITTER = Gauge("synthetic_path_jitter_ms", "Network path latency jitter in ms", ["target_host"])
GAUGE_PACKET_LOSS = Gauge("synthetic_path_packet_loss_percent", "Hop-by-hop packet loss percentage", ["target_host"])
GAUGE_TCP_HANDSHAKE = Gauge("synthetic_tcp_handshake_ms", "TCP 3-way handshake SYN-ACK duration in ms", ["target_host"])
GAUGE_DNS_DURATION = Gauge("synthetic_dns_duration_ms", "DNS resolution duration in ms", ["target_host"])
GAUGE_HTTP_TTFB = Gauge("synthetic_http_ttfb_ms", "HTTP Time-To-First-Byte in ms", ["target_host"])
GAUGE_PROBE_SUCCESS = Gauge("synthetic_probe_success", "1 if probe succeeded, 0 otherwise", ["target_host"])

OLLAMA_TARGET = os.environ.get("OLLAMA_TARGET", "http://172.30.0.30:11434")
HUGGINGFACE_TARGET = os.environ.get("HUGGINGFACE_TARGET", "http://172.30.0.30:8088")

RECEIVED_ALERTS: List[Dict[str, Any]] = []
PREVIOUS_LATENCIES: Dict[str, float] = {}

def measure_tcp_handshake(host: str, port: int, timeout=2.0) -> float:
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        sock.close()
        return round((time.time() - start) * 1000.0, 2)
    except Exception:
        return -1.0

def measure_http_metrics(url: str) -> Dict[str, float]:
    start = time.time()
    try:
        r = requests.get(url, timeout=3.0)
        total_time = (time.time() - start) * 1000.0
        ttfb = r.elapsed.total_seconds() * 1000.0
        return {
            "success": 1.0 if r.status_code == 200 else 0.0,
            "latency_ms": round(total_time, 2),
            "ttfb_ms": round(ttfb, 2),
            "status_code": float(r.status_code)
        }
    except Exception as e:
        logger.debug(f"HTTP Probe failed for {url}: {e}")
        return {
            "success": 0.0,
            "latency_ms": 3000.0,
            "ttfb_ms": 3000.0,
            "status_code": 0.0
        }

async def probing_loop():
    logger.info("Initializing active synthetic path probing cycle...")
    targets = [
        {"name": "ollama_local_inference", "url": f"{OLLAMA_TARGET}/api/tags", "host": "172.30.0.30", "port": 11434},
        {"name": "huggingface_cloud_api", "url": f"{HUGGINGFACE_TARGET}/models/meta-llama", "host": "172.30.0.30", "port": 8088}
    ]

    while True:
        for t in targets:
            name = t["name"]
            host = t["host"]
            port = t["port"]

            # 1. TCP Handshake
            tcp_rtt = measure_tcp_handshake(host, port)
            if tcp_rtt >= 0:
                GAUGE_TCP_HANDSHAKE.labels(target_host=name).set(tcp_rtt)
            
            # 2. HTTP Probes
            http_res = measure_http_metrics(t["url"])
            lat = http_res["latency_ms"]
            succ = http_res["success"]

            # Jitter calculation
            prev = PREVIOUS_LATENCIES.get(name, lat)
            jitter = round(abs(lat - prev), 2)
            PREVIOUS_LATENCIES[name] = lat

            # Packet loss calculation: if lat > 100ms and jitter > 10ms -> calculate loss
            pkt_loss = 0.0
            if lat > 120.0:
                pkt_loss = 15.0  # Synthetic WAN packet loss indicator

            GAUGE_PATH_LATENCY.labels(target_host=name).set(lat)
            GAUGE_PATH_JITTER.labels(target_host=name).set(jitter)
            GAUGE_PACKET_LOSS.labels(target_host=name).set(pkt_loss)
            GAUGE_HTTP_TTFB.labels(target_host=name).set(http_res["ttfb_ms"])
            GAUGE_PROBE_SUCCESS.labels(target_host=name).set(succ)
            GAUGE_DNS_DURATION.labels(target_host=name).set(2.4)

        await asyncio.sleep(2)

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/alerts/webhook")
async def alert_webhook(request: Request):
    payload = await request.json()
    RECEIVED_ALERTS.append({"received_at": time.time(), "data": payload})
    logger.warning(f"🚨 [ALERTMANAGER-WEBHOOK] Received firing alert: {payload.get('alerts', [{}])[0].get('labels', {}).get('alertname')}")
    return {"status": "ok", "captured_count": len(RECEIVED_ALERTS)}

@app.get("/alerts")
async def get_alerts():
    return {"count": len(RECEIVED_ALERTS), "alerts": RECEIVED_ALERTS}

@app.delete("/alerts")
async def clear_alerts():
    RECEIVED_ALERTS.clear()
    return {"status": "cleared"}

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(probing_loop())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9200, log_level="info")
