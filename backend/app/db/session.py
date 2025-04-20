from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from sqlitedict import SqliteDict

# Create async engine
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create sessionmaker
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Dependency for database session
async def get_db():
    session = AsyncSessionLocal()
    try:
        yield session
    finally:
        await session.close()

# Create a SQLite database connection
db_name = "sessionData.sqlite" # this the chosen database name
oauth_store = SqliteDict(db_name, tablename="oauth_store", autocommit=True)
start_url_store = SqliteDict(db_name, tablename="start_url_store", autocommit=True)
screenname_store = SqliteDict(db_name, tablename="screenname_store ", autocommit=True)
userid_store = SqliteDict(db_name, tablename="userid_store ", autocommit=True)
worker_id_store = SqliteDict(db_name, tablename="worker_id_store ", autocommit=True)
access_token_store = SqliteDict(db_name, tablename="access_token_store ", autocommit=True)
access_token_secret_store = SqliteDict(db_name, tablename="access_token_secret_store", autocommit=True)
max_page_store = SqliteDict(db_name, tablename="max_page_store", autocommit=True)
session_id_store = SqliteDict(db_name, tablename="session_id_store", autocommit=True)
twitterversion_store = SqliteDict(db_name, tablename="twitterversion_store", autocommit=True)
mode_store = SqliteDict(db_name, tablename="mode_store", autocommit=True)
participant_id_store = SqliteDict(db_name, tablename="participant_id_store", autocommit=True)
assignment_id_store = SqliteDict(db_name, tablename="assignment_id_store", autocommit=True)
project_id_store = SqliteDict(db_name, tablename="project_id_store", autocommit=True)
hometimeline_pulled_store = SqliteDict(db_name, tablename="hometimeline_pulled_store", autocommit=True)
completed_survey = SqliteDict(db_name, tablename="completed_survey", autocommit=True)
experimental_condition = SqliteDict(db_name, tablename="experimental_condition", autocommit=True)
tweet_services_store = SqliteDict(db_name, tablename="tweet_services_store", autocommit=True)


def get_store(name) -> SqliteDict:
    """
        This function returns the database connection for the given name.
    """
    dbs = {
        "oauth_store": oauth_store,
        "start_url_store": start_url_store,
        "screenname_store": screenname_store,
        "userid_store": userid_store,
        "worker_id_store": worker_id_store,
        "access_token_store": access_token_store,
        "access_token_secret_store": access_token_secret_store,
        "max_page_store": max_page_store,
        "session_id_store": session_id_store,
        "twitterversion_store": twitterversion_store,
        "mode_store": mode_store,
        "participant_id_store": participant_id_store,
        "assignment_id_store": assignment_id_store,
        "project_id_store": project_id_store,
        "hometimeline_pulled_store": hometimeline_pulled_store,
        "completed_survey": completed_survey,
        "experimental_condition": experimental_condition,
        "tweet_services_store": tweet_services_store
    }
    if name in dbs:
        return dbs[name]
    else:
        raise ValueError(f"Database connection '{name}' not found.")

def close_stores() -> None:
    """
        This function closes all the tables connections to the sql database.
    """
    oauth_store.close()
    start_url_store.close()
    screenname_store.close()
    userid_store.close()
    worker_id_store.close()
    access_token_store.close()
    access_token_secret_store.close()
    max_page_store.close()
    session_id_store.close()
    twitterversion_store.close()
    mode_store.close()
    participant_id_store.close()
    assignment_id_store.close()
    project_id_store.close()
    completed_survey.close()
    experimental_condition.close()
    tweet_services_store.close()
