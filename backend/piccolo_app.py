"""
Piccolo app configuration.
"""

from piccolo.conf.apps import AppConfig, table_finder

APP_CONFIG = AppConfig(
    app_name="backend",
    migrations_folder_path="migrations",
    table_classes=table_finder(modules=["backend.db.tables"], exclude_imported=True),
    migration_dependencies=[],
    commands=[],
)
