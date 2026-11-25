"""Step 6 self-test: start the server over stdio, list its tools, call list_events.

Run (macOS):  GOOGLE_PRIVATE_DIR=~/secrets uv run test_server.py
Add --offline to only check tools/list (no Google call).
"""

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

HERE = os.path.dirname(os.path.abspath(__file__))
EXPECTED = {"search_emails", "read_email", "create_draft",
            "list_events", "find_free_slots", "create_event"}


async def main(offline: bool) -> None:
    params = StdioServerParameters(
        command=sys.executable, args=[os.path.join(HERE, "server.py")],
        env={**os.environ}, cwd=HERE)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = (await session.list_tools()).tools
            names = {t.name for t in tools}
            print("tools/list ->")
            for t in tools:
                print(f"  {t.name}: {(t.description or '').splitlines()[0]}")
            assert names == EXPECTED, f"unexpected tools: {names ^ EXPECTED}"
            bad = [n for n in names if "send" in n or "delete" in n]
            assert not bad, f"forbidden tools: {bad}"
            print("OK: exactly 6 tools, no send/delete tool.")
            if offline:
                return
            res = await session.call_tool("list_events", {"days_ahead": 1})
            print("tools/call list_events(days_ahead=1) ->")
            print("  " + res.content[0].text.replace("\n", "\n  "))


if __name__ == "__main__":
    asyncio.run(main("--offline" in sys.argv))
