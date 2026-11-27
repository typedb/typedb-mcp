import argparse
import os
import signal
import logging
from fastmcp import FastMCP
import config
from query import query as execute_query
from database import list_databases as db_list, create_database as db_create, delete_database as db_delete, database_schema as db_schema
from user import list_users as usr_list, create_user as usr_create, delete_user as usr_delete

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def query(query: str, database: str, transaction_type: str) -> str:
    """Executes given TypeQL query against the given database.
    
    Args:
        query: TypeQL query to be executed
        database: The name of the database against which the query will be executed
        transaction_type: Transaction type - "read" (for fetching data), "write" (for inserting data), or "schema" (for modifying the schema)
    
    Returns:
        Query results as JSON string
    
    Example:
        query("match $p isa person; fetch { $p.* };", "social_network")
    """
    return execute_query(query, database, transaction_type)


def database_list() -> str:
    """List all databases on the TypeDB server.
    
    Returns:
        JSON string containing list of databases
    """
    return db_list()


def database_create(name: str) -> str:
    """Create a new database on the TypeDB server.
    
    Args:
        name: Name of the database to create
    
    Returns:
        Success message
    """
    return db_create(name)


def database_delete(name: str) -> str:
    """Delete a database from the TypeDB server.
    
    Args:
        name: Name of the database to delete
    
    Returns:
        Success message
    """
    return db_delete(name)


def database_schema(name: str) -> str:
    """Get the complete database schema as TypeQL.
    
    Args:
        name: Name of the database
    
    Returns:
        Complete schema definition in TypeQL format (or empty string if no schema defined)
    """
    return db_schema(name)


def user_list() -> str:
    """List all users on the TypeDB server.
    
    Returns:
        JSON string containing list of users
    """
    return usr_list()


def user_create(username: str, password: str) -> str:
    """Create a new user on the TypeDB server.
    
    Args:
        username: Username for the new user
        password: Password for the new user
    
    Returns:
        Success message
    """
    return usr_create(username, password)


def user_delete(username: str) -> str:
    """Delete a user from the TypeDB server.
    
    Args:
        username: Username of the user to delete
    
    Returns:
        Success message
    """
    return usr_delete(username)


def build_server(read_only: bool = False) -> FastMCP:
    """Create the MCP server; in read-only mode only the read tools are registered."""
    mcp = FastMCP("TypeDB MCP Server")
    config.READ_ONLY = read_only  # one mode per process, like TYPEDB_URL
    for fn in (query, database_list, database_schema):
        mcp.tool(fn)
    if not read_only:
        for fn in (database_create, database_delete, user_list, user_create, user_delete):
            mcp.tool(fn)
    return mcp


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TypeDB MCP Server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Interface to bind (default: 127.0.0.1; use 0.0.0.0 inside a container)")
    parser.add_argument("--port", type=int, default=8001, help="Port for the MCP server (default: 8001)")
    parser.add_argument("--typedb-address", type=str, required=True, help="Address for TypeDB's HTTP port (e.g., http://localhost:8000)")
    parser.add_argument("--typedb-username", type=str, default="admin", help="TypeDB username (default: admin)")
    # No %(default)s here: --help must never print the password.
    parser.add_argument("--typedb-password", type=str, default=os.environ.get("TYPEDB_PASSWORD", "password"), help="TypeDB password (default: env TYPEDB_PASSWORD, else the TypeDB default)")
    parser.add_argument("--read-only", action="store_true", help="Register only read tools and allow only read transactions")
    return parser.parse_args(argv)


def main(argv=None) -> None:
    args = parse_args(argv)

    config.TYPEDB_URL = args.typedb_address
    config.TYPEDB_USERNAME = args.typedb_username
    config.TYPEDB_PASSWORD = args.typedb_password

    # Signal handler for graceful shutdown
    def handle_shutdown(signum, frame):
        logger.info("Received shutdown signal, initiating graceful shutdown...")

    # Register signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    # Run server with increased graceful shutdown timeout
    logger.info(f"Starting TypeDB MCP Server on {args.host}:{args.port}")
    logger.info(f"Connecting to TypeDB at {args.typedb_address}")
    build_server(args.read_only).run(transport="http", host=args.host, port=args.port, uvicorn_config={"timeout_graceful_shutdown": 30})


if __name__ == "__main__":
    main()
