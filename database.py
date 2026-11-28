from urllib.parse import quote

from common import typedb_request, handle_typedb_response


def list_databases() -> str:
    """Get all databases present on the server."""
    response = typedb_request(
        "GET", "/v1/databases"
    )
    handle_typedb_response(response)
    return response.text


def create_database(name: str) -> str:
    """Create a database on the server."""
    response = typedb_request(
        "POST", f"/v1/databases/{quote(name, safe='')}"
    )
    handle_typedb_response(response)
    return f"Database '{name}' created successfully"


def delete_database(name: str) -> str:
    """Delete a database from the server."""
    response = typedb_request(
        "DELETE", f"/v1/databases/{quote(name, safe='')}"
    )
    handle_typedb_response(response)
    return f"Database '{name}' deleted successfully"


def database_schema(name: str) -> str:
    """Get the complete database schema as TypeQL."""
    response = typedb_request(
        "GET", f"/v1/databases/{quote(name, safe='')}/schema"
    )
    handle_typedb_response(response)
    return response.text
