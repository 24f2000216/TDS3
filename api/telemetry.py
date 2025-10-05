from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import json
import math
from typing import List, Dict, Any, Optional

app = FastAPI()

# Load telemetry data
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

# Manual OPTIONS handler for CORS (Vercel serverless fix)
@app.options("/api/telemetry")
@app.options("/")
async def preflight():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# POST endpoint
@app.post("/api/telemetry")
@app.post("/")
async def telemetry_metrics(body: Dict[str, Any]):
    regions = body.get("regions")
    threshold_ms = body.get("threshold_ms")

    if not isinstance(regions, list) or threshold_ms is None:
        raise HTTPException(status_code=400, detail="Invalid request body")

    result = {}
    for region in regions:
        records = [r for r in TELEMETRY if r.get("region") == region]
        latencies = [float(r.get("latency_ms")) for r in records if isinstance(r.get("latency_ms"), (int, float))]
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

    return JSONResponse(content=result, headers={"Access-Control-Allow-Origin": "*"})
