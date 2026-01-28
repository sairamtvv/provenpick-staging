"""
Piccolo database tables for staging system.
All tables live in the 'staging' schema.
"""

from piccolo.table import Table
from piccolo.columns import (
    Serial,
    Varchar,
    Text,
    Float,
    JSONB,
    Timestamp,
    Integer,
    Boolean,
)


class StagingProductTable(Table, schema="staging"):
    """Products in staging environment"""

    staging_product_id = Serial(primary_key=True)

    # Product information (same as main ProductTable)
    name = Varchar(length=255)
    brand = Varchar(length=100)
    category = Varchar(length=100)  # Category name, not FK
    price = Float()
    description = Text()
    image_url = Text()
    specs = JSONB(default={})
    affiliate_links = JSONB(default={})

    # Link to staging article (optional, for tracking)
    staging_article_id = Integer(null=True)

    created_at = Timestamp()

    def __str__(self):
        return self.name or "Staging Product"


class StagingArticleTable(Table, schema="staging"):
    """Articles in staging awaiting review"""

    staging_article_id = Serial(primary_key=True)

    # Article information (same as main ArticleTable)
    title = Varchar(length=255)
    category = Varchar(length=100)
    author_name = Varchar(length=100, null=True)

    # Product references (staging IDs, not main DB IDs)
    top_pick_staging_id = Integer()
    runner_up_staging_id = Integer(null=True)
    budget_pick_staging_id = Integer(null=True)

    # Staging metadata
    status = Varchar(length=20, default="pending")  # 'pending', 'approved', 'rejected'
    reviewer_comments = Text(null=True)
    submitted_at = Timestamp()
    reviewed_at = Timestamp(null=True)
    reviewer_token = Varchar(length=100, null=True)

    created_at = Timestamp()
    updated_at = Timestamp(null=True)

    def __str__(self):
        return self.title or "Staging Article"


class StagingArticleImageTable(Table, schema="staging"):
    """Images for staging articles"""

    staging_article_image_id = Serial(primary_key=True)
    staging_article_id = Integer()  # References StagingArticleTable
    image_url = Text()
    alt_text = Varchar(length=255, null=True)
    image_type = Varchar(length=50)  # 'hook', 'mindmap', 'general'
    sequence_order = Integer(default=0)
    created_at = Timestamp()

    def __str__(self):
        return f"{self.image_type} - {self.alt_text or 'Image'}"


class StagingArticleTextTable(Table, schema="staging"):
    """Text content for staging articles"""

    staging_article_text_id = Serial(primary_key=True)
    staging_article_id = Integer()  # References StagingArticleTable
    content = Text()
    section_type = Varchar(length=50)  # 'mindmap_summary', 'methodology', 'general'
    sequence_order = Integer(default=0)
    created_at = Timestamp()

    def __str__(self):
        summary = (self.content[:20] + "...") if self.content else "Text"
        return f"{self.section_type} - {summary}"


class StagingProductImageTable(Table, schema="staging"):
    """Images for staging products"""

    staging_product_image_id = Serial(primary_key=True)
    staging_product_id = Integer()  # References StagingProductTable
    image_url = Text()
    alt_text = Varchar(length=255, null=True)
    sequence_order = Integer(default=0)
    created_at = Timestamp()

    def __str__(self):
        return f"Product Image {self.sequence_order}"


class StagingProductTextTable(Table, schema="staging"):
    """Text content for staging products"""

    staging_product_text_id = Serial(primary_key=True)
    staging_product_id = Integer()  # References StagingProductTable
    content = Text()
    heading = Varchar(length=255, null=True)
    sequence_order = Integer(default=0)
    created_at = Timestamp()

    def __str__(self):
        return self.heading or f"Product Text {self.sequence_order}"


class RejectionQueueTable(Table, schema="staging"):
    """Queue of rejected articles for AI pipeline to reprocess"""

    rejection_id = Serial(primary_key=True)
    staging_article_id = Integer()
    article_data = JSONB()  # Full article + products + all child data
    reviewer_comments = Text()
    rejected_at = Timestamp()
    processed_by_pipeline = Boolean(default=False)
    processed_at = Timestamp(null=True)

    def __str__(self):
        status = "Processed" if self.processed_by_pipeline else "Pending"
        return f"Rejection {self.rejection_id} - {status}"


class ArchiveTable(Table, schema="staging"):
    """Archive of approved and rejected articles"""

    archive_id = Serial(primary_key=True)
    staging_article_id = Integer()
    action = Varchar(length=20)  # 'approved' or 'rejected'
    article_data = JSONB()  # Complete snapshot of article + products + child data
    reviewer_comments = Text(null=True)
    archived_at = Timestamp()
    retention_until = Timestamp()  # Calculated based on ARCHIVE_RETENTION_DAYS

    def __str__(self):
        return f"Archive {self.archive_id} - {self.action}"
