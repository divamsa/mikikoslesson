import os, asyncio
import mcp.server.stdio
from mcp.server import Server
from mcp.types import Tool, TextContent
import openai

server = Server("openai-codex")
_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY environment variable is not set")
        _client = openai.AsyncOpenAI(api_key=api_key)
    return _client

@server.list_tools()
async def list_tools():
    return [
        Tool(name="ask_codex", description="Send a coding question to OpenAI GPT-4o.", inputSchema={"type":"object","properties":{"prompt":{"type":"string"},"model":{"type":"string","default":"gpt-4o"}},"required":["prompt"]}),
        Tool(name="review_code", description="Ask GPT-4o to review code.", inputSchema={"type":"object","properties":{"code":{"type":"string"},"language":{"type":"string","default":"unknown"},"focus":{"type":"string","default":"all"}},"required":["code"]}),
    ]

@server.call_tool()
async def call_tool(name, arguments):
    client = get_client()
    if name == "ask_codex":
        r = await client.chat.completions.create(model=arguments.get("model","gpt-4o"), messages=[{"role":"user","content":arguments["prompt"]}])
        return [TextContent(type="text", text=f"[GPT-4o]\n\n{r.choices[0].message.content}")]
    if name == "review_code":
        prompt = f"Review this {arguments.get('language','unknown')} code (focus: {arguments.get('focus','all')}):\n\n```\n{arguments['code']}\n```"
        r = await client.chat.completions.create(model="gpt-4o", messages=[{"role":"system","content":"You are a senior code reviewer."},{"role":"user","content":prompt}])
        return [TextContent(type="text", text=f"[Code Review by GPT-4o]\n\n{r.choices[0].message.content}")]
    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with mcp.server.stdio.stdio_server() as (r, w):
        await server.run(r, w, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
