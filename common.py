import logging
import requests
import config
from fastmcp import Context
from fastmcp.server.elicitation import (
    AcceptedElicitation,
    DeclinedElicitation,
    CancelledElicitation,
)

logger = logging.getLogger(__name__)


class ConfirmationDenied(Exception):
    """Raised when the user declines or cancels a confirmation prompt, or when
    the client does not support elicitation. The MCP server surfaces this back
    to the agent so it can report the operation as blocked."""


async def confirm_or_raise(ctx: Context, message: str) -> None:
    """Ask the user to confirm a destructive operation via MCP elicitation.

    Raises ConfirmationDenied if the user declines/cancels or the client does
    not support elicitation. Returns normally on accept.
    """
    try:
        result = await ctx.elicit(message=message, response_type=None)
    except Exception as e:
        logger.warning("Elicitation failed (client likely lacks support): %s", e)
        raise ConfirmationDenied(
            "This MCP client does not support confirmation prompts. "
            "Destructive operations are blocked. Use a client with MCP "
            "elicitation support (e.g. recent Claude Code)."
        ) from e

    if isinstance(result, AcceptedElicitation):
        return
    if isinstance(result, DeclinedElicitation):
        raise ConfirmationDenied("User declined the operation.")
    if isinstance(result, CancelledElicitation):
        raise ConfirmationDenied("User cancelled the operation.")
    raise ConfirmationDenied(f"Unexpected elicitation result: {result!r}")


def get_auth_token() -> str:
    """Sign in to TypeDB and get an access token."""
    response = requests.post(
        f"{config.TYPEDB_URL}/v1/signin",
        json={"username": config.TYPEDB_USERNAME, "password": config.TYPEDB_PASSWORD}
    )
    handle_typedb_response(response)
    return response.json()["token"]


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
