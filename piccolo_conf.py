"""
Piccolo configuration file.
"""

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine
from backend.db.connection import DB

# App registry
APP_REGISTRY = AppRegistry(
    apps=[
        "backend.piccolo_app",
    ]
)

# Database engine
DB = DB
