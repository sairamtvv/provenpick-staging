# ProvenPick Staging System - Quick Start Guide

## ✅ Services Status

All services are running and ready to use!

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8080  
- **API Docs**: http://localhost:8080/docs
- **Websocket**: ws://localhost:8000

## 🔑 Authentication

**Admin Token**: `provenpick-staging-secret-token-2026`

## 🚀 Getting Started

### Step 1: Access the Application

1. Open your browser (preferably in **Incognito/Private mode** for a clean start)
2. Navigate to: **http://localhost:3000**
3. You should see the login page

### Step 2: Login

1. Enter the admin token in the password field:
   ```
   provenpick-staging-secret-token-2026
   ```

2. Click "Login"

3. You'll be redirected to the dashboard

### Step 3: Review Articles

On the dashboard, you'll see **8 pending articles** (2 were already approved/rejected in testing):

1. Click **"Review"** on any article
2. You'll see:
   - Article title and metadata
   - All products (Top Pick, Runner-up, Budget Pick)
   - Product details, prices, images
   - Article images and content

3. You can:
   - **Approve**: Archives the article (production migration disabled for now)
   - **Reject**: Enter comments and reject (adds to rejection queue)

### Step 4: View Archive

- Click on the "Archive" link to see approved and rejected articles
- You'll see 2 archived items from earlier testing

## 📊 Available Test Data

- **Total Articles Created**: 10
- **Pending Review**: 8
- **Already Approved**: 1
- **Already Rejected**: 1

### Sample Articles:

1. Best Wireless Headphones for 2026
2. Top Gaming Laptops Under $2000
3. Best Budget Smartphones of 2026
4. Professional Cameras for Content Creators
5. Best 4K Monitors for Productivity
6. Top Mechanical Keyboards for 2026
7. Best Wireless Mice for Productivity
8. Best Webcams for Remote Work

Each article has:
- 3 products with full details
- Product images (placeholder from picsum.photos)
- Product descriptions and specifications
- Article images (hook, mindmap, general)
- Article text sections (summary, methodology, etc.)

## 🔧 Troubleshooting

### Issue: 401 Unauthorized Error

**Solution**:
1. Clear browser storage:
   - Press F12 to open DevTools
   - Go to "Application" tab
   - Expand "Local Storage"
   - Right-click on "http://localhost:3000"
   - Click "Clear"

2. Refresh the page (Ctrl+R)
3. Login again with the token

### Issue: Can't see articles on dashboard

**Solution**:
1. Check backend is running:
   ```bash
   curl http://localhost:8080/
   ```
   Should return: `{"status":"ok","service":"ProvenPick Staging API","version":"1.0.0"}`

2. Test API with authentication:
   ```bash
   curl -H "Authorization: Bearer provenpick-staging-secret-token-2026" \
        http://localhost:8080/api/articles/
   ```

### Issue: Services not running

**Restart both services**:
```bash
# Backend
cd /home/sai/Desktop/Projects_and_Folders/my_code/provenpick-staging
export $(cat .env | grep -v '^#' | xargs)
export PYTHONPATH=$(pwd):$PYTHONPATH
source .venv/bin/activate
python backend/main.py > backend.log 2>&1 &

# Frontend
source .venv/bin/activate
reflex run > frontend.log 2>&1 &
```

## 📝 API Testing (Optional)

Test the API directly with curl:

```bash
# List all pending articles
curl -H "Authorization: Bearer provenpick-staging-secret-token-2026" \
     http://localhost:8080/api/articles/

# Get specific article
curl -H "Authorization: Bearer provenpick-staging-secret-token-2026" \
     http://localhost:8080/api/articles/1

# Approve article
curl -X POST \
     -H "Authorization: Bearer provenpick-staging-secret-token-2026" \
     http://localhost:8080/api/articles/2/approve

# Reject article
curl -X POST \
     -H "Authorization: Bearer provenpick-staging-secret-token-2026" \
     -H "Content-Type: application/json" \
     -d '{"comments": "Images need better quality"}' \
     http://localhost:8080/api/articles/3/reject

# View archive
curl -H "Authorization: Bearer provenpick-staging-secret-token-2026" \
     http://localhost:8080/api/archive/
```

## 🎯 What Works

✅ **Authentication**: Token-based auth with localStorage persistence  
✅ **Article Listing**: Dashboard shows all pending articles  
✅ **Article Details**: Full article view with products and content  
✅ **Approval Workflow**: Approve articles (archived, production migration disabled)  
✅ **Rejection Workflow**: Reject with comments, adds to rejection queue  
✅ **Archive**: View historical approved/rejected articles  
✅ **API**: All REST endpoints working correctly  

## 📌 Notes

- **Production Migration**: Currently disabled (production tables not set up)
- **Images**: Using picsum.photos for placeholder images
- **Database**: PostgreSQL with staging schema
- **Test Data**: 10 articles, 30 products, all with full content

## 🎉 Success Criteria

If you can:
1. ✅ Login with the token
2. ✅ See 8 pending articles on the dashboard
3. ✅ Click "Review" to view an article
4. ✅ Approve or reject an article
5. ✅ See the article move to the archive

**Then everything is working perfectly!**
