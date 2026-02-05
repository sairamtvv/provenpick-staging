"""
Redis Queue Consumer Service

Consumes articles from the workflow queue and inserts them into the staging database.
Run this as a background service.
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional

import redis

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Redis configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
SUBMIT_QUEUE = os.getenv("SUBMIT_QUEUE", "provenpick:submit_to_staging")


def get_redis_client():
    """Get Redis client"""
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


async def insert_article_to_staging(article_data: Dict[str, Any]) -> Optional[int]:
    """
    Insert article into staging database.

    Args:
        article_data: Article data from workflow

    Returns:
        Staging article ID if successful
    """
    from backend.db.tables import (
        StagingArticleTable,
        StagingProductTable,
        StagingArticleTextTable,
        StagingArticleImageTable,
    )

    try:
        article_uuid = article_data.get("article_uuid")
        l3_category_id = article_data.get("l3_category_id")
        products = article_data.get("products", [])
        content = article_data.get("content", {})
        sources = article_data.get("sources", [])

        logger.info(f"Inserting article {article_uuid} with {len(products)} products")

        # Create the staging article
        article = StagingArticleTable(
            workflow_uuid=article_uuid,
            title=f"Review: Category {l3_category_id}",  # Will be updated during review
            category=str(l3_category_id),
            status="pending",
            submitted_at=datetime.now(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
            top_pick_staging_id=0,  # Will be updated after products are created
        )

        await article.save()
        article_id = article._meta.primary_key

        # Get the actual ID
        saved_article = (
            await StagingArticleTable.select(StagingArticleTable.staging_article_id)
            .where(StagingArticleTable.workflow_uuid == article_uuid)
            .first()
        )

        if saved_article:
            article_id = saved_article["staging_article_id"]

        logger.info(f"Created staging article with ID: {article_id}")

        # Insert article text content
        if content:
            # Main article HTML
            article_text = StagingArticleTextTable(
                staging_article_id=article_id,
                content=content.get("full_article_html", ""),
                section_type="full_article",
                sequence_order=0,
                created_at=datetime.now(),
            )
            await article_text.save()

            # Bullet points as separate section
            bullets = content.get("bullet_points", [])
            if bullets:
                bullets_text = StagingArticleTextTable(
                    staging_article_id=article_id,
                    content=json.dumps(bullets),
                    section_type="bullet_points",
                    sequence_order=1,
                    created_at=datetime.now(),
                )
                await bullets_text.save()

            # Mindmap
            mindmap = content.get("mindmap_mermaid", "")
            if mindmap:
                mindmap_text = StagingArticleTextTable(
                    staging_article_id=article_id,
                    content=mindmap,
                    section_type="mindmap_summary",
                    sequence_order=2,
                    created_at=datetime.now(),
                )
                await mindmap_text.save()

            logger.info(f"Created article text sections for article {article_id}")

            # Store mindmap image if provided
            mindmap_image_b64 = content.get("mindmap_image")
            if mindmap_image_b64:
                # Store as data URL for now (can be uploaded to S3 later)
                image_url = f"data:image/png;base64,{mindmap_image_b64}"
                mindmap_image = StagingArticleImageTable(
                    staging_article_id=article_id,
                    image_url=image_url,
                    alt_text="Buying Guide Mindmap",
                    image_type="mindmap",
                    sequence_order=0,
                    created_at=datetime.now(),
                )
                await mindmap_image.save()
                logger.info(f"Stored mindmap image for article {article_id}")

        # Insert products
        first_product_id = None
        for i, product in enumerate(products):
            # Build description from available info
            description = (
                product.get("best_for")
                or product.get("pick_label")
                or product.get("target_persona")
                or "General purpose"
            )

            staging_product = StagingProductTable(
                staging_article_id=article_id,
                name=product.get("name", "Unknown Product"),
                brand=product.get("brand") or "",
                category=str(l3_category_id),
                price=product.get("price_inr") or 0,  # Default to 0 if None
                description=description,  # Never None
                image_url=product.get("image_urls", [""])[0]
                if product.get("image_urls")
                else "",
                specs=product.get("specs", {}),
                affiliate_links=product.get("affiliate_links", {}),
                created_at=datetime.now(),
            )
            await staging_product.save()

            # Get product ID
            saved_product = (
                await StagingProductTable.select(StagingProductTable.staging_product_id)
                .where(StagingProductTable.name == product.get("name"))
                .where(StagingProductTable.staging_article_id == article_id)
                .first()
            )

            if saved_product and i == 0:
                first_product_id = saved_product["staging_product_id"]

            logger.info(f"Created product: {product.get('name')}")

        # Update article with top pick
        if first_product_id:
            await StagingArticleTable.update(
                {StagingArticleTable.top_pick_staging_id: first_product_id}
            ).where(StagingArticleTable.staging_article_id == article_id)

        return article_id

    except Exception as e:
        logger.error(f"Failed to insert article: {e}")
        import traceback

        traceback.print_exc()
        return None


async def process_message(message: str) -> bool:
    """
    Process a single message from the queue.

    Args:
        message: JSON message from Redis

    Returns:
        True if processed successfully
    """
    try:
        data = json.loads(message)
        action = data.get("action")

        if action == "submit":
            article_id = await insert_article_to_staging(data)
            if article_id:
                logger.info(
                    f"Successfully processed submission -> Staging ID: {article_id}"
                )
                return True
            else:
                logger.error("Failed to insert article into staging")
                return False
        else:
            logger.warning(f"Unknown action: {action}")
            return False

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in message: {e}")
        return False
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        return False


async def run_consumer():
    """
    Main consumer loop.

    Continuously polls Redis queue and processes messages.
    """
    client = get_redis_client()

    logger.info(f"Starting queue consumer for: {SUBMIT_QUEUE}")
    logger.info(f"Redis: {REDIS_HOST}:{REDIS_PORT}")

    # Check connection
    try:
        client.ping()
        logger.info("Redis connection OK")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")
        return

    while True:
        try:
            # Blocking pop with 5 second timeout
            result = client.blpop(SUBMIT_QUEUE, timeout=5)

            if result:
                queue_name, message = result
                logger.info(f"Received message from {queue_name}")

                success = await process_message(message)

                if not success:
                    # Optionally push failed messages to a dead letter queue
                    client.rpush(f"{SUBMIT_QUEUE}:failed", message)
                    logger.warning("Message moved to failed queue")

        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
            break
        except Exception as e:
            logger.error(f"Consumer error: {e}")
            await asyncio.sleep(1)  # Wait before retrying

    client.close()
    logger.info("Consumer shutdown complete")


if __name__ == "__main__":
    print("=" * 60)
    print(" ProvenPick Staging Queue Consumer")
    print("=" * 60)
    print(f" Queue: {SUBMIT_QUEUE}")
    print(f" Redis: {REDIS_HOST}:{REDIS_PORT}")
    print("=" * 60)
    print()

    asyncio.run(run_consumer())
