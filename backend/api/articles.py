"""
Article review API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from backend.auth import verify_token
from backend.db.tables import StagingArticleTable, StagingProductTable
from backend.services.approval import approve_article
from backend.services.rejection import reject_article
from shared.models import (
    ArticleListItem,
    StagingArticle,
    ApprovalRequest,
    RejectionRequest,
)

router = APIRouter(prefix="/api/articles", tags=["Articles"])


@router.get("/", response_model=List[ArticleListItem])
async def list_pending_articles(token: str = Depends(verify_token)):
    """
    Get list of all pending articles.
    """
    articles = (
        await StagingArticleTable.select()
        .where(StagingArticleTable.status == "pending")
        .order_by(StagingArticleTable.submitted_at, ascending=False)
        .run()
    )

    result = []
    for article in articles:
        # Get top pick product name
        top_pick = (
            await StagingProductTable.select(StagingProductTable.name)
            .where(
                StagingProductTable.staging_product_id == article["top_pick_staging_id"]
            )
            .first()
            .run()
        )

        # Count total products
        products_count = 1  # Top pick always exists
        if article["runner_up_staging_id"]:
            products_count += 1
        if article["budget_pick_staging_id"]:
            products_count += 1

        result.append(
            ArticleListItem(
                id=article["staging_article_id"],
                title=article["title"],
                category=article["category"],
                status=article["status"],
                submitted_at=article["submitted_at"],
                products_count=products_count,
                top_pick_name=top_pick["name"] if top_pick else "Unknown",
            )
        )

    return result


@router.get("/{article_id}")
async def get_article_detail(article_id: int, token: str = Depends(verify_token)):
    """
    Get full article details including products, images, and texts.
    """
    from backend.services.approval import fetch_full_staging_article

    full_data = await fetch_full_staging_article(article_id)
    if not full_data:
        raise HTTPException(status_code=404, detail="Article not found")

    return full_data


@router.post("/{article_id}/approve")
async def approve(article_id: int, token: str = Depends(verify_token)):
    """
    Approve an article and move it to production.
    """
    result = await approve_article(article_id, token)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


@router.post("/{article_id}/reject")
async def reject(
    article_id: int, request: RejectionRequest, token: str = Depends(verify_token)
):
    """
    Reject an article with comments.
    """
    result = await reject_article(article_id, token, request.comments)

    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])

    return result
