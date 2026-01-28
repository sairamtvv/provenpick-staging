"""
Database connection configuration for Piccolo ORM.
"""

import os
from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database connection
DB = PostgresEngine(
    config={
        "database": os.getenv("DB_NAME", "provenpick"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
    }
)
