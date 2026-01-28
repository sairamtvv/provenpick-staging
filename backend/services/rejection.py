"""
Rejection workflow service.
Handles the process of rejecting staging articles and queuing them for AI reprocessing.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from backend.db.tables import (
    StagingArticleTable,
    RejectionQueueTable,
    ArchiveTable,
)
from backend.services.approval import (
    fetch_full_staging_article,
    delete_staging_data,
    archive_staging_data,
)


async def add_to_rejection_queue(
    staging_article_id: int, full_data: Dict[str, Any], comments: str
) -> int:
    """
    Add rejected article to queue for AI pipeline.

    Args:
        staging_article_id: ID of the staging article
        full_data: Complete staging data
        comments: Reviewer's comments

    Returns:
        Rejection queue ID
    """
    result = await RejectionQueueTable.insert(
        RejectionQueueTable(
            staging_article_id=staging_article_id,
            article_data=full_data,
            reviewer_comments=comments,
            rejected_at=datetime.now(),
            processed_by_pipeline=False,
        )
    ).run()

    return result[0]["rejection_id"]


async def reject_article(
    staging_article_id: int, reviewer_token: str, comments: str
) -> Dict[str, Any]:
    """
    Main rejection workflow.

    Args:
        staging_article_id: ID of the staging article to reject
        reviewer_token: Token of the reviewer
        comments: Reviewer's feedback/comments

    Returns:
        Result dictionary with success status and details
    """
    if not comments or not comments.strip():
        return {
            "success": False,
            "error": "Comments are required when rejecting an article",
        }

    try:
        # 1. Fetch complete staging data
        full_data = await fetch_full_staging_article(staging_article_id)
        if not full_data:
            return {"success": False, "error": "Article not found"}

        # Check if already processed
        article = full_data["article"]
        if article["status"] != "pending":
            return {"success": False, "error": f"Article already {article['status']}"}

        # 2. Add to rejection queue
        rejection_id = await add_to_rejection_queue(
            staging_article_id=staging_article_id,
            full_data=full_data,
            comments=comments,
        )

        # 3. Archive the staging data
        archive_id = await archive_staging_data(
            staging_article_id=staging_article_id,
            full_data=full_data,
            action="rejected",
            comments=comments,
        )

        # 4. Delete from staging
        product_ids = list(full_data["products"].keys())
        await delete_staging_data(staging_article_id, product_ids)

        return {
            "success": True,
            "rejection_id": rejection_id,
            "archive_id": archive_id,
            "message": "Article rejected and queued for reprocessing",
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


async def get_pending_rejections() -> List[Dict[str, Any]]:
    """
    Get all pending items in rejection queue (for AI pipeline to poll).

    Returns:
        List of rejection queue items
    """
    return (
        await RejectionQueueTable.select()
        .where(RejectionQueueTable.processed_by_pipeline == False)
        .order_by(RejectionQueueTable.rejected_at)
        .run()
    )


async def mark_rejection_processed(rejection_id: int) -> bool:
    """
    Mark a rejection as processed by AI pipeline.

    Args:
        rejection_id: ID of the rejection queue item

    Returns:
        True if successful
    """
    await (
        RejectionQueueTable.update(
            {
                RejectionQueueTable.processed_by_pipeline: True,
                RejectionQueueTable.processed_at: datetime.now(),
            }
        )
        .where(RejectionQueueTable.rejection_id == rejection_id)
        .run()
    )

    return True
