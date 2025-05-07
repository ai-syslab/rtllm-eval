# iverilog_mcp_server.py
# Launch server - poetry run fastmcp run iverilog_mcp_server.py:mcp --transport sse --host 0.0.0.0 --port 8000

from fastmcp import FastMCP
from pathlib import Path
import asyncio, subprocess

mcp = FastMCP("iverilog")

@mcp.tool()
async def run_verilog_tests(working_dir: str) -> dict[str, str | bool]:
    """Compile `design.v` and `testbench.v` with Icarus and run the VVP."""
    wd = Path(working_dir).resolve()
    compile = await asyncio.create_subprocess_exec(
        "iverilog", "-o", "netlist.vvp", "design.v", "testbench.v",
        cwd=wd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    out, _ = await compile.communicate()
    if compile.returncode:
        return {"success": False, "output": out.decode()}
    run = await asyncio.create_subprocess_exec(
        "vvp", "netlist.vvp", cwd=wd,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    rout, _ = await run.communicate()
    return {"success": run.returncode == 0,
            "output": (out + rout).decode()}
