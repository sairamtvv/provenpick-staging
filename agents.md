# ProvenPick System - Complete Agent Context & Architecture

**Last Updated:** February 2, 2026  
**Current State:** Production Ready - Full E2E Workflow Operational

---

## 1. System Overview

ProvenPick is a content generation system that transforms YouTube product reviews into professional buying guide articles. The system consists of **3 repositories** working together:

### Repository Architecture

| Repository | Path | Purpose | Tech Stack |
|------------|------|---------|------------|
| **provenpick-workflow** | `/provenpick-workflow` | Content generation pipeline | LangGraph + Gradio + LightRAG |
| **provenpick-staging** | `/provenpick-staging` | Review & approval system | FastAPI + Reflex |
| **provenpick** | `/provenpick` | Production website | Reflex |

---

## 2. Content Generation Pipeline (provenpick-workflow)

### 2.1 Architecture

The workflow uses **LangGraph** to orchestrate a multi-agent pipeline that processes YouTube videos and generates articles.

**Key Components:**
- **LangGraph State Machine**: Orchestrates 7 specialized agents
- **LightRAG + Neo4j**: Knowledge graph for contextual retrieval
- **Local Embeddings**: sentence-transformers/all-MiniLM-L6-v2
- **Gradio UI**: Interactive web interface on port 7860

### 2.2 Agent Workflow

```
Video URL → Transcript → Knowledge Graph → Content Generation → Staging Submission
```

**Agents (in execution order):**

1. **transcript_agent** (`agents/transcript_agent.py`)
   - Downloads YouTube transcript
   - Stores raw text in state
   - Fallback: Uses YouTube Data API if transcript unavailable

2. **lightrag_agent** (`agents/lightrag_agent.py`)
   - Inserts transcript into LightRAG knowledge graph
   - Builds entity-relationship graph in Neo4j
   - Enables semantic search across video content

3. **research_agent** (`agents/research_agent.py`)
   - Queries LightRAG with "naive" mode for broad context
   - Extracts product information, features, pros/cons
   - Output: Structured research notes

4. **mindmap_agent** (`agents/mindmap_agent.py`)
   - Creates visual decision tree (Graphviz DOT format)
   - Generates PNG mindmap image
   - Produces mindmap summary text
   - Storage: `output/mindmap.png`

5. **article_agent** (`agents/article_agent.py`)
   - Generates full buying guide article
   - Uses graph context from Neo4j
   - Output: HTML with tables, headings, product comparisons
   - Sections: Introduction, Quick Picks, Detailed Reviews

6. **bullet_points_agent** (`agents/bullet_points_agent.py`)
   - Creates concise bullet-point summary
   - Highlights key takeaways
   - Used for quick scanning

7. **staging_submission_agent** (`agents/staging_submission_agent.py`)
   - Submits complete article to staging API
   - Sends: article text, products, images, metadata
   - Endpoint: `http://localhost:8080/api/articles`

### 2.3 LightRAG Integration

**File:** `src/services/lightrag_service.py`

**Key Features:**
- Local embeddings (no API calls)
- Neo4j storage backend (bolt://localhost:7687)
- Custom `LocalEmbedding` class implementing `EmbeddingFunc`
- Async initialization: `await rag.initialize_storages()`

**Configuration:** `config.toml`
```toml
[lightrag]
working_dir = "./lightrag_data"
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
llm_model = "gpt-4o-mini"

[neo4j]
uri = "bolt://localhost:7687"
username = "neo4j"
password = "provenpick"
database = "provenpick"
```

**Critical Fix (Feb 2):**
- Added `EmbeddingFunc` parameter to LightRAG constructor
- Added `await rag.initialize_storages()` before first use
- Ensures graph context is populated (not fallback empty response)

### 2.4 LangGraph State

**File:** `src/workflow/state.py`

```python
class WorkflowState(TypedDict):
    video_url: str
    transcript: str
    research_notes: str
    mindmap_dot: str
    mindmap_image_path: str
    mindmap_summary: str
    full_article: str
    bullet_points: str
    staging_response: dict
    category: str
```

### 2.5 Running the Workflow

**Start Services:**
```bash
# Neo4j (required for LightRAG)
docker start neo4j

# Redis (required for staging queue)
redis-server

# Start workflow Gradio UI
cd /provenpick-workflow
uv run python -m src.main
```

**Access:** http://localhost:7860

**Test Video:** https://www.youtube.com/watch?v=0y_kPPKGRWA

---

## 3. Staging System (provenpick-staging)

### 3.1 Purpose

Human review and approval of AI-generated articles before production deployment.

### 3.2 Architecture

**Frontend:**
- Reflex framework (React-based)
- Port: **3001** (config) → **5173** (dev server)
- Pages: Dashboard (`/`) + Review (`/review/[article_id]`)

**Backend:**
- FastAPI
- Port: **8080**
- Database: PostgreSQL (schema: `staging`)

### 3.3 Database Schema

**Tables:**
- `staging.staging_article` - Article metadata
- `staging.staging_product` - Product picks
- `staging.staging_article_image` - Hook/mindmap images
- `staging.staging_article_text` - Article sections
- `staging.archive_*` - Archived approved/rejected articles

**Key Fields:**
```sql
staging_article:
  - staging_id (PK)
  - title, category, status
  - top_pick_staging_id, runner_up_staging_id, budget_pick_staging_id

staging_article_text:
  - section_type: 'full_article' | 'bullet_points' | 'mindmap_summary'
  - content: TEXT (HTML for full_article)

staging_article_image:
  - image_type: 'hook' | 'mindmap'
  - image_url: VARCHAR
```

### 3.4 Review Page

**File:** `frontend/pages/review.py`

**Key Features:**
- Displays full article with all sections
- Hook image upload capability
- Mindmap visualization
- Product pick boxes (Top Pick, Runner Up, Budget)
- Affiliate links (Amazon, Best Buy)
- Approve/Reject buttons

**Critical Fix (Feb 2):**

**Problem:** Reflex doesn't allow passing reactive `Var` objects to `rx.html()` for dynamic HTML rendering.

**Solution:** Use iframe with base64-encoded data URL

**Implementation:**
```python
@rx.var
def get_full_article_html_dataurl(self) -> str:
    """Return full article HTML as data URL for iframe"""
    if self.article and self.article.full_article_html:
        import base64
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: sans-serif; line-height: 1.6; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; }}
    </style>
</head>
<body>
{self.article.full_article_html}
</body>
</html>
        """
        encoded = base64.b64encode(html_content.encode('utf-8')).decode('utf-8')
        return f"data:text/html;base64,{encoded}"
    return ""
```

**UI Component (lines 670-689):**
```python
rx.el.iframe(
    src=ReviewState.get_full_article_html_dataurl,
    style={
        "width": "100%",
        "minHeight": "800px",
        "border": "none",
    },
)
```

### 3.5 Approval Workflow

**File:** `backend/services/approval.py`

**On APPROVE:**
1. Migrate article to production database (`public` schema)
2. Map all staging IDs → production IDs
3. Archive staging data to `staging.archive_*`
4. Delete from `staging.staging_*`

**On REJECT:**
1. Push article + comments to Redis queue: `rejected_articles_queue`
2. Archive to `staging.archive_*`
3. Delete from `staging.staging_*`
4. Queue consumer can reprocess rejected articles

**Migration Logic:**
```python
async def migrate_to_production(article_id: int):
    # 1. Create production article
    # 2. Migrate products (map staging_id → production_id)
    # 3. Migrate images
    # 4. Migrate text sections
    # 5. Archive staging data
    # 6. Delete staging data
```

### 3.6 Queue Consumer

**File:** `backend/services/queue_consumer.py`

**Purpose:** Process rejected articles from Redis queue

**Run:**
```bash
cd /provenpick-staging
uv run python -m backend.services.queue_consumer
```

**Functionality:**
- Polls `rejected_articles_queue`
- Logs rejection details
- Can be extended to auto-retry or notify workflow system

### 3.7 API Endpoints

**Base URL:** http://localhost:8080

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/articles` | GET | List all pending articles |
| `/api/articles` | POST | Submit new article from workflow |
| `/api/articles/{id}` | GET | Get article with all data |
| `/api/articles/{id}/approve` | POST | Approve article → production |
| `/api/articles/{id}/reject` | POST | Reject article → queue |
| `/api/articles/{id}/hook-image` | POST | Upload hook image |

### 3.8 Starting Staging System

```bash
# Backend
cd /provenpick-staging
.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080 &

# Frontend (Reflex export + dev server)
.venv/bin/python -m reflex export --no-zip
cd .web
npm run dev &

# Queue Consumer
uv run python -m backend.services.queue_consumer &
```

**Access:**
- Dashboard: http://localhost:5173
- Review: http://localhost:5173/review/19
- API Docs: http://localhost:8080/docs

---

## 4. Production Website (provenpick)

### 4.1 Purpose

Public-facing website displaying approved articles.

### 4.2 Architecture

**Framework:** Reflex  
**Ports:** Frontend 3000, Backend 8000  
**Database:** PostgreSQL (`public` schema)

### 4.3 Database Schema

**Tables:**
- `public.article_table` - Published articles
- `public.product_table` - Products
- `public.article_image_table` - Images
- `public.article_text_table` - Article content

**Key Relationships:**
```
article_table
  ├── top_pick_id → product_table
  ├── runner_up_id → product_table
  ├── budget_pick_id → product_table
  ├── article_images (hook, mindmap)
  └── article_texts (full_article, bullet_points)
```

### 4.4 Running Production

```bash
cd /provenpick
source .venv/bin/activate
nohup .venv/bin/python -m reflex run > /tmp/provenpick.log 2>&1 &
```

**Access:** http://localhost:3000

---

## 5. Service Dependencies

### 5.1 Required Services

| Service | Port | Purpose | Start Command |
|---------|------|---------|---------------|
| PostgreSQL | 5432 | Primary database | `sudo systemctl start postgresql` |
| Redis | 6379 | Rejection queue | `redis-server` |
| Neo4j | 7687, 7474 | Knowledge graph | `docker start neo4j` |

### 5.2 Neo4j Setup

**Credentials:**
- Username: `neo4j`
- Password: `provenpick`
- Database: `provenpick`

**Reset Password:**
```bash
docker exec -it neo4j cypher-shell -u neo4j -p neo4j
ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO 'provenpick';
```

**Clear Database:**
```cypher
MATCH (n) DETACH DELETE n;
```

### 5.3 PostgreSQL Schemas

**staging:** Pending articles  
**public:** Production articles

**Verify:**
```sql
\c provenpick
\dt staging.*
\dt public.*
```

---

## 6. End-to-End Test Workflow

### Step 1: Start All Services

```bash
# Infrastructure
sudo systemctl start postgresql
redis-server &
docker start neo4j

# Workflow System
cd /provenpick-workflow
uv run python -m src.main &

# Staging Backend
cd /provenpick-staging
.venv/bin/python -m uvicorn backend.main:app --port 8080 &

# Staging Frontend
cd /provenpick-staging
.venv/bin/python -m reflex export --no-zip
cd .web && npm run dev &

# Production Site
cd /provenpick
nohup .venv/bin/python -m reflex run > /tmp/provenpick.log 2>&1 &

# Queue Consumer
cd /provenpick-staging
uv run python -m backend.services.queue_consumer &
```

### Step 2: Generate Article

1. Open http://localhost:7860
2. Enter YouTube URL: `https://www.youtube.com/watch?v=0y_kPPKGRWA`
3. Enter category: `Electronics` (or any category)
4. Click "Generate Article"
5. Wait ~5 minutes for workflow to complete
6. Check logs for "Article submitted to staging with ID: X"

### Step 3: Review Article

1. Open http://localhost:5173
2. Click on article in dashboard
3. Review all sections:
   - Hook image
   - Mindmap + summary
   - Full article (in iframe)
   - Product picks
   - Methodology
4. Upload hook image (optional)
5. Click "✓ Approve"

### Step 4: Verify Production

1. Open http://localhost:3000
2. Navigate to article category
3. Verify article appears
4. Check all content renders correctly

### Step 5: Verify Database

```sql
-- Check staging is empty
SELECT COUNT(*) FROM staging.staging_article;

-- Check production has article
SELECT * FROM public.article_table ORDER BY article_table_id DESC LIMIT 1;

-- Check archived data
SELECT * FROM staging.archive_article ORDER BY archived_at DESC LIMIT 1;
```

---

## 7. Known Issues & Solutions

### Issue 1: LightRAG Returns Empty Graph Context

**Symptoms:**
- `_get_graph_context()` returns `""`
- Article lacks video-specific details

**Cause:**
- Missing `EmbeddingFunc` parameter in LightRAG constructor
- No `await rag.initialize_storages()` call

**Fix:**
```python
# lightrag_service.py
class LocalEmbedding(EmbeddingFunc):
    # ... implementation

async def _create_rag() -> LightRAG:
    embedding_func = LocalEmbedding(
        embedding_dim=384,
        max_token_size=512,
        func=local_embedding_func,
    )
    
    rag = LightRAG(
        working_dir=str(config.lightrag.working_dir),
        embedding_func=embedding_func,  # CRITICAL
        # ...
    )
    
    await rag.initialize_storages()  # CRITICAL
    return rag
```

### Issue 2: Reflex HTML Rendering Error

**Symptoms:**
- `TypeError: Cannot pass a Var to a built-in function`
- Full article section shows heading but no content

**Cause:**
- `rx.html()` doesn't accept reactive Vars in Reflex

**Solution:**
- Use iframe with base64 data URL (see Section 3.4)

### Issue 3: Staging Frontend on Wrong Port

**Expected:** 3001 (rxconfig.py)  
**Actual:** 5173 (React Router dev server)

**Explanation:**
- Reflex uses React Router which defaults to 5173
- `reflex run` may use different port than config
- Use `npm run dev` in `.web/` directory for consistent 5173

**Access:** http://localhost:5173 (not 3001)

### Issue 4: Neo4j Connection Failed

**Error:** `ServiceUnavailable: Cannot connect to bolt://localhost:7687`

**Fix:**
```bash
docker start neo4j
# Wait 30 seconds for startup
# Verify: docker logs neo4j
```

### Issue 5: Redis Queue Not Processing

**Symptoms:**
- Rejected articles not logged
- Queue consumer silent

**Check:**
```bash
# Verify Redis running
redis-cli ping

# Check queue length
redis-cli llen rejected_articles_queue

# View items
redis-cli lrange rejected_articles_queue 0 -1
```

**Restart Consumer:**
```bash
cd /provenpick-staging
uv run python -m backend.services.queue_consumer
```

---

## 8. Development Workflow

### Adding New Agent to Workflow

1. Create agent file: `src/agents/new_agent.py`
2. Define agent function:
   ```python
   def new_agent_node(state: WorkflowState) -> WorkflowState:
       # Process state
       return {"new_field": result}
   ```
3. Update `WorkflowState` in `src/workflow/state.py`
4. Add node to graph in `src/workflow/graph.py`:
   ```python
   graph.add_node("new_agent", new_agent_node)
   graph.add_edge("previous_agent", "new_agent")
   ```
5. Update `src/workflow/__init__.py` exports

### Adding New Field to Staging

1. Update database table: `backend/db/tables.py`
2. Create migration: `piccolo migrations new`
3. Run migration: `piccolo migrations forwards`
4. Update API endpoint: `backend/api/articles.py`
5. Update Reflex model: `frontend/pages/review.py`
6. Update UI component

### Modifying Production Schema

1. Update production database directly (no ORM)
2. Update migration logic: `backend/services/approval.py`
3. Test with approval workflow
4. Verify in production site

---

## 9. File Reference Guide

### Workflow System

| File | Purpose | Key Functions |
|------|---------|---------------|
| `src/main.py` | Gradio UI entry point | `generate_article_interface()` |
| `src/workflow/graph.py` | LangGraph workflow definition | `create_workflow()` |
| `src/workflow/state.py` | State schema | `WorkflowState` |
| `src/agents/transcript_agent.py` | YouTube transcript download | `transcript_agent_node()` |
| `src/agents/lightrag_agent.py` | Knowledge graph insertion | `lightrag_agent_node()` |
| `src/agents/research_agent.py` | Context extraction | `research_agent_node()` |
| `src/agents/mindmap_agent.py` | Decision tree generation | `mindmap_agent_node()` |
| `src/agents/article_agent.py` | Full article writing | `article_agent_node()` |
| `src/agents/bullet_points_agent.py` | Summary generation | `bullet_points_agent_node()` |
| `src/agents/staging_submission_agent.py` | API submission | `staging_submission_agent_node()` |
| `src/services/lightrag_service.py` | LightRAG integration | `LightRAGService` |
| `config.toml` | Configuration | All settings |

### Staging System

| File | Purpose | Key Components |
|------|---------|----------------|
| `backend/main.py` | FastAPI app | `app`, CORS, routes |
| `backend/api/articles.py` | Article endpoints | GET, POST, approve, reject |
| `backend/services/approval.py` | Approval logic | `migrate_to_production()`, `archive_staging_data()` |
| `backend/services/queue_consumer.py` | Queue processor | `process_queue()` |
| `backend/db/tables.py` | Piccolo ORM models | All staging tables |
| `frontend/app.py` | Reflex app | `app` |
| `frontend/pages/index.py` | Dashboard | `index()` |
| `frontend/pages/review.py` | Review page | `review_page()`, `ReviewState` |
| `frontend/state.py` | Base state | `AppState` |
| `rxconfig.py` | Reflex config | Ports, app name |

### Production Site

| File | Purpose |
|------|---------|
| `provenpick/provenpick.py` | Main Reflex app |
| `provenpick/pages/*.py` | Page components |
| `provenpick/rxconfig.py` | Reflex config |

---

## 10. Testing & Verification

### Test Article Submission

```bash
curl -X POST http://localhost:8080/api/articles \
  -H "Content-Type: application/json" \
  -d @test_article.json
```

### Test Approval Flow

```python
import httpx
response = httpx.post("http://localhost:8080/api/articles/19/approve")
assert response.status_code == 200
```

### Check Neo4j Graph

```cypher
// Count entities
MATCH (n) RETURN labels(n), count(n);

// View relationships
MATCH (n)-[r]->(m) 
RETURN type(r), count(r);

// Sample entities
MATCH (n) RETURN n LIMIT 10;
```

### Monitor Redis Queue

```bash
# Real-time monitoring
redis-cli monitor | grep rejected_articles_queue

# Queue stats
redis-cli
> LLEN rejected_articles_queue
> LRANGE rejected_articles_queue 0 -1
```

---

## 11. Production Deployment Checklist

- [ ] All services start automatically (systemd units)
- [ ] PostgreSQL backups configured
- [ ] Redis persistence enabled (AOF)
- [ ] Neo4j backups configured
- [ ] Environment variables secured (.env files)
- [ ] API rate limiting implemented
- [ ] Error monitoring (Sentry, etc.)
- [ ] Log aggregation (Loki, etc.)
- [ ] SSL/TLS for web interfaces
- [ ] Firewall rules configured
- [ ] Load balancing for production site
- [ ] CDN for static assets
- [ ] Database connection pooling
- [ ] Workflow auto-retry on failure
- [ ] Queue dead-letter handling

---

## 12. Architecture Diagrams

### Data Flow

```
YouTube Video
    ↓
[Transcript Agent] → Raw transcript
    ↓
[LightRAG Agent] → Neo4j Knowledge Graph
    ↓
[Research Agent] → Structured notes (using graph context)
    ↓
[Mindmap Agent] → Decision tree PNG + summary
    ↓
[Article Agent] → Full HTML article (using graph context)
    ↓
[Bullet Points Agent] → Summary
    ↓
[Staging Submission Agent] → POST to staging API
    ↓
[Staging Database] → staging.staging_article
    ↓
[Human Review] → http://localhost:5173/review/[id]
    ↓
    ├─ APPROVE → [Production Migration] → public.article_table
    └─ REJECT → [Redis Queue] → rejected_articles_queue
```

### System Components

```
┌─────────────────────────────────────────────────┐
│           ProvenPick Workflow                    │
│  (LangGraph + Gradio on :7860)                  │
│                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │Transcript│→ │ LightRAG │→ │ Research │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                     ↓                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │ Mindmap  │→ │ Article  │→ │ Bullets  │      │
│  └──────────┘  └──────────┘  └──────────┘      │
│                     ↓                            │
│              [Staging Submit]                    │
└──────────────────┬──────────────────────────────┘
                   │ HTTP POST
                   ↓
┌─────────────────────────────────────────────────┐
│         ProvenPick Staging (:8080, :5173)       │
│                                                  │
│  ┌─────────────────┐  ┌────────────────────┐   │
│  │  FastAPI Backend │  │ Reflex Frontend    │   │
│  │  /api/articles   │  │ Dashboard + Review │   │
│  └────────┬─────────┘  └────────────────────┘   │
│           │                                      │
│           ↓                                      │
│  ┌────────────────┐      ┌─────────────────┐   │
│  │   PostgreSQL   │      │     Redis        │   │
│  │ staging schema │      │ Rejection Queue  │   │
│  └────────────────┘      └─────────────────┘   │
│           │                                      │
│       [Approve]                                  │
└───────────┬──────────────────────────────────────┘
            │ Migrate
            ↓
┌─────────────────────────────────────────────────┐
│      ProvenPick Production (:3000, :8000)       │
│                                                  │
│  ┌─────────────────────────────────────────┐   │
│  │         Reflex Website                   │   │
│  │  Article List → Article Detail           │   │
│  └─────────────────────────────────────────┘   │
│           │                                      │
│           ↓                                      │
│  ┌─────────────────────────────────────────┐   │
│  │         PostgreSQL (public schema)       │   │
│  │  article_table, product_table, etc.      │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### Knowledge Graph (Neo4j)

```
            [Video Transcript]
                   │
                   ↓
           [LightRAG Insert]
                   │
         ┌─────────┴─────────┐
         ↓                   ↓
    [Entities]         [Relationships]
    • Products         • HAS_FEATURE
    • Features         • COMPARED_TO
    • Brands           • RECOMMENDED_FOR
    • Pros/Cons        • PERFORMS_IN
         │                   │
         └─────────┬─────────┘
                   ↓
          [Graph Context Query]
                   │
         ┌─────────┴─────────┐
         ↓                   ↓
   [Research Agent]    [Article Agent]
   (naive mode)        (hybrid mode)
         │                   │
         └─────────┬─────────┘
                   ↓
            [Rich Content]
```

---

## 13. Contact & Support

For questions about this system architecture:
1. Check this agents.md document
2. Review code comments in key files
3. Check logs in `/tmp/*.log`
4. Verify service status: `ps aux | grep -E "reflex|uvicorn|gradio"`

**Key Log Files:**
- Workflow: Console output from `uv run python -m src.main`
- Staging Backend: `uvicorn` console or `/tmp/staging-backend-clean.log`
- Staging Frontend: `/tmp/staging-frontend-final.log`
- Production: `/tmp/provenpick.log`
- Queue Consumer: Console output

**Service Status:**
```bash
# Check all ProvenPick processes
ps aux | grep -E "provenpick|reflex|uvicorn|gradio" | grep -v grep

# Check ports
lsof -i:3000,3001,5173,7860,8000,8001,8080

# Check databases
psql -U sai -d provenpick -c "\dt staging.*"
redis-cli ping
docker exec -it neo4j cypher-shell -u neo4j -p provenpick
```

---

**Last Major Update:** February 2, 2026  
**Changes:**
- Fixed LightRAG empty graph context issue (added EmbeddingFunc + initialize_storages)
- Fixed Reflex HTML rendering (iframe + base64 data URL)
- Documented full E2E workflow
- Added complete service dependency guide
- Verified staging frontend on port 5173
