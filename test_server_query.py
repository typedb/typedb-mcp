"""Manual smoke tests for the MCP server tools, including the elicitation
confirmation gate. Run against a TypeDB instance that has a database named
'test2'. The decline scenario does not require TypeDB to be reachable."""

import asyncio
from fastmcp import Client
from fastmcp.client.elicitation import ElicitResult
from server import mcp


async def auto_accept(message, response_type, params, context):
    print(f"[elicit/accept] {message}")
    return ElicitResult(action="accept", content={})


async def auto_decline(message, response_type, params, context):
    print(f"[elicit/decline] {message}")
    return ElicitResult(action="decline", content=None)


async def read_query():
    async with Client(mcp) as client:
        result = await client.call_tool("query", {
            "query": "match $p isa person;",
            "database": "test2",
            "transaction_type": "read",
        })
        print("read query result:", result.content[0].text)


async def write_query_accepted():
    async with Client(mcp, elicitation_handler=auto_accept) as client:
        result = await client.call_tool("query", {
            "query": "insert $p isa person, has name 'test';",
            "database": "test2",
            "transaction_type": "write",
        })
        print("write query result (accepted):", result.content[0].text)


async def write_query_declined():
    async with Client(mcp, elicitation_handler=auto_decline) as client:
        result = await client.call_tool("query", {
            "query": "match $p isa person; delete $p;",
            "database": "test2",
            "transaction_type": "write",
        })
        print("write query result (declined):", result.content[0].text)


async def main():
    await read_query()
    await write_query_accepted()
    await write_query_declined()


if __name__ == "__main__":
    asyncio.run(main())
