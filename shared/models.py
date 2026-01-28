"""
Shared Pydantic models for staging system.
These models are used for data validation and transfer between components.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ===== Base Models =====
class BaseEntity(BaseModel):
    id: int
    created_at: datetime = Field(default_factory=datetime.now)


# ===== Product Models =====
class ProductImage(BaseEntity):
    url: str
    alt_text: Optional[str] = None
    sequence: int


class ProductText(BaseEntity):
    content: str
    heading: Optional[str] = None
    sequence: int


class Product(BaseEntity):
    name: str
    brand: str
    category: str
    price: float
    description: str
    image_url: str
    specs: Dict[str, Any] = {}
    affiliate_links: Dict[str, str] = {}
    images: List[ProductImage] = []
    texts: List[ProductText] = []
    updated_at: Optional[datetime] = None


# ===== Article Models =====
class ArticleImage(BaseEntity):
    image_url: str
    alt_text: Optional[str] = None
    image_type: str  # 'hook', 'mindmap', 'general'
    sequence: int


class ArticleText(BaseEntity):
    content: str
    section_type: str  # 'mindmap_summary', 'general'
    sequence: int


# ===== Staging Models =====
class StagingProduct(Product):
    """Product in staging environment"""

    staging_article_id: Optional[int] = None


class StagingArticle(BaseEntity):
    """Article in staging awaiting review"""

    title: str
    category: str
    author_name: Optional[str] = None

    # Product references (staging IDs)
    top_pick_staging_id: int
    runner_up_staging_id: Optional[int] = None
    budget_pick_staging_id: Optional[int] = None

    # Hydrated products (populated when fetched)
    top_pick: Optional[StagingProduct] = None
    runner_up: Optional[StagingProduct] = None
    budget_pick: Optional[StagingProduct] = None

    # Article content
    hook_image: Optional[ArticleImage] = None
    mindmap_image: Optional[ArticleImage] = None
    mindmap_summary: Optional[ArticleText] = None
    methodology_texts: List[ArticleText] = []
    images: List[ArticleImage] = []
    texts: List[ArticleText] = []

    # Staging metadata
    status: str = "pending"  # 'pending', 'approved', 'rejected'
    reviewer_comments: Optional[str] = None
    submitted_at: datetime = Field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    reviewer_token: Optional[str] = None

    updated_at: Optional[datetime] = None


# ===== API Request/Response Models =====
class ArticleListItem(BaseModel):
    """Lightweight model for article list view"""

    id: int
    title: str
    category: str
    status: str
    submitted_at: datetime
    products_count: int
    top_pick_name: str


class ApprovalRequest(BaseModel):
    """Request to approve an article"""

    article_id: int
    reviewer_token: str


class RejectionRequest(BaseModel):
    """Request to reject an article"""

    comments: str


class ArchiveItem(BaseModel):
    """Archived article record"""

    archive_id: int
    staging_article_id: int
    action: str  # 'approved' or 'rejected'
    article_data: Dict[str, Any]
    reviewer_comments: Optional[str]
    archived_at: datetime
    retention_until: datetime


class RejectionQueueItem(BaseModel):
    """Item in rejection queue for AI pipeline"""

    rejection_id: int
    staging_article_id: int
    article_data: Dict[str, Any]
    reviewer_comments: str
    rejected_at: datetime
    processed_by_pipeline: bool
    processed_at: Optional[datetime]


# ===== Stats Models =====
class SystemStats(BaseModel):
    """System statistics for monitoring"""

    pending_articles: int
    approved_today: int
    rejected_today: int
    avg_review_time_hours: Optional[float]
    oldest_pending_date: Optional[datetime]
