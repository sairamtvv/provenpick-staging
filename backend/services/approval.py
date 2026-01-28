"""
Approval workflow service.
Handles the process of approving staging articles and moving them to production.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from backend.db.tables import (
    StagingArticleTable,
    StagingProductTable,
    StagingArticleImageTable,
    StagingArticleTextTable,
    StagingProductImageTable,
    StagingProductTextTable,
    ArchiveTable,
)
from piccolo.engine import engine_finder


# Get references to production tables (from main DB, public schema)
# We'll import these at runtime to avoid circular dependencies
def get_production_tables():
    """Dynamically import production tables"""
    # TODO: When integrating with main DB, import actual tables from main repo
    # For now, we'll use placeholder imports
    # from infrastructure.db.tables import (
    #     ProductTable, ArticleTable, ProductImageTable,
    #     ProductTextTable, ArticleImageTable, ArticleTextTable
    # )
    pass


async def fetch_full_staging_article(
    staging_article_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Fetch complete staging article with all related data.

    Args:
        staging_article_id: ID of the staging article

    Returns:
        Dictionary containing article and all related products, images, texts
    """
    # Fetch article
    article = (
        await StagingArticleTable.select()
        .where(StagingArticleTable.staging_article_id == staging_article_id)
        .first()
        .run()
    )

    if not article:
        return None

    # Fetch products
    product_ids = [article["top_pick_staging_id"]]
    if article["runner_up_staging_id"]:
        product_ids.append(article["runner_up_staging_id"])
    if article["budget_pick_staging_id"]:
        product_ids.append(article["budget_pick_staging_id"])

    products = {}
    for pid in product_ids:
        product = (
            await StagingProductTable.select()
            .where(StagingProductTable.staging_product_id == pid)
            .first()
            .run()
        )

        if product:
            # Fetch product images
            product_images = (
                await StagingProductImageTable.select()
                .where(StagingProductImageTable.staging_product_id == pid)
                .order_by(StagingProductImageTable.sequence_order)
                .run()
            )

            # Fetch product texts
            product_texts = (
                await StagingProductTextTable.select()
                .where(StagingProductTextTable.staging_product_id == pid)
                .order_by(StagingProductTextTable.sequence_order)
                .run()
            )

            products[pid] = {
                **product,
                "images": product_images,
                "texts": product_texts,
            }

    # Fetch article images
    article_images = (
        await StagingArticleImageTable.select()
        .where(StagingArticleImageTable.staging_article_id == staging_article_id)
        .order_by(StagingArticleImageTable.sequence_order)
        .run()
    )

    # Fetch article texts
    article_texts = (
        await StagingArticleTextTable.select()
        .where(StagingArticleTextTable.staging_article_id == staging_article_id)
        .order_by(StagingArticleTextTable.sequence_order)
        .run()
    )

    return {
        "article": article,
        "products": products,
        "article_images": article_images,
        "article_texts": article_texts,
    }


async def migrate_to_production(full_data: Dict[str, Any]) -> Dict[str, int]:
    """
    Migrate staging data to production database.

    Args:
        full_data: Complete article + products data from staging

    Returns:
        Dictionary mapping staging IDs to production IDs
    """
    # TODO: Implement actual migration to production tables
    # This is a placeholder that shows the structure

    # This function would:
    # 1. Insert products into public.product_table
    # 2. Insert product images/texts
    # 3. Insert article into public.article_table
    # 4. Insert article images/texts
    # 5. Return mapping of staging_id -> production_id

    # Placeholder return
    id_mapping = {
        "products": {},  # {staging_product_id: production_product_id}
        "article_id": 0,
    }

    # Example structure:
    # for staging_pid, product_data in full_data["products"].items():
    #     # Insert into production
    #     prod_id = await insert_into_production_product(product_data)
    #     id_mapping["products"][staging_pid] = prod_id

    return id_mapping


async def archive_staging_data(
    staging_article_id: int,
    full_data: Dict[str, Any],
    action: str = "approved",
    comments: Optional[str] = None,
) -> int:
    """
    Archive the staging data.

    Args:
        staging_article_id: ID of the staging article
        full_data: Complete staging data to archive
        action: 'approved' or 'rejected'
        comments: Optional reviewer comments

    Returns:
        Archive ID
    """
    retention_days = int(os.getenv("ARCHIVE_RETENTION_DAYS", "90"))
    retention_until = datetime.now() + timedelta(days=retention_days)

    result = await ArchiveTable.insert(
        ArchiveTable(
            staging_article_id=staging_article_id,
            action=action,
            article_data=full_data,
            reviewer_comments=comments,
            archived_at=datetime.now(),
            retention_until=retention_until,
        )
    ).run()

    return result[0]["archive_id"]


async def delete_staging_data(staging_article_id: int, product_ids: List[int]):
    """
    Delete staging data after approval/archival.

    Args:
        staging_article_id: ID of the staging article
        product_ids: List of staging product IDs to delete
    """
    # Delete article images
    await (
        StagingArticleImageTable.delete()
        .where(StagingArticleImageTable.staging_article_id == staging_article_id)
        .run()
    )

    # Delete article texts
    await (
        StagingArticleTextTable.delete()
        .where(StagingArticleTextTable.staging_article_id == staging_article_id)
        .run()
    )

    # Delete article
    await (
        StagingArticleTable.delete()
        .where(StagingArticleTable.staging_article_id == staging_article_id)
        .run()
    )

    # Delete products and their children
    for pid in product_ids:
        await (
            StagingProductImageTable.delete()
            .where(StagingProductImageTable.staging_product_id == pid)
            .run()
        )

        await (
            StagingProductTextTable.delete()
            .where(StagingProductTextTable.staging_product_id == pid)
            .run()
        )

        await (
            StagingProductTable.delete()
            .where(StagingProductTable.staging_product_id == pid)
            .run()
        )


async def approve_article(
    staging_article_id: int, reviewer_token: str
) -> Dict[str, Any]:
    """
    Main approval workflow.

    Args:
        staging_article_id: ID of the staging article to approve
        reviewer_token: Token of the reviewer

    Returns:
        Result dictionary with success status and details
    """
    try:
        # 1. Fetch complete staging data
        full_data = await fetch_full_staging_article(staging_article_id)
        if not full_data:
            return {"success": False, "error": "Article not found"}

        # Check if already processed
        article = full_data["article"]
        if article["status"] != "pending":
            return {"success": False, "error": f"Article already {article['status']}"}

        # 2. Migrate to production
        id_mapping = await migrate_to_production(full_data)

        # 3. Archive the staging data
        archive_id = await archive_staging_data(
            staging_article_id=staging_article_id,
            full_data=full_data,
            action="approved",
        )

        # 4. Delete from staging
        product_ids = list(full_data["products"].keys())
        await delete_staging_data(staging_article_id, product_ids)

        return {
            "success": True,
            "archive_id": archive_id,
            "production_article_id": id_mapping.get("article_id"),
            "message": "Article approved and moved to production",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
