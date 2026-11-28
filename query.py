import config
from common import typedb_request, handle_typedb_response


def query(query: str, database: str, transaction_type: str = "read") -> str:
    """Executes given TypeQL query against the given database.
    
    Args:
        query: TypeQL query to be executed
        database: The name of the database against which the query will be executed
        transaction_type: Transaction type - "read", "write", or "schema" (default: "read")
    
    Returns:
        Query results as JSON string
    
    Example:
        query("match $p isa person; fetch { $p.* };", "social_network")
    """
    if config.READ_ONLY and transaction_type != "read":
        raise ValueError("read-only mode: only transaction_type 'read' is allowed")
    response = typedb_request(
        "POST", "/v1/query",
        json={
            "databaseName": database,
            "transactionType": transaction_type,
            "query": query,
            "commit": transaction_type in ("write", "schema")
        }
    )
    handle_typedb_response(response)
    return response.text
