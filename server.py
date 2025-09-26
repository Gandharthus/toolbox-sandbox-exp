# mcp_server.py
import os
import httpx
from typing import Optional, List
from mcp.server.fastmcp import FastMCP

GATEWAY = os.environ.get("GATEWAY_URL", "http://localhost:8080")

mcp = FastMCP("LaaS Talk-with-your-logs")

def _post(path: str, payload: dict):
    url = f"{GATEWAY}{path}"
    with httpx.Client(timeout=20) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        return r.json()

@mcp.tool()
def search_logs(
    query: str,
    from_iso: str,
    to_iso: str,
    indices: Optional[List[str]] = None,
    limit: int = 200,
    redact: bool = True,
):
    """Safe, time-boxed search over LaaS (proxied via the gateway)."""
    return _post(
        "/mcp/search",
        {"query": query, "range": {"from": from_iso, "to": to_iso},
         "indices": indices, "limit": limit, "redact": redact},
    )

@mcp.tool()
def top_patterns(service: str, env: str, from_iso: str, to_iso: str, k: int = 20):
    """Top Drain templates within a window."""
    return _post(
        "/mcp/top-patterns",
        {"service": service, "env": env, "range": {"from": from_iso, "to": to_iso}, "k": k},
    )

@mcp.tool()
def show_anomalies(service: str, env: str, from_iso: str, to_iso: str):
    """List anomalies produced by the VAE→PCA pipeline."""
    return _post(
        "/mcp/show-anomalies",
        {"service": service, "env": env, "range": {"from": from_iso, "to": to_iso}},
    )

@mcp.tool()
def change_window_snapshot(service: str, env: str, change_id: str, pre_min: int = 15, post_min: int = 30):
    """Pre/Post change snapshots + delta."""
    return _post(
        "/mcp/change-window-snapshot",
        {"service": service, "env": env, "change_id": change_id, "pre_min": pre_min, "post_min": post_min},
    )

# optional resource for quick-discovery
@mcp.resource("laas://anomalies/{service}/{env}")
def anomalies_resource(service: str, env: str) -> str:
    return f"Anomalies for {service} {env}. Use show_anomalies(tool) with a time window."

def main():
    # STDIO is perfect for local/desktop hosts; for remote/prod, you can use streamable-http.
    mcp.run(transport="streamable-http")  # or: mcp.run(transport="streamable-http")

if __name__ == "__main__":
    main()