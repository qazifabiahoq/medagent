from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


def _normalize_postgres_url(url: str) -> str:
    return url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


def get_checkpointer_context(postgres_url: str):
    """Returns the async context manager — caller must use 'async with'."""
    conn_str = _normalize_postgres_url(postgres_url)
    return AsyncPostgresSaver.from_conn_string(conn_str)
