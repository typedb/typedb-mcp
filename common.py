import requests
import config
import json


def get_auth_token() -> str:
    """Sign in to TypeDB and get an access token."""
    response = requests.post(
        f"{config.TYPEDB_URL}/v1/signin",
        json={"username": config.TYPEDB_USERNAME, "password": config.TYPEDB_PASSWORD},
        timeout=10,
    )
    handle_typedb_response(response)
    return response.json()["token"]


# Cached token, shared between threads. typedb_request reads it into a local variable
# and only writes it to publish a fresh one; two threads signing in at once yields two valid tokens.
_token: str | None = None


def typedb_request(method: str, path: str, timeout: float = 60, **kwargs) -> requests.Response:
    """Call the TypeDB HTTP API with a reused token; on HTTP 401 sign in once more and retry once."""
    global _token
    token = _token if config.TOKEN_REUSE else None
    for attempt in (0, 1):
        if token is None:
            token = get_auth_token()
            if config.TOKEN_REUSE:
                _token = token
        response = requests.request(
            method, config.TYPEDB_URL + path,
            headers={"Authorization": f"Bearer {token}"}, timeout=timeout, **kwargs,
        )
        if response.status_code == 401 and attempt == 0:
            token = None  # token expired or TypeDB restarted
            if config.TOKEN_REUSE:
                _token = None
            continue
        return response
    return response


def handle_typedb_response(response: requests.Response) -> None:
    """Check response status and raise an error with TypeDB error details if needed.
    
    This ensures that TypeDB error messages are properly extracted from the response
    and propagated to the MCP client.
    
    Args:
        response: The requests.Response object to check
        
    Raises:
        requests.HTTPError: If the response status indicates an error, with TypeDB error details included
    """
    try:
        response.raise_for_status()
    except requests.HTTPError as e:
        # Try to extract error details from TypeDB response
        error_data = response.json()
        http_error = requests.HTTPError(error_data, response=response)
        raise http_error from e
