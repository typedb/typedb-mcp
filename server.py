import argparse
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

mcp = FastMCP(
    "TypeDB MCP Server",
    # description="Provides query capability against a TypeDB server"
)

@mcp.tool
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


@mcp.tool
def database_list() -> str:
    """List all databases on the TypeDB server.
    
    Returns:
        JSON string containing list of databases
    """
    return db_list()


@mcp.tool
def database_create(name: str) -> str:
    """Create a new database on the TypeDB server.
    
    Args:
        name: Name of the database to create
    
    Returns:
        Success message
    """
    return db_create(name)


@mcp.tool
def database_delete(name: str) -> str:
    """Delete a database from the TypeDB server.
    
    Args:
        name: Name of the database to delete
    
    Returns:
        Success message
    """
    return db_delete(name)


@mcp.tool
def database_schema(name: str) -> str:
    """Get the complete database schema as TypeQL.
    
    Args:
        name: Name of the database
    
    Returns:
        Complete schema definition in TypeQL format (or empty string if no schema defined)
    """
    return db_schema(name)


@mcp.tool
def user_list() -> str:
    """List all users on the TypeDB server.
    
    Returns:
        JSON string containing list of users
    """
    return usr_list()


@mcp.tool
def user_create(username: str, password: str) -> str:
    """Create a new user on the TypeDB server.
    
    Args:
        username: Username for the new user
        password: Password for the new user
    
    Returns:
        Success message
    """
    return usr_create(username, password)


@mcp.tool
def user_delete(username: str) -> str:
    """Delete a user from the TypeDB server.
    
    Args:
        username: Username of the user to delete
    
    Returns:
        Success message
    """
    return usr_delete(username)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TypeDB MCP Server")
    parser.add_argument("--port", type=int, default=8001, help="Port for the MCP server (default: 8001)")
    parser.add_argument("--typedb-address", type=str, required=True, help="Address for TypeDB's HTTP port (e.g., http://localhost:8000)")
    parser.add_argument("--typedb-username", type=str, default="admin", help="TypeDB username (default: admin)")
    parser.add_argument("--typedb-password", type=str, default="password", help="TypeDB password (default: password)")
    
    args = parser.parse_args()
    
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
    logger.info(f"Starting TypeDB MCP Server on port {args.port}")
    logger.info(f"Connecting to TypeDB at {args.typedb_address}")
    mcp.run(transport="http", host="0.0.0.0", port=args.port, uvicorn_config={"timeout_graceful_shutdown": 30})

