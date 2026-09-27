#!/usr/bin/env bash
# ==============================================================================
# Linux tc netem WAN Impairment Injection Script
# Simulates Subsea Fiber Degradation / Multi-Cloud Transit Latency Spikes
# ==============================================================================

set -euo pipefail

TARGET_CONTAINER="${1:-lab4_mock_ai}"
ACTION="${2:-inject}"

case "${ACTION}" in
    inject)
        echo "🚨 [WAN-IMPAIRMENT] Injecting 180ms (+-30ms) latency jitter and 15% packet loss on container '${TARGET_CONTAINER}'..."
        docker exec --privileged "${TARGET_CONTAINER}" tc qdisc del dev eth0 root 2>/dev/null || true
        docker exec --privileged "${TARGET_CONTAINER}" tc qdisc add dev eth0 root netem delay 180ms 30ms distribution normal loss 15%
        echo "✅ Impairment active on ${TARGET_CONTAINER}:"
        docker exec "${TARGET_CONTAINER}" tc qdisc show dev eth0
        ;;
    heal)
        echo "🌿 [WAN-HEAL] Removing network impairment on container '${TARGET_CONTAINER}'..."
        docker exec --privileged "${TARGET_CONTAINER}" tc qdisc del dev eth0 root 2>/dev/null || true
        echo "✅ Network restored to clean baseline state on ${TARGET_CONTAINER}."
        ;;
    status)
        echo "🔍 [QDISC-STATUS] Inspecting tc qdisc state on '${TARGET_CONTAINER}':"
        docker exec "${TARGET_CONTAINER}" tc qdisc show dev eth0 || true
        ;;
    *)
        echo "Usage: $0 [target_container] [inject|heal|status]"
        exit 1
        ;;
esac
