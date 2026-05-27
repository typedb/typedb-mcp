import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MCP_URL = "http://localhost:8001/mcp"
DB_NAME = "assembly_test"


async def call(session: ClientSession, name: str, args: dict) -> str:
    result = await session.call_tool(name, args)
    return result.content[0].text


async def main():
    async with streamablehttp_client(MCP_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print(await call(session, "database_create", {"name": DB_NAME}))

            await call(session, "query", {
                "query": "define entity person;",
                "database": DB_NAME,
                "transaction_type": "schema",
            })

            await call(session, "query", {
                "query": "insert $p isa person;",
                "database": DB_NAME,
                "transaction_type": "write",
            })

            read_result = await call(session, "query", {
                "query": "match $p isa person;",
                "database": DB_NAME,
                "transaction_type": "read",
            })
            print("Query result:", read_result)

            schema = await call(session, "database_schema", {"name": DB_NAME})
            print("Schema:")
            print(schema)


if __name__ == "__main__":
    asyncio.run(main())
