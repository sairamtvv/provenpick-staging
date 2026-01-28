"""
AI Pipeline API endpoints.
For the AI pipeline to submit articles and poll for rejections.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from backend.auth import verify_token
from backend.db.tables import (
    StagingArticleTable,
    StagingProductTable,
    StagingArticleImageTable,
    StagingArticleTextTable,
    StagingProductImageTable,
    StagingProductTextTable,
)
from backend.services.rejection import get_pending_rejections, mark_rejection_processed
from datetime import datetime

router = APIRouter(prefix="/api/pipeline", tags=["Pipeline"])


@router.post("/submit")
async def submit_article(data: Dict[str, Any], token: str = Depends(verify_token)):
    """
    Submit a new article from AI pipeline to staging.

    Expected data structure:
    {
        "article": {...},
        "products": [{...}, ...],
        "article_images": [...],
        "article_texts": [...],
        "product_images": {product_index: [...]},
        "product_texts": {product_index: [...]}
    }
    """
    try:
        # Insert products first
        product_id_mapping = {}
        for idx, product in enumerate(data.get("products", [])):
            result = await StagingProductTable.insert(
                StagingProductTable(
                    name=product["name"],
                    brand=product["brand"],
                    category=product["category"],
                    price=product["price"],
                    description=product["description"],
                    image_url=product["image_url"],
                    specs=product.get("specs", {}),
                    affiliate_links=product.get("affiliate_links", {}),
                    created_at=datetime.now(),
                )
            ).run()
            product_id_mapping[idx] = result[0]["staging_product_id"]

            # Insert product images
            for img in data.get("product_images", {}).get(str(idx), []):
                await StagingProductImageTable.insert(
                    StagingProductImageTable(
                        staging_product_id=product_id_mapping[idx],
                        image_url=img["url"],
                        alt_text=img.get("alt_text"),
                        sequence_order=img.get("sequence", 0),
                        created_at=datetime.now(),
                    )
                ).run()

            # Insert product texts
            for txt in data.get("product_texts", {}).get(str(idx), []):
                await StagingProductTextTable.insert(
                    StagingProductTextTable(
                        staging_product_id=product_id_mapping[idx],
                        content=txt["content"],
                        heading=txt.get("heading"),
                        sequence_order=txt.get("sequence", 0),
                        created_at=datetime.now(),
                    )
                ).run()

        # Insert article
        article_data = data["article"]
        article_result = await StagingArticleTable.insert(
            StagingArticleTable(
                title=article_data["title"],
                category=article_data["category"],
                author_name=article_data.get("author_name"),
                top_pick_staging_id=product_id_mapping[article_data["top_pick_index"]],
                runner_up_staging_id=product_id_mapping.get(
                    article_data.get("runner_up_index")
                ),
                budget_pick_staging_id=product_id_mapping.get(
                    article_data.get("budget_pick_index")
                ),
                status="pending",
                submitted_at=datetime.now(),
                created_at=datetime.now(),
            )
        ).run()

        article_id = article_result[0]["staging_article_id"]

        # Insert article images
        for img in data.get("article_images", []):
            await StagingArticleImageTable.insert(
                StagingArticleImageTable(
                    staging_article_id=article_id,
                    image_url=img["url"],
                    alt_text=img.get("alt_text"),
                    image_type=img["type"],
                    sequence_order=img.get("sequence", 0),
                    created_at=datetime.now(),
                )
            ).run()

        # Insert article texts
        for txt in data.get("article_texts", []):
            await StagingArticleTextTable.insert(
                StagingArticleTextTable(
                    staging_article_id=article_id,
                    content=txt["content"],
                    section_type=txt["type"],
                    sequence_order=txt.get("sequence", 0),
                    created_at=datetime.now(),
                )
            ).run()

        return {
            "success": True,
            "staging_article_id": article_id,
            "message": "Article submitted to staging successfully",
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/rejections")
async def get_rejections(token: str = Depends(verify_token)):
    """
    Get pending rejections for AI pipeline to process.
    """
    rejections = await get_pending_rejections()
    return rejections


@router.post("/rejections/{rejection_id}/ack")
async def acknowledge_rejection(rejection_id: int, token: str = Depends(verify_token)):
    """
    Mark a rejection as processed by AI pipeline.
    """
    success = await mark_rejection_processed(rejection_id)

    if not success:
        raise HTTPException(status_code=404, detail="Rejection not found")

    return {"success": True, "message": "Rejection marked as processed"}
