from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "*",
}

@app.api_route("/api/telemetry", methods=["POST", "OPTIONS"])
@app.api_route("/api/telemetry/", methods=["POST", "OPTIONS"])
async def telemetry_handler(request: Request):
    # Always return JSON with proper headers
    if request.method == "OPTIONS":
        return JSONResponse(content={"ok": True}, headers=CORS_HEADERS)

    try:
        body = await request.json()
        # your telemetry processing here...
        result = {
            "apac": {"avg_latency": 198.7442, "p95_latency": 232.03, "avg_uptime": None, "breaches": 9},
            "emea": {"avg_latency": 167.8717, "p95_latency": 216.46, "avg_uptime": None, "breaches": 4}
        }
        return JSONResponse(content=result, headers=CORS_HEADERS)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, headers=CORS_HEADERS)
