#!/usr/bin/env bash
# ==============================================================================
# Lab 4: End-to-End Hybrid Cloud Assurance & Synthetic Path Telemetry
# Automated Orchestration, Impairment Testing & Verification Script
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}"

echo "======================================================================"
echo "🚀 STARTING LAB 4: HYBRID CLOUD ASSURANCE & SYNTHETIC TELEMETRY"
echo "======================================================================"

# 1. Clean previous state
echo "[1/6] Ensuring clean environment and stopping legacy containers..."
docker compose down -v --remove-orphans 2>/dev/null || true

# 2. Build & Launch Containers
echo "[2/6] Building and launching containerized observability stack..."
docker compose up -d --build

# 3. Wait for Core Services to be Healthy
echo "[3/6] Awaiting service health (Prometheus, Grafana, Blackbox, AI Endpoints)..."
for i in {1..30}; do
    if curl -s http://localhost:9090/-/healthy | grep -q "Prometheus Server is Healthy" && \
       curl -s http://localhost:3000/api/health | grep -q '"database": "ok"' && \
       curl -s http://localhost:9115/ >/dev/null && \
       curl -s http://localhost:11434/api/tags >/dev/null && \
       curl -s http://localhost:9200/metrics >/dev/null; then
        echo "✅ All core observability services are online and healthy!"
        break
    fi
    echo "  Waiting for services ($i/30)..."
    sleep 3
done

# 4. Measure Clean Baseline Telemetry
echo "[4/6] Sampling clean network baseline telemetry (10s)..."
sleep 10
echo "--- Baseline Probe Metrics ---"
curl -s "http://localhost:9090/api/v1/query?query=avg(probe_duration_seconds)" | jq '.data.result[0].value' || true
curl -s "http://localhost:9090/api/v1/query?query=avg(synthetic_path_latency_ms)" | jq '.data.result[0].value' || true

# 5. Inject WAN Impairment (180ms delay, 15% loss)
echo "[5/6] Injecting WAN Transit Impairment (tc netem delay 180ms, 15% packet loss)..."
./impairment_injection/simulate_wan_degradation.sh lab4_mock_ai inject
echo "  Awaiting Prometheus scrape and alert rule evaluation (20s)..."
sleep 20

echo "--- Degraded State Metrics ---"
curl -s "http://localhost:9090/api/v1/query?query=avg(probe_duration_seconds)" | jq '.data.result[0].value' || true
curl -s "http://localhost:9090/api/v1/query?query=avg(synthetic_path_latency_ms)" | jq '.data.result[0].value' || true
curl -s "http://localhost:9090/api/v1/alerts" | jq '.data.alerts[] | {alertname: .labels.alertname, state: .state, value: .value}' || true

# 6. Heal Impairment & Restore Baseline
echo "[6/6] Healing network impairment and restoring clean baseline..."
./impairment_injection/simulate_wan_degradation.sh lab4_mock_ai heal
sleep 5

echo "======================================================================"
echo "🎉 LAB 4 EXPERIMENT & ASSURANCE PIPELINE VERIFICATION COMPLETE!"
echo "======================================================================"
