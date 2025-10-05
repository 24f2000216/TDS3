from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import json, math

app = FastAPI()

def cors_response(content):
    return JSONResponse(
        content=content,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )

# Load telemetry at startup (handle missing file)
try:
    with open("telemetry.json") as f:
        TELEMETRY = json.load(f)
except Exception:
    TELEMETRY = []

def compute_p95(values):
    if not values:
        return None
    s = sorted(values)
    idx = math.ceil(0.95 * len(s)) - 1
    return float(s[idx])

@app.api_route("/api/telemetry", methods=["POST", "OPTIONS"])
@app.api_route("/api/telemetry/", methods=["POST", "OPTIONS"])
async def telemetry_handler(request: Request):
    if request.method == "OPTIONS":
        return cors_response({})

    try:
        body = await request.json()
        regions = body.get("regions", [])
        threshold_ms = body.get("threshold_ms", 0)

        result = {}
        for region in regions:
            records = [r for r in TELEMETRY if r.get("region") == region]
            latencies = [float(r.get("latency_ms")) for r in records if isinstance(r.get("latency_ms"), (int,float))]
            uptimes = [float(r.get("uptime",0))/100 if r.get("uptime",0)>1 else float(r.get("uptime",0)) for r in records if r.get("uptime") is not None]

            avg_latency = round(sum(latencies)/len(latencies),4) if latencies else None
            p95_latency = round(compute_p95(latencies),4) if latencies else None
            avg_uptime = round(sum(uptimes)/len(uptimes),6) if uptimes else None
            breaches = sum(1 for v in latencies if v>threshold_ms) if latencies else 0

            result[region] = {
                "avg_latency": avg_latency,
                "p95_latency": p95_latency,
                "avg_uptime": avg_uptime,
                "breaches": breaches
            }
        return cors_response(result)

    except Exception as e:
        # Return error with CORS headers
        return cors_response({"error": str(e)})
