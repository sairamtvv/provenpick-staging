"""
Archive API endpoints.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from backend.auth import verify_token
from backend.db.tables import ArchiveTable
from datetime import datetime

router = APIRouter(prefix="/api/archive", tags=["Archive"])


@router.get("/")
async def list_archive(token: str = Depends(verify_token), action: str = None):
    """
    Get archived articles.

    Args:
        action: Filter by 'approved' or 'rejected' (optional)
    """
    query = ArchiveTable.select().order_by(ArchiveTable.archived_at, ascending=False)

    if action:
        query = query.where(ArchiveTable.action == action)

    archives = await query.run()
    return archives


@router.delete("/cleanup")
async def cleanup_expired(token: str = Depends(verify_token)):
    """
    Delete archived items that have exceeded retention period.
    """
    deleted = (
        await ArchiveTable.delete()
        .where(ArchiveTable.retention_until < datetime.now())
        .run()
    )

    return {
        "success": True,
        "deleted_count": len(deleted) if deleted else 0,
        "message": f"Cleaned up expired archive items",
    }


@router.get("/stats")
async def get_stats(token: str = Depends(verify_token)):
    """
    Get archive statistics.
    """
    total = await ArchiveTable.count().run()
    approved = await ArchiveTable.count().where(ArchiveTable.action == "approved").run()
    rejected = await ArchiveTable.count().where(ArchiveTable.action == "rejected").run()

    return {
        "total_archived": total,
        "approved_count": approved,
        "rejected_count": rejected,
    }
