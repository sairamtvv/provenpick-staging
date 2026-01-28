"""
Archive API endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter
from backend.db.tables import ArchiveTable

router = APIRouter(prefix="/api/archive", tags=["Archive"])


@router.get("/")
async def list_archives(action: Optional[str] = None):
    """
    Get list of archived articles.

    Args:
        action: Filter by 'approved' or 'rejected' (optional)
    """
    query = ArchiveTable.select()

    if action:
        query = query.where(ArchiveTable.action == action)

    archives = await query.order_by(ArchiveTable.archived_at, ascending=False).run()

    return archives
