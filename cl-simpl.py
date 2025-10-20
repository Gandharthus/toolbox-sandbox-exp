import asyncio
import os
import requests
import json

from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MCP_SERVER_URL   = os.getenv("MCP_SERVER_URL", "http://localhost:8123/mcp")

async def call_llm(prompt: str) -> dict:
    """Call your custom LLM via OpenAI-style API."""
    body = {
        "model": "gpt-4-turbo-whatever",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    resp = requests.post("https://api.openai.com/v1/chat/completions",
                         headers=headers, json=body)
    resp.raise_for_status()
    return resp.json()

async def mcp_list_tools(session: ClientSession):
    resp = await session.list_tools()
    return resp.tools

async def mcp_call_tool(session: ClientSession, name: str, arguments: dict):
    resp = await session.call_tool(name=name, arguments=arguments)
    return resp

async def main_loop():
    async with streamablehttp_client(MCP_SERVER_URL) as (reader, writer, _) :
        async with ClientSession(reader, writer) as session:
            await session.initialize()
            # optional: list tools, log them
            tools = await mcp_list_tools(session)
            print("MCP tools available:", [t.name for t in tools])

            while True:
                user_input = input("You: ")
                # 1) send to LLM
                llm_resp = await asyncio.to_thread(call_llm, user_input)
                # assume you inspect the response to see if a tool call is needed
                # for example inspect llm_resp["choices"][0]["message"]["function_call"] if using OpenAI style
                msg = llm_resp["choices"][0]["message"]
                if "tool_call" in msg:  # pseudocode: adapt to actual schema
                    tool_name = msg["tool_call"]["name"]
                    tool_args = msg["tool_call"]["arguments"]
                    print(f"Invoking tool {tool_name} with args {tool_args}")
                    tool_res = await mcp_call_tool(session, tool_name, tool_args)
                    print("Tool result:", tool_res)
                    # Feed result back into LLM as new prompt
                    followup_prompt = f"Tool result:\n{tool_res}\nUser asked: {user_input}\nPlease answer accordingly."
                    llm_resp2 = await asyncio.to_thread(call_llm, followup_prompt)
                    print("Assistant:", llm_resp2["choices"][0]["message"]["content"])
                else:
                    print("Assistant:", msg["content"])

if __name__ == "__main__":
    asyncio.run(main_loop())
