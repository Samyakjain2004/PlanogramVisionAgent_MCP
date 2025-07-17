# app/mcp_server.py
from app.tools.price_compare import compare_prices

tools = {
    "price://compare": compare_prices
}

def invoke_tool(uri: str, args: list):
    print(f"[🔧 MCP Tool Invoked] URI: {uri}, Args: {args}")
    if uri in tools:
        return tools[uri](*args)
    return {"error": f"Tool {uri} not found"}
