"""
Database connection configuration for Piccolo ORM.
"""

import os
from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

# Load environment variables (dotenv is optional)
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

# Database connection
DB = PostgresEngine(
    config={
        "database": os.getenv("DB_NAME", "provenpick"),
        "user": os.getenv("DB_USER", "provenpick"),
        "password": os.getenv("DB_PASSWORD", "provenpick"),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
    }
)
