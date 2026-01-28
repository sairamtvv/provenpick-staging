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
    from backend.db.connection import DB
    from datetime import datetime

    id_mapping = {
        "products": {},  # {staging_product_id: production_product_id}
        "article_id": 0,
    }

    # Note: category handling - we'll use category name as string for now
    # In future, should look up category_table_id

    # 1. Insert products into production
    for staging_pid, product_data in full_data["products"].items():
        # Insert product into public.product_table
        insert_product_sql = """
            INSERT INTO public.product_table 
            (name, brand, category, price, description, image_url, specs, affiliate_links, created_at, updated_at)
            VALUES ($1, $2, 1, $3, $4, $5, $6, $7, $8, $9)
            RETURNING product_table_id
        """

        result = await DB.run_ddl(
            insert_product_sql,
            product_data["name"],
            product_data["brand"],
            # category=1 is a placeholder - should lookup CategoryTable
            product_data["price"],
            product_data["description"],
            product_data["image_url"],
            product_data["specs"],
            product_data["affiliate_links"],
            product_data.get("created_at", datetime.now()),
            datetime.now(),
        )

        # Get the newly created product_id
        prod_id_result = await DB.run_sync(
            f"SELECT product_table_id FROM public.product_table WHERE name = '{product_data['name']}' ORDER BY created_at DESC LIMIT 1"
        )
        prod_id = prod_id_result[0]["product_table_id"] if prod_id_result else 0

        id_mapping["products"][staging_pid] = prod_id

        # Insert product images
        for img in product_data.get("images", []):
            await DB.run_ddl(
                """
                INSERT INTO public.product_image_table 
                (product, image_url, alt_text, sequence_order, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                prod_id,
                img["image_url"],
                img.get("alt_text"),
                img.get("sequence_order", 0),
                img.get("created_at", datetime.now()),
            )

        # Insert product texts
        for txt in product_data.get("texts", []):
            await DB.run_ddl(
                """
                INSERT INTO public.product_text_table 
                (product, content, heading, sequence_order, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                prod_id,
                txt["content"],
                txt.get("heading"),
                txt.get("sequence_order", 0),
                txt.get("created_at", datetime.now()),
            )

    # 2. Insert article into production
    article = full_data["article"]

    # Map staging product IDs to production product IDs
    top_pick_id = id_mapping["products"].get(article["top_pick_staging_id"])
    runner_up_id = id_mapping["products"].get(article.get("runner_up_staging_id"))
    budget_pick_id = id_mapping["products"].get(article.get("budget_pick_staging_id"))

    insert_article_sql = """
        INSERT INTO public.article_table 
        (title, category, author, top_pick, runner_up, budget_pick, created_at, updated_at)
        VALUES ($1, $2, NULL, $3, $4, $5, $6, $7)
        RETURNING article_table_id
    """

    await DB.run_ddl(
        insert_article_sql,
        article["title"],
        article["category"],
        top_pick_id,
        runner_up_id,
        budget_pick_id,
        article.get("created_at", datetime.now()),
        datetime.now(),
    )

    # Get the newly created article_id
    article_id_result = await DB.run_sync(
        f"SELECT article_table_id FROM public.article_table WHERE title = '{article['title']}' ORDER BY created_at DESC LIMIT 1"
    )
    article_id = article_id_result[0]["article_table_id"] if article_id_result else 0
    id_mapping["article_id"] = article_id

    # 3. Insert article images
    for img in full_data.get("article_images", []):
        await DB.run_ddl(
            """
            INSERT INTO public.article_image_table 
            (article, image_url, alt_text, image_type, sequence_order, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            article_id,
            img["image_url"],
            img.get("alt_text"),
            img["image_type"],
            img.get("sequence_order", 0),
            img.get("created_at", datetime.now()),
        )

    # 4. Insert article texts
    for txt in full_data.get("article_texts", []):
        await DB.run_ddl(
            """
            INSERT INTO public.article_text_table 
            (article, content, section_type, sequence_order, created_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            article_id,
            txt["content"],
            txt["section_type"],
            txt.get("sequence_order", 0),
            txt.get("created_at", datetime.now()),
        )

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
