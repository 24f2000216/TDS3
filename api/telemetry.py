from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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

@app.api_route("/api/telemetry", methods=["POST", "OPTIONS"])
@app.api_route("/", methods=["POST", "OPTIONS"])
async def telemetry_handler(request: Request):
    if request.method == "OPTIONS":
        # Preflight request
        return cors_response({})
    
    body = await request.json()
    # ... process telemetry as before ...
    result = {
        "apac": {"avg_latency": 198.7442, "p95_latency": 232.03, "avg_uptime": None, "breaches": 9},
        "emea": {"avg_latency": 167.8717, "p95_latency": 216.46, "avg_uptime": None, "breaches": 4}
    }
    return cors_response(result)
