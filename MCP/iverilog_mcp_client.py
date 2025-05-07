# fast_iverilog_client.py
# Launch server
# To run the client, poetry run python iverilog_mcp_client.py --endpoint http://localhost:8000/sse --working-dir ../RTLLM/Arithmetic/Adder/adder_8bit

import argparse
import asyncio
import json
from fastmcp import Client
from mcp import types



async def main(endpoint: str, working_dir: str) -> None:
    async with Client(endpoint) as client:
        result = await client.call_tool(
            "run_verilog_tests",
            {"working_dir": working_dir}
        )

        # Convert TextContent to string for JSON serialization
        if isinstance(result[0], types.TextContent):
            result[0] = str(result[0])

        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FastMCP client for Verilog tests (stand-alone server)"
    )
    parser.add_argument(
        "--endpoint",
        default="http://localhost:8000/sse",
        help="URL of the MCP server's SSE endpoint"
    )
    parser.add_argument(
        "--working-dir",
        required=True,
        help="Path to the directory with design.v and testbench.v"
    )
    args = parser.parse_args()
    asyncio.run(main(args.endpoint, args.working_dir))
