from common import typedb_request, handle_typedb_response


def list_users() -> str:
    """Get all users present on the server."""
    response = typedb_request(
        "GET", "/v1/users"
    )
    handle_typedb_response(response)
    return response.text


def create_user(username: str, password: str) -> str:
    """Create a new user on the server."""
    response = typedb_request(
        "POST", f"/v1/users/{username}",
        json={"password": password}
    )
    handle_typedb_response(response)
    return f"User '{username}' created successfully"


def delete_user(username: str) -> str:
    """Delete a user from the server."""
    response = typedb_request(
        "DELETE", f"/v1/users/{username}"
    )
    handle_typedb_response(response)
    return f"User '{username}' deleted successfully"
