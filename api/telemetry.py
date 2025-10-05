# api/telemetry.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import math
from typing import List, Dict, Any, Optional

app = FastAPI()

# Enable CORS for POST from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load the telemetry bundle at cold-start (deployed functions include repo files)
try:
    with open("telemetry.json", "r") as f:
        TELEMETRY = json.load(f)
except FileNotFoundError:
    TELEMETRY = []


def compute_p95(values: List[float]) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    idx = math.ceil(0.95 * len(s)) - 1
    idx = max(0, min(idx, len(s) - 1))
    return float(s[idx])


# Accept both "/" (local) and "/api/telemetry" (Vercel) as POST endpoints
@app.post("/")
@app.post("/api/telemetry")
async def telemetry_metrics(body: Dict[str, Any]):
    """
    Expects JSON body: {"regions": [...], "threshold_ms": 180}
    Returns a mapping: region -> { avg_latency, p95_latency, avg_uptime, breaches }
    """
    regions = body.get("regions")
    threshold_ms = body.get("threshold_ms")

    if not isinstance(regions, list) or threshold_ms is None:
        raise HTTPException(
            status_code=400,
            detail="Body must be {'regions':[...], 'threshold_ms': <number>}"
        )

    result = {}
    for region in regions:
        # filter records for this region
        records = [r for r in TELEMETRY if r.get("region") == region]

        # collect numeric latencies
        latencies = [
            float(r.get("latency_ms"))
            for r in records
            if isinstance(r.get("latency_ms"), (int, float))
        ]

        # collect uptime values and normalize:
        # if uptime > 1 assume it's percent (e.g., 99.9) and convert to fraction (0.999)
        uptimes = []
        for r in records:
            u = r.get("uptime")
            if u is None:
                continue
            if isinstance(u, (int, float)):
                if u > 1:
                    u = u / 100.0
                uptimes.append(float(u))

        avg_latency = round(sum(latencies) / len(latencies), 4) if latencies else None
        p95_latency = round(compute_p95(latencies), 4) if latencies else None
        avg_uptime = round(sum(uptimes) / len(uptimes), 6) if uptimes else None
        breaches = int(sum(1 for v in latencies if v > float(threshold_ms))) if latencies else 0

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return result
