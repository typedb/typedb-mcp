# TypeDB MCP Server

An MCP (Model Context Protocol) server that enables AI assistants to interact with [TypeDB](https://typedb.com) databases. This allows LLMs to execute TypeQL queries, manage databases, and manage users through natural language.

## Features

- **Query Execution**: Run TypeQL read, write, and schema queries
- **Database Management**: List, create, and delete databases
- **User Management**: List, create, and delete users
- **Confirmation prompts**: Write/schema queries and all destructive admin operations require explicit user approval before they reach TypeDB (see below)

## Confirmation prompts

Any operation that can mutate state — write/schema queries, database creation/deletion, user creation/deletion — pauses and asks the human user to approve before running. The exact query (or operation) is shown verbatim in the prompt. This uses the MCP **elicitation** primitive, so the request comes from the server and is rendered by the client; the agent cannot bypass it.

Read queries (`transaction_type: "read"`) and read-only listings (`database_list`, `database_schema`, `user_list`) run without prompting.

If your MCP client does not support elicitation, mutating operations will be blocked entirely and the agent will receive a "not executed" response. Confirmed support: recent Claude Code. Other clients may vary.

## Running the Server

```bash
docker run -p 8001:8001 typedb/typedb-mcp:<version> \
  --typedb-address <address> \
  --typedb-username <username> \
  --typedb-password <password>
```

If you're running TypeDB server on `localhost`:
- replace `<address>` with `http://host.docker.internal:8000` instead of `http://localhost:8000`
- on Linux, add `--add-host=host.docker.internal:host-gateway`

## Using with Cursor IDE

1. Start the MCP server (see above)

2. Open Cursor Settings → MCP

3. Add the server configuration. Create or edit `.cursor/mcp.json` in your project:

```json
{
  "mcpServers": {
    "typedb": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

4. Restart Cursor or refresh MCP connections

5. Start chatting! You can now ask Cursor to:
   - "List all databases"
   - "Create a database called 'mydb'"
   - "Define an entity 'person' with attribute 'name' in database 'mydb'"
   - "Insert a person with name 'Alice'"
   - "Query all persons in the database"

## Building from Source

Use `podman` or `Docker` to create a Docker image and push it to DockerHub:

```bash
podman login docker.io

VERSION=<desired version number>
podman build -t typedb/typedb-mcp:$VERSION .
podman push typedb/typedb-mcp:$VERSION
```