# api/telemetry.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import json, os, math, statistics

app = FastAPI(title="eShopCo telemetry checker")

# Enable CORS for POST from ANY origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

class Query(BaseModel):
    regions: List[str]
    threshold_ms: float

# Utility: percentile (linear interpolation)
def percentile(data: List[float], perc: float):
    if not data:
        return None
    data = sorted(data)
    n = len(data)
    if n == 1:
        return float(data[0])
    # index as float
    k = (n - 1) * (perc / 100.0)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return float(data[int(k)])
    d0 = data[int(f)] * (c - k)
    d1 = data[int(c)] * (k - f)
    return float(d0 + d1)

# Load telemetry bundle (place your downloaded telemetry file at data/telemetry.json or telemetry.json)
TELEMETRY = []
for p in ("data/telemetry.json", "telemetry.json"):
    if os.path.exists(p):
        with open(p, "r") as fh:
            TELEMETRY = json.load(fh)
        break

# Example expected record shape (for reference):
# { "region": "apac", "latency_ms": 120.5, "uptime": 1 } where uptime is 1/0 or 0.999 etc.

def compute_region_metrics(region: str, threshold_ms: float) -> Dict[str, Any]:
    records = [r for r in TELEMETRY if r.get("region") == region]
    if not records:
        # return zero/None or empty metrics if region not present
        return {"avg_latency": None, "p95_latency": None, "avg_uptime": None, "breaches": 0}
    # collect latencies and uptimes
    latencies = []
    uptimes = []
    for r in records:
        if "latency_ms" in r and r["latency_ms"] is not None:
            try:
                latencies.append(float(r["latency_ms"]))
            except:
                pass
        if "uptime" in r and r["uptime"] is not None:
            # accept boolean, fraction, percent (0-1 or 0-100)
            u = r["uptime"]
            try:
                u = float(u)
                # if user stored uptime as 0-100, normalize to 0-1 if >1
                if u > 1:
                    u = u / 100.0
                uptimes.append(u)
            except:
                pass

    avg_latency = round(statistics.mean(latencies), 3) if latencies else None
    p95_latency = round(percentile(latencies, 95), 3) if latencies else None
    avg_uptime = round(statistics.mean(uptimes), 6) if uptimes else None
    breaches = sum(1 for l in latencies if l > threshold_ms)

    return {
        "avg_latency": avg_latency,
        "p95_latency": p95_latency,
        "avg_uptime": avg_uptime,
        "breaches": breaches,
    }

@app.post("/")
async def check_telemetry(query: Query):
    # Ensure telemetry bundle is loaded
    if TELEMETRY == []:
        raise HTTPException(status_code=500, detail="Telemetry bundle not found on server. Put it at data/telemetry.json")
    out = {}
    for region in query.regions:
        out[region] = compute_region_metrics(region, query.threshold_ms)
    return out
