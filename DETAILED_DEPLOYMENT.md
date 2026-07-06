# Ultra-Detailed Deployment Guide

## Step 1: Deploy Backend to Railway

### 1.1 Create Railway Account
1. Open browser, go to: https://railway.app
2. Click "Login" in top right
3. Choose "Continue with GitHub" (recommended)
4. Authorize Railway to access your GitHub
5. You'll be redirected to Railway dashboard

### 1.2 Create New Project
1. On Railway dashboard, click "New Project" button (top left)
2. A modal will appear with options
3. Click "Deploy from GitHub repo"
4. Railway will show your GitHub repositories

### 1.3 Select Repository
1. Find and click on `smartsupport-ai` repository
2. Click "Import" button
3. Railway will show deployment configuration

### 1.4 Set Root Directory
1. Look for "Root Directory" field
2. Click inside the field
3. Type: `apps/backend`
4. Click outside the field or press Enter
5. Railway will detect the Dockerfile automatically

### 1.5 Start Deployment
1. Click "Deploy" button
2. Railway will start building your backend
3. Wait for build to complete (2-3 minutes)
4. You'll see a green checkmark when done
5. Your backend will have a URL like: `https://smartsupport-backend-xxx.up.railway.app`

### 1.6 Add PostgreSQL Database
1. In your Railway project, look at the left sidebar
2. Click "+ New Service" button (top of sidebar)
3. A menu will appear
4. Click "Database"
5. Click "PostgreSQL"
6. Railway will create a PostgreSQL service
7. Wait for it to be ready (green checkmark)

### 1.7 Add Volume for ChromaDB
1. In the left sidebar, click "+ New Service" again
2. Click "Storage"
3. Click "Volume"
4. In "Name" field, type: `chroma-data`
5. In "Mount Path" field, type: `/chroma`
6. Click "Add Volume"
7. Wait for it to be ready

### 1.8 Configure Environment Variables
1. Click on your backend service in the left sidebar
2. Click "Variables" tab (top of the service view)
3. Click "+ New Variable" button
4. Add these variables one by one:

**Variable 1:**
- Name: `SECRET_KEY`
- Value: Generate one by opening terminal and running: `openssl rand -hex 32`
- Copy the output and paste as value
- Click "Add"

**Variable 2:**
- Name: `AI_API_KEY`
- Value: Your OpenAI API key (starts with `sk-`)
- Click "Add"

**Variable 3:**
- Name: `CORS_ORIGINS`
- Value: `http://localhost:3000`
- Click "Add"

**Variable 4:**
- Name: `APP_ENV`
- Value: `production`
- Click "Add"

**Variable 5:**
- Name: `DEBUG`
- Value: `false`
- Click "Add"

### 1.9 Link Database Variables
1. Still in Variables tab
2. Click "+ New Variable"
3. Name: `POSTGRES_HOST`
4. Value: Click the reference icon (looks like `{}`) → Select `RAILWAY_PRIVATE_DOMAIN`
5. Click "Add"

6. Click "+ New Variable"
7. Name: `POSTGRES_PASSWORD`
8. Value: Click reference icon → Select `POSTGRES_PASSWORD` (from PostgreSQL service)
9. Click "Add"

10. Click "+ New Variable"
11. Name: `POSTGRES_USER`
12. Value: Click reference icon → Select `POSTGRES_USER`
13. Click "Add"

14. Click "+ New Variable"
15. Name: `POSTGRES_DB`
16. Value: Click reference icon → Select `POSTGRES_DB`
17. Click "Add"

### 1.10 Run Database Migrations
1. Click on your backend service in left sidebar
2. Look for "Exec" or "Terminal" button (usually top right of service view)
3. Click it
4. A terminal will open in your browser
5. Wait for prompt to appear
6. Type: `alembic upgrade head`
7. Press Enter
8. Wait for migration to complete
9. You should see "Running upgrade..." messages
10. Close the terminal

### 1.11 Copy Backend URL
1. Click on your backend service
2. Look at the top of the service view
3. You'll see a URL like: `https://smartsupport-backend-xxx.up.railway.app`
4. Click the copy button next to it
5. Save this URL somewhere (you'll need it for Vercel)

---

## Step 2: Deploy Frontend to Vercel

### 2.1 Create Vercel Account
1. Open browser, go to: https://vercel.com
2. Click "Login" in top right
3. Choose "Continue with GitHub"
4. Authorize Vercel to access your GitHub
5. You'll be redirected to Vercel dashboard

### 2.2 Create New Project
1. On Vercel dashboard, click "Add New" button (top left)
2. Click "Project" from dropdown
3. Vercel will show your GitHub repositories

### 2.3 Import Repository
1. Find and click on `smartsupport-ai` repository
2. Click "Import" button
3. Vercel will show project configuration

### 2.4 Set Root Directory
1. Look for "Root Directory" field
2. Click inside the field
3. Type: `apps/frontend`
4. Click outside the field or press Enter
5. Vercel will detect Next.js automatically

### 2.5 Configure Project Name
1. Look for "Project Name" field
2. Vercel will suggest a name (e.g., `smartsupport-ai`)
3. You can keep it or change it
4. This will be part of your URL: `https://your-project-name.vercel.app`

### 2.6 Add Environment Variable
1. Scroll down to "Environment Variables" section
2. Click "+ New Variable" button
3. In "Key" field, type: `NEXT_PUBLIC_API_URL`
4. In "Value" field, paste your Railway backend URL with `/api/v1` at the end
   - Example: `https://smartsupport-backend-xxx.up.railway.app/api/v1`
5. Select "All" for environments (Production, Preview, Development)
6. Click "Add"

### 2.7 Deploy
1. Click "Deploy" button at the bottom
2. Vercel will start building your frontend
3. Wait for build to complete (1-2 minutes)
4. You'll see a green checkmark when done
5. Click "Continue to Dashboard"
6. Your frontend URL will be at the top: `https://your-project-name.vercel.app`
7. Copy this URL

---

## Step 3: Update CORS in Railway

### 3.1 Go Back to Railway
1. Go back to Railway tab in your browser
2. Click on your backend service

### 3.2 Update CORS Variable
1. Click "Variables" tab
2. Find the `CORS_ORIGINS` variable
3. Click the edit (pencil) icon
4. Change value to: `https://your-frontend-url.vercel.app,http://localhost:3000`
5. Replace `your-frontend-url.vercel.app` with your actual Vercel URL
6. Click "Save"
7. Railway will automatically redeploy your backend

---

## Step 4: Test Your Deployment

### 4.1 Test Backend Health
1. Open new browser tab
2. Go to: `https://your-backend-url.up.railway.app/api/v1/health`
3. You should see: `{"status": "healthy"}`

### 4.2 Test API Documentation
1. Go to: `https://your-backend-url.up.railway.app/docs`
2. You should see FastAPI Swagger UI
3. Browse the available endpoints

### 4.3 Test Frontend
1. Go to: `https://your-frontend-url.vercel.app`
2. You should see the SmartSupport AI Platform login page
3. Click "Register"
4. Enter email and password
5. Click "Register"
6. You should be redirected to dashboard

### 4.4 Test Document Upload
1. In dashboard, click "Upload Document"
2. Click "Choose File"
3. Select a PDF file from your computer
4. Click "Upload"
5. Wait for processing (30-60 seconds)
6. Document should appear in the list

### 4.5 Test RAG Chat
1. In dashboard, click "Chat"
2. Type a question about your uploaded document
3. Click "Send"
4. Wait for AI response
5. You should see an answer with source citations

---

## Troubleshooting

### Backend won't start
1. Click on backend service in Railway
2. Click "Logs" tab
3. Look for error messages
4. Common issues:
   - Missing SECRET_KEY
   - Database not connected
   - Invalid AI_API_KEY

### CORS errors
1. Make sure CORS_ORIGINS includes your Vercel URL
2. URL must be HTTPS (not HTTP)
3. No trailing slashes
4. Comma-separated, no spaces

### Frontend build errors
1. Click on project in Vercel
2. Click "Deployments" tab
3. Click on failed deployment
4. Look at build logs
5. Common issues:
   - Wrong root directory
   - Missing NEXT_PUBLIC_API_URL
   - Invalid backend URL

### Database connection errors
1. Verify PostgreSQL service is running in Railway
2. Check database variables are linked correctly
3. Look for connection errors in backend logs

---

## You're Done! 🎉

Your app is live:
- **Frontend**: Your Vercel URL
- **Backend**: Your Railway URL
- **API Docs**: Your Railway URL + `/docs`
