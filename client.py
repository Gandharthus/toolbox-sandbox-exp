import asyncio
from typing import Any, Dict, List

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport

def unwrap_tool_result(resp: Any) -> Any:
    """
    FastMCP returns a result object with `.content` list, each part has `.text` or `.json`.
    This helper extracts the usable payload.
    """
    # resp.content is a list of items
    if hasattr(resp, "content") and resp.content:
        first = resp.content[0]
        # If it has `.json`, prefer that
        if hasattr(first, "json"):
            try:
                return first.json
            except Exception:
                pass
        if hasattr(first, "text"):
            return first.text
    # fallback
    return resp

async def main():
    SERVER_URL = "http://localhost:8000/mcp"
    TOKEN = "YOUR_TOKEN_HERE"

    transport = StreamableHttpTransport(
        url=SERVER_URL,
        headers={"Authorization": f"Bearer {TOKEN}"}
    )
    client = Client(transport=transport)

    async with client:
        # Test echo
        res = await client.call_tool("echo", {"msg": "hello streamable HTTP"})
        print("Echo:", unwrap_tool_result(res))

        # Test add
        res2 = await client.call_tool("add", {"a": 3, "b": 4})
        print("Add:", unwrap_tool_result(res2))

        # Test LLM streaming
        content = input("query>")
        chat_req = {
            "messages": [{"role": "user", "content": "Tell me a joke"}],
            "model": "gpt-4"
        }
        print("hi")
        resp_chat = await client.call_tool("llm_chat", chat_req)
        result_text = unwrap_tool_result(resp_chat)
        print("LLM chat:", result_text)

if __name__ == "__main__":
    asyncio.run(main())