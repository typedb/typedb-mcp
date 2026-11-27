[![TypeDB MCP on mcprush](https://mcprush.com/badge/typedb-mcp/score.svg)](https://mcprush.com/to/typedb-mcp?ref=badge)

# TypeDB MCP Server

An MCP (Model Context Protocol) server that enables AI assistants to interact with [TypeDB](https://typedb.com) databases. This allows LLMs to execute TypeQL queries, manage databases, and manage users through natural language.

Available on Docker Hub: https://hub.docker.com/repository/docker/typedb/typedb-mcp

## Features

- **Query Execution**: Run TypeQL read, write, and schema queries
- **Database Management**: List, create, and delete databases
- **User Management**: List, create, and delete users

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

## Options

| Option | Default | Meaning |
| --- | --- | --- |
| `--typedb-address` | required | TypeDB HTTP address, e.g. `http://localhost:8000` |
| `--typedb-username` | `admin` | TypeDB user |
| `--typedb-password` | env `TYPEDB_PASSWORD`, else `password` | TypeDB password; prefer the environment variable so the password stays out of the process list |
| `--host` | `127.0.0.1` | Interface to bind. The Docker image passes `--host 0.0.0.0` (needed inside a container), so container use is unchanged; publish the port on the host loopback, see below |
| `--port` | `8001` | MCP server port |
| `--read-only` | off | Register only `query`, `database_list` and `database_schema`; `query` accepts only `transaction_type` `read`. Write, schema and user tools are not available |
| `--no-token-reuse` | off | Sign in on every request instead of reusing one token |

The server reuses one TypeDB token. TypeDB invalidates tokens when it restarts, so on an HTTP 401 the server signs in once more and retries the request once. Use `--no-token-reuse` to sign in per request instead.

Read-only server on the loopback interface of the Docker host:

```bash
docker run -p 127.0.0.1:8001:8001 -e TYPEDB_PASSWORD=<password> typedb/typedb-mcp:<version> \
  --typedb-address http://host.docker.internal:8000 \
  --read-only
```

The MCP routes are not protected by authentication, so keep the published port on `127.0.0.1` unless something else guards it.

## Tests

```bash
uv run pytest                 # unit tests, no TypeDB needed
TYPEDB_IT_URL=http://localhost:8000 TYPEDB_PASSWORD=<password> uv run pytest -m integration
```

Integration tests need a running TypeDB and create throwaway databases.

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
