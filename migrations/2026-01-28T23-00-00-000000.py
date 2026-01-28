"""
Auto-generated migration for staging tables.
ID: 2026-01-28T23:00:00:000000
"""

from piccolo.apps.migrations.auto.migration_manager import MigrationManager
from piccolo.columns import (
    Serial,
    Varchar,
    Text,
    Float,
    JSONB,
    Timestamp,
    Integer,
    Boolean,
)


ID = "2026-01-28T23:00:00:000000"
VERSION = "1.30.0"
DESCRIPTION = "Create staging tables"


async def forwards():
    manager = MigrationManager(
        migration_id=ID, app_name="backend", description=DESCRIPTION
    )

    # Create staging_product table
    manager.add_table(
        class_name="StagingProductTable",
        tablename="staging_product",
        schema="staging",
        columns=None,
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="staging_product_id",
        db_column_name="staging_product_id",
        column_class_name="Serial",
        column_class=Serial,
        params={
            "default": 0,
            "null": False,
            "primary_key": True,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="name",
        db_column_name="name",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 255,
            "default": "",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="brand",
        db_column_name="brand",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 100,
            "default": "",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="category",
        db_column_name="category",
        column_class_name="Varchar",
        column_class=Varchar,
        params={
            "length": 100,
            "default": "",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="price",
        db_column_name="price",
        column_class_name="Float",
        column_class=Float,
        params={
            "default": 0.0,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="description",
        db_column_name="description",
        column_class_name="Text",
        column_class=Text,
        params={
            "default": "",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="image_url",
        db_column_name="image_url",
        column_class_name="Text",
        column_class=Text,
        params={
            "default": "",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="specs",
        db_column_name="specs",
        column_class_name="JSONB",
        column_class=JSONB,
        params={
            "default": "{}",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="affiliate_links",
        db_column_name="affiliate_links",
        column_class_name="JSONB",
        column_class=JSONB,
        params={
            "default": "{}",
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="staging_article_id",
        db_column_name="staging_article_id",
        column_class_name="Integer",
        column_class=Integer,
        params={
            "default": 0,
            "null": True,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    manager.add_column(
        table_class_name="StagingProductTable",
        tablename="staging_product",
        column_name="created_at",
        db_column_name="created_at",
        column_class_name="Timestamp",
        column_class=Timestamp,
        params={
            "default": None,
            "null": False,
            "primary_key": False,
            "unique": False,
            "index": False,
            "index_method": "btree",
            "choices": None,
            "db_column_name": None,
            "secret": False,
        },
        schema="staging",
    )

    # TODO: Add other tables (staging_article, staging_article_image, etc.)
    # For now, let's create tables directly using SQL

    return manager
