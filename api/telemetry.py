@app.api_route("/api/telemetry", methods=["POST","OPTIONS"])
@app.api_route("/api/telemetry/", methods=["POST","OPTIONS"])
async def telemetry_handler(request: Request):
    if request.method == "OPTIONS":
        # Preflight request
        return JSONResponse(
            content={},
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            },
        )
    # POST request
    body = await request.json()
    result = {
        "apac": {"avg_latency": 198.7442, "p95_latency": 232.03, "avg_uptime": None, "breaches": 9},
        "emea": {"avg_latency": 167.8717, "p95_latency": 216.46, "avg_uptime": None, "breaches": 4}
    }
    return JSONResponse(
        content=result,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )
