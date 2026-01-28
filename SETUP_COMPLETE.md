# Setup Completed! ✅

## What's Been Configured

### 1. Database Setup
- ✅ **Staging schema created** in PostgreSQL database `provenpick`
- ✅ Database credentials configured:
  - Database: `provenpick`
  - User: `provenpick`
  - Password: `provenpick`
  - Host: `localhost`
  - Port: `5432`

### 2. Environment Configuration
- ✅ `.env` file created with all necessary variables
- ✅ Authentication token set: `provenpick-staging-secret-token-2026`
- ✅ Archive retention: 90 days
- ✅ API configured for port 8000
- ✅ Frontend configured for port 3000

### 3. Schema Verification
```sql
Schema  |   Owner   
---------+-----------
staging | provenpick
```

## Next Steps

### 1. Install Dependencies (Required)

Due to TLS certificate issues with `uv`, you have two options:

**Option A: Use main ProvenPick's venv (Quick)**
```bash
cd /home/sai/Desktop/Projects_and_Folders/my_code/provenpick-staging

# Use the main project's Python environment
alias staging-python="/home/sai/Desktop/Projects_and_Folders/my_code/provenpick/.venv/bin/python"

# Install staging-specific packages if needed
/home/sai/Desktop/Projects_and_Folders/my_code/provenpick/.venv/bin/pip install fastapi uvicorn
```

**Option B: Fix UV TLS and install fresh (Recommended for production)**
```bash
# Export environment variable to use system certificates
export UV_NATIVE_TLS=1

# Or reinstall with --native-tls flag
uv pip install -r requirements.txt --python .venv/bin/python --native-tls
```

### 2. Create Database Tables

Once dependencies are installed:

```bash
# Generate migrations
piccolo migrations new backend --auto

# Apply migrations
piccolo migrations forwards all
```

This will create all 8 staging tables:
- `staging.staging_article`
- `staging.staging_product`
- `staging.staging_article_image`
- `staging.staging_article_text`
- `staging.staging_product_image`
- `staging.staging_product_text`
- `staging.rejection_queue`
- `staging.archive`

### 3. Run the Application

```bash
# Terminal 1: Backend API
python backend/main.py
# Access at: http://localhost:8000
# API Docs: http://localhost:8000/docs

# Terminal 2: Frontend UI
reflex run
# Access at: http://localhost:3000
```

### 4. Test the System

1. **Login**: Go to http://localhost:3000/login
   - Token: `provenpick-staging-secret-token-2026`

2. **Dashboard**: View pending articles (will be empty initially)

3. **Submit Test Article**: Use API docs at http://localhost:8000/docs
   - Navigate to POST `/api/pipeline/submit`
   - Submit test article data

4. **Review**: Click article in dashboard to review

5. **Approve/Reject**: Test the workflow

## Integration Tasks

### High Priority: Production Migration

The approval workflow has a placeholder function that needs implementation:

**File**: `backend/services/approval.py` (line ~75)

```python
async def migrate_to_production(full_data: Dict[str, Any]) -> Dict[str, int]:
    """
    TODO: Implement actual migration to production tables
    
    This function should:
    1. Insert products into public.product_table
    2. Insert product images/texts
    3. Insert article into public.article_table  
    4. Insert article images/texts
    5. Return mapping of staging_id -> production_id
    """
```

You'll need to:
1. Import production tables from main ProvenPick
2. Map staging data to production format
3. Insert into `public` schema tables
4. Handle transactions properly

## Current Status

✅ Repository created: https://github.com/sairamtvv/provenpick-staging  
✅ Database schema created  
✅ Environment configured  
✅ Ready for dependency installation  
⏳ Awaiting: Dependency installation + migration implementation  

## Quick Reference

### Database Connection String
```
postgresql://provenpick:provenpick@localhost:5432/provenpick
```

### Authentication Token
```
provenpick-staging-secret-token-2026
```

### URLs
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Frontend UI: http://localhost:3000
- GitHub: https://github.com/sairamtvv/provenpick-staging

---

**Status**: Environment ready! Install dependencies and you're good to go! 🚀
