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
    search_query: SearchRequest,
    index: str
):
    """
    Safe, time-boxed Elasticsearch search over LaaS (proxied via the gateway).

    Parameters
    ----------
    search_query : SearchRequest
        A Pydantic v2 model representing the `_search` payload **or** (if you’ve chosen
        to pass only the `query` container) the object placed under the `"query"` key.
        When providing a full `SearchRequest`, call:
            `search_query.model_dump(by_alias=True, exclude_none=True)`
        before sending over the wire (or ensure `_post` knows how to serialize Pydantic models).

        Common usage patterns:
          • Full body:
              SearchRequest(
                  query=BoolQuery(...),
                  size=100,
                  **{"from": 0}
              )
          • Query-only (if your gateway expects just the `query` block):
              BoolQuery(...) or MatchQuery(...)

    index : str
        Target index name, data stream, or pattern (e.g., `"logs-2025.10.15"`,
        `"logs-*"`, `"metrics-app"`) routed through the gateway.

    Behavior
    --------
    Issues `POST {index}/_search` via the gateway with a time-boxed execution policy
    (timeouts/retries enforced upstream). This helper is intended for safe, bounded
    production use in LLM tools/pipelines.

    Request Body
    ------------
    The function currently wraps the provided object as:
        {"query": search_query}
    If `search_query` is a `SearchRequest`, consider pre-serializing and passing its
    `.model_dump(...)` **and** adjusting the body to avoid nesting a full request
    under `"query"`. If `search_query` is already a query container (e.g., `BoolQuery`),
    this shape is correct.

    Returns
    -------
    Any
        The gateway’s JSON response from Elasticsearch (hits, aggregations, etc.).

    Notes
    -----
    • Use `size`/`from` responsibly; gateways may cap them.
    • Prefer filters (`terms`, `range` in `bool.filter`) for non-scoring constraints.
    • Redact/avoid PII in queries; logs may be persisted for auditing.
    """
    return _post(
        f"{index}/_search",
        {"query": search_query},
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
