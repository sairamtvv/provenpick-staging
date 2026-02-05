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

    # Fetch ALL products linked to this article (not just top_pick/runner_up/budget_pick)
    all_products = (
        await StagingProductTable.select()
        .where(StagingProductTable.staging_article_id == staging_article_id)
        .run()
    )

    products = {}
    for product in all_products:
        pid = product["staging_product_id"]

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

        # If no images in StagingProductImageTable but image_url exists, use it
        if not product_images and product.get("image_url"):
            product_images = [
                {
                    "image_url": product["image_url"],
                    "alt_text": product.get("name", "Product image"),
                    "sequence_order": 0,
                }
            ]

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
    import asyncpg
    from datetime import datetime

    id_mapping = {
        "products": {},  # {staging_product_id: production_product_id}
        "article_id": 0,
    }

    # Connect to database
    conn = await asyncpg.connect(
        os.getenv(
            "DATABASE_URL",
            "postgresql://provenpick:provenpick@localhost:5432/provenpick",
        )
    )

    try:
        # Helper to get category ID
        async def get_category_id(category_name: str) -> int:
            if not category_name:
                return 4
            row = await conn.fetchrow(
                "SELECT category_table_id FROM public.category_table WHERE LOWER(name) = LOWER($1)",
                category_name,
            )
            return row["category_table_id"] if row else 4

        # 1. Insert products
        for staging_pid, product_data in full_data["products"].items():
            specs = product_data.get("specs", "{}")
            if isinstance(specs, str):
                specs = (
                    json.loads(specs.replace('\\"', '"').replace("\\\\", "\\"))
                    if specs
                    else {}
                )

            affiliate_links = product_data.get("affiliate_links", "{}")
            if isinstance(affiliate_links, str):
                affiliate_links = (
                    json.loads(
                        affiliate_links.replace('\\"', '"').replace("\\\\", "\\")
                    )
                    if affiliate_links
                    else {}
                )

            prod_category_name = product_data.get(
                "category", full_data["article"]["category"]
            )
            prod_category_id = await get_category_id(prod_category_name)

            prod_id = await conn.fetchval(
                """
                INSERT INTO public.product_table 
                (name, brand, category, price, description, image_url, specs, affiliate_links, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING product_table_id
                """,
                product_data["name"],
                product_data["brand"],
                prod_category_id,
                float(product_data["price"]),
                product_data["description"],
                product_data["image_url"],
                json.dumps(specs),
                json.dumps(affiliate_links),
                datetime.now(),
                datetime.now(),
            )
            id_mapping["products"][str(staging_pid)] = prod_id

            # Images
            for img in product_data.get("images", []):
                await conn.execute(
                    """
                    INSERT INTO public.product_image_table (product, image_url, alt_text, sequence_order, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    prod_id,
                    img["image_url"],
                    img.get("alt_text"),
                    img.get("sequence_order", 0),
                    datetime.now(),
                )

            # Texts
            for txt in product_data.get("texts", []):
                await conn.execute(
                    """
                    INSERT INTO public.product_text_table (product, content, heading, sequence_order, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    prod_id,
                    txt["content"],
                    txt.get("heading"),
                    txt.get("sequence_order", 0),
                    datetime.now(),
                )

        # 2. Insert article
        article = full_data["article"]
        top_pick_id = id_mapping["products"].get(str(article["top_pick_staging_id"]))
        runner_up_id = (
            id_mapping["products"].get(str(article.get("runner_up_staging_id")))
            if article.get("runner_up_staging_id")
            else None
        )
        budget_pick_id = (
            id_mapping["products"].get(str(article.get("budget_pick_staging_id")))
            if article.get("budget_pick_staging_id")
            else None
        )

        article_id = await conn.fetchval(
            """
            INSERT INTO public.article_table (title, category, author, top_pick, runner_up, budget_pick, created_at, updated_at)
            VALUES ($1, $2, NULL, $3, $4, $5, $6, $7)
            RETURNING article_table_id
            """,
            article["title"],
            article["category"],
            top_pick_id,
            runner_up_id,
            budget_pick_id,
            datetime.now(),
            datetime.now(),
        )
        id_mapping["article_id"] = article_id

        # Article Images
        for img in full_data.get("article_images", []):
            await conn.execute(
                """
                INSERT INTO public.article_image_table (article, image_url, alt_text, image_type, sequence_order, created_at)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                article_id,
                img["image_url"],
                img.get("alt_text"),
                img["image_type"],
                img.get("sequence_order", 0),
                datetime.now(),
            )

        # Article Texts
        for txt in full_data.get("article_texts", []):
            await conn.execute(
                """
                INSERT INTO public.article_text_table (article, content, section_type, sequence_order, created_at)
                VALUES ($1, $2, $3, $4, $5)
                """,
                article_id,
                txt["content"],
                txt["section_type"],
                txt.get("sequence_order", 0),
                datetime.now(),
            )

        return id_mapping

    finally:
        await conn.close()


async def publish_rejection_event(data: Dict[str, Any]):
    """
    Publish rejection event to Redis queue for external processing.
    """
    import redis.asyncio as redis

    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        client = redis.from_url(redis_url)

        # Check connection
        await client.ping()

        # Publish to queue
        queue_name = os.getenv("REJECTION_QUEUE", "rejected_articles_queue")
        await client.lpush(queue_name, json.dumps(data, default=str))
        print(f"Published rejection event to {queue_name}")

        await client.aclose()
    except Exception as e:
        print(f"Warning: Failed to publish to Redis: {e}")


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

    # If rejected, publish to queue
    if action == "rejected":
        event_data = {
            "event": "article_rejected",
            "staging_id": staging_article_id,
            "title": full_data["article"]["title"],
            "category": full_data["article"]["category"],
            "comments": comments,
            "rejected_at": datetime.now().isoformat(),
            "full_data": full_data,
        }
        await publish_rejection_event(event_data)

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
        migration_success = False
        migration_error_msg = None
        try:
            id_mapping = await migrate_to_production(full_data)
            migration_success = True
        except Exception as migration_error:
            # Log error but continue with archiving
            migration_error_msg = str(migration_error)
            print(f"Warning: Production migration failed: {migration_error}")
            id_mapping = None

        # 3. Archive the staging data
        archive_id = await archive_staging_data(
            staging_article_id=staging_article_id,
            full_data=full_data,
            action="approved",
        )

        # 4. Delete from staging
        product_ids = list(full_data["products"].keys())
        await delete_staging_data(staging_article_id, product_ids)

        if migration_success:
            return {
                "success": True,
                "archive_id": archive_id,
                "production_article_id": id_mapping.get("article_id")
                if id_mapping
                else None,
                "message": "Article approved, migrated to production, and archived",
            }
        else:
            return {
                "success": True,
                "archive_id": archive_id,
                "message": f"Article approved and archived (migration failed: {migration_error_msg})",
            }

    except Exception as e:
        return {"success": False, "error": str(e)}
