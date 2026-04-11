from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver


def _normalize_postgres_url(url: str) -> str:
    """Strip SQLAlchemy driver prefix so psycopg3 can parse the URL."""
    return url.replace("postgresql+asyncpg://", "postgresql://").replace(
        "postgresql+psycopg2://", "postgresql://"
    )


async def create_checkpointer(postgres_url: str) -> AsyncPostgresSaver:
    """
    Create and initialise an AsyncPostgresSaver checkpointer.
    Caller is responsible for managing the lifecycle (use as async context manager
    or call aclose() when done).
    """
    conn_str = _normalize_postgres_url(postgres_url)
    checkpointer = await AsyncPostgresSaver.from_conn_string(conn_str)
    await checkpointer.setup()
    return checkpointer
