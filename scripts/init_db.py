"""
Initialize staging database schema.
Run this script once to create the staging schema.
"""

import asyncio
from piccolo.conf.apps import Finder
from piccolo.table import create_db_tables_sync
from backend.db.connection import DB


async def init_db():
    """Initialize database schema"""

    print("Creating staging schema...")

    # Create schema
    await DB.run_ddl("CREATE SCHEMA IF NOT EXISTS staging;")

    print("Staging schema created successfully!")
    print("\nNext steps:")
    print("1. Run: piccolo migrations forwards all")
    print("2. Configure your .env file")
    print("3. Start the backend: python backend/main.py")
    print("4. Start the frontend: reflex run")


if __name__ == "__main__":
    asyncio.run(init_db())
