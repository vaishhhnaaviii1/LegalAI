import asyncio
from logging.config import fileConfig
import urllib.parse  # NEW IMPORT

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
# ==========================================
# 1. IMPORT YOUR APP'S CONFIG AND MODELS
# ==========================================
from sqlmodel import SQLModel
from app.core.config import settings
import app.models# This forces SQLModel to read your tables!

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# ==========================================
# SAFELY ENCODE THE DATABASE URL
# ==========================================
# 1. Break the URL apart
parsed_url = urllib.parse.urlparse(settings.DATABASE_URL)

# 2. Safely encode the password
encoded_password = urllib.parse.quote(parsed_url.password)

# 3. Put the URL back together
safe_url = f"{parsed_url.scheme}://{parsed_url.username}:{encoded_password}@{parsed_url.hostname}:{parsed_url.port}{parsed_url.path}"

# 4. Pass the safe URL to Alembic!
# (Notice we also have to escape the % symbol by making it %% so configparser doesn't crash)
config.set_main_option("sqlalchemy.url", safe_url.replace('%', '%%'))



# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
# ==========================================
# 3. SET THE TARGET METADATA TO SQLMODEL
# ==========================================
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
