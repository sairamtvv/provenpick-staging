# ProvenPick Staging System - Agent Context & Changelog

**Last Updated:** January 29, 2026
**Current State:** Fully Functional / Auth Removed / Production Migration Enabled

## 1. System Overview
The staging system allows human review of AI-generated articles before they go to production.
- **Frontend:** Reflex (React-based) running on port `3000`
- **Backend:** FastAPI running on port `8080`
- **Database:** PostgreSQL (Schema: `staging` for pending, `public` for production)
- **Queue:** Redis (for rejected articles)

## 2. Recent Major Changes

### A. Authentication Removed
- **Change:** Removed all Bearer token requirements and login pages.
- **Reason:** Simplified access for testing and internal usage.
- **Impact:** All API endpoints are open. Dashboard is directly accessible at `/`.

### B. Production Migration (Approval Workflow)
- **File:** `backend/services/approval.py` -> `migrate_to_production`
- **Logic:**
    1.  When an article is APPROVED:
    2.  It is inserted into the **Production Database** (`public` schema).
    3.  It maps all IDs (Article, Products, Images, Texts) from Staging -> Production.
    4.  It defaults category to "Electronics" (ID 4) if lookup fails.
    5.  It archives the staging data in `staging.archive`.
    6.  It deletes the data from `staging.articles`.

### C. Rejection Queue
- **File:** `backend/services/approval.py` -> `archive_staging_data`
- **Logic:**
    1.  When an article is REJECTED:
    2.  The full article data + reviewer comments are pushed to a **Redis List**.
    3.  **Queue Name:** `rejected_articles_queue`
    4.  **Format:** JSON string
    5.  **Failover:** If Redis is down, it logs a warning but proceeds with archival (does not break UI).

### D. UI Overhaul
- **File:** `frontend/pages/review.py`
- **Change:** Rebuilt to match the main ProvenPick application design.
- **Features:**
    - Hook & Mindmap images
    - Product Pick boxes (Top Pick, Runner Up, Budget)
    - Affiliate buttons (Amazon/Best Buy)
    - Methodology section

## 3. Key Files & Locations

| Component | File Path | Description |
|-----------|-----------|-------------|
| **Approval Logic** | `backend/services/approval.py` | Core logic for migration & rejection queue |
| **Review Page** | `frontend/pages/review.py` | Main UI for reviewing articles |
| **DB Tables** | `backend/db/tables.py` | Piccolo ORM definitions for Staging |
| **API Endpoints** | `backend/api/articles.py` | FastAPI routes for article management |
| **Test Data** | `scripts/populate_test_data.py` | Script to generate dummy articles |

## 4. How to Verify

### Check Production Migration
After approving an article (ID `X`), run:
```sql
SELECT * FROM public.article_table ORDER BY article_table_id DESC LIMIT 1;
```
You should see the new article.

### Check Rejection Queue
After rejecting an article, check Redis:
```bash
redis-cli lrange rejected_articles_queue 0 -1
```

## 5. Development Notes for Future Agents
- **Redis Dependency:** The system expects Redis at `localhost:6379`. If missing, it degrades gracefully.
- **Database:** Uses `asyncpg` for migration queries (raw SQL) to handle complex insertions that Piccolo ORM found difficult.
- **State Management:** Reflex state variables must be handled carefully (avoid variable shadowing like `article_id` vs route params).
