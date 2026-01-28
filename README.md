# ProvenPick Staging System

Content staging and moderation system for ProvenPick. This system provides a human-in-the-loop approval workflow for AI-generated product review articles before they go live.

## Overview

This is a **Content Moderation System** (also known as an Editorial Workflow System) that allows human reviewers to:
- Review AI-generated articles in a staging environment
- Approve articles to move them to production
- Reject articles with comments for AI reprocessing
- Track archived decisions with configurable retention

## Architecture

- **Backend**: FastAPI with Piccolo ORM (PostgreSQL)
- **Frontend**: Reflex (Python-based reactive UI)
- **Database**: PostgreSQL with separate `staging` and `public` schemas
- **Authentication**: Simple token-based auth

## Project Structure

```
provenpick-staging/
├── backend/              # FastAPI application
│   ├── api/             # API endpoints
│   │   ├── articles.py  # Article review endpoints
│   │   ├── pipeline.py  # AI pipeline endpoints
│   │   └── archive.py   # Archive endpoints
│   ├── db/              # Database layer
│   │   ├── tables.py    # Piccolo tables (staging schema)
│   │   └── connection.py
│   ├── services/        # Business logic
│   │   ├── approval.py  # Approval workflow
│   │   └── rejection.py # Rejection workflow
│   ├── auth.py          # Authentication
│   └── main.py          # FastAPI app entry
│
├── frontend/            # Reflex UI
│   ├── pages/          # UI pages
│   │   ├── login.py    # Login page
│   │   ├── dashboard.py # Article list
│   │   ├── review.py   # Article review page
│   │   └── archive_page.py # Archive view
│   ├── state.py        # Global state
│   └── app.py          # Reflex app setup
│
├── shared/              # Shared models
│   └── models.py       # Pydantic models
│
├── migrations/          # Database migrations
├── scripts/            # Utility scripts
├── .env.example        # Environment template
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- `uv` package manager (optional but recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sairamtvv/provenpick-staging.git
   cd provenpick-staging
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   # Using uv
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   
   # Or using pip
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials and token
   ```

4. **Create database schemas**
   ```sql
   -- Connect to your PostgreSQL database
   CREATE SCHEMA IF NOT EXISTS staging;
   ```

5. **Run database migrations**
   ```bash
   piccolo migrations forwards all
   ```

## Running the Application

### Backend (FastAPI)

```bash
# Development mode with auto-reload
python backend/main.py

# Or using uvicorn directly
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

API will be available at: `http://localhost:8000`
API docs (Swagger): `http://localhost:8000/docs`

### Frontend (Reflex)

```bash
# In a separate terminal
reflex run

# Or run frontend only
reflex run --frontend-only
```

Frontend will be available at: `http://localhost:3000`

## Usage

### For Reviewers

1. **Login** at `/login` with your admin token
2. **View pending articles** on the dashboard (`/`)
3. **Review an article** by clicking "Review"
4. **Preview** the article as it will appear on the main site
5. **Approve** or **Reject** with comments

### For AI Pipeline (Future Integration)

The system exposes these endpoints for the AI pipeline:

- `POST /api/pipeline/submit` - Submit new article to staging
- `GET /api/pipeline/rejections` - Poll for rejected items
- `POST /api/pipeline/rejections/{id}/ack` - Mark rejection as processed

## API Endpoints

### Article Review
- `GET /api/articles/` - List pending articles
- `GET /api/articles/{id}` - Get full article details
- `POST /api/articles/{id}/approve` - Approve article
- `POST /api/articles/{id}/reject` - Reject article with comments

### Archive
- `GET /api/archive/` - List archived items
- `GET /api/archive/stats` - Get statistics
- `DELETE /api/archive/cleanup` - Clean up expired archives

### Health
- `GET /` - Basic health check
- `GET /health` - Detailed health status

## Database Schema

All staging tables live in the `staging` schema:

- `staging_article` - Articles awaiting review
- `staging_product` - Products linked to staging articles
- `staging_article_image` - Article images
- `staging_article_text` - Article text content
- `staging_product_image` - Product images
- `staging_product_text` - Product text content
- `rejection_queue` - Rejected items for AI reprocessing
- `archive` - Historical record of all decisions

## Workflow

### Approval Flow

1. Human reviews article in staging
2. Clicks "Approve"
3. System:
   - Copies products to `public.product_table`
   - Copies article to `public.article_table`
   - Archives the staging data
   - Deletes from staging tables

### Rejection Flow

1. Human reviews article
2. Enters comments explaining issues
3. Clicks "Reject"
4. System:
   - Adds to `rejection_queue` with comments
   - Archives the staging data
   - Deletes from staging tables
5. AI pipeline polls `/api/pipeline/rejections` and reprocesses

## Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/provenpick

# Authentication
STAGING_ADMIN_TOKEN=your-secret-token-here

# Archive retention (days)
ARCHIVE_RETENTION_DAYS=90

# API settings
API_HOST=0.0.0.0
API_PORT=8000
```

## Development

### Running Tests

```bash
pytest
```

### Code Style

```bash
# Format code
ruff format .

# Lint
ruff check .
```

## Roadmap

- [ ] Implement actual migration to production database
- [ ] Add product deduplication logic
- [ ] Support batch operations (approve/reject multiple)
- [ ] Add concurrent review locking
- [ ] Implement monitoring and metrics
- [ ] Add email notifications for reviewers
- [ ] Support partial approvals (approve article but reject a product)

## License

[Add your license here]

## Support

For issues and questions, please open an issue on GitHub.

## Related Projects

- [ProvenPick Main](https://github.com/sairamtvv/provenpick) - The main ProvenPick application
