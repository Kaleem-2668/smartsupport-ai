# Simple Deployment Guide - Orin

**Quick deployment using Railway and Vercel with built-in services.**

## What You Need

- **GitHub account** (for deployment)
- **Railway account** (https://railway.app) - $5 free credit
- **Vercel account** (https://vercel.com) - free
- **OpenAI API key** (for AI features)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Vercel Frontend                    │
│                   (Next.js)                          │
└──────────────────┬──────────────────────────────────┘
                   │ HTTPS
┌──────────────────▼──────────────────────────────────┐
│                  Railway Backend                     │
│              (FastAPI + PostgreSQL + ChromaDB)       │
│              (All in one project)                    │
└─────────────────────────────────────────────────────┘
```

## Step 1: Deploy Backend on Railway (5 minutes)

1. **Go to Railway**
   - Visit https://railway.app and sign up/login
   - Click "New Project" → "Deploy from GitHub repo"

2. **Select Repository**
   - Choose your `smartsupport-ai` repository
   - Set root directory to: `apps/backend`
   - Click "Deploy"

3. **Add PostgreSQL Database**
   - In your Railway project, click "+ New Service"
   - Select "PostgreSQL"
   - Railway will create a database automatically

4. **Add Persistent Volume for ChromaDB**
   - Click "+ New Service"
   - Select "Volume"
   - Name it: `chroma-data`
   - Mount path: `/chroma`

5. **Configure Environment Variables**
   - Go to your backend service → Variables
   - Add these variables:

   ```bash
   # App
   APP_ENV=production
   DEBUG=false

   # Security (generate with: openssl rand -hex 32)
   SECRET_KEY=your-generated-secret-key-here

   # Database (Railway auto-fills these)
   POSTGRES_HOST=${{RAILWAY_PRIVATE_DOMAIN}}
   POSTGRES_PASSWORD=${{POSTGRES_PASSWORD}}
   POSTGRES_USER=${{POSTGRES_USER}}
   POSTGRES_DB=${{POSTGRES_DB}}

   # ChromaDB (use local storage)
   CHROMA_HOST=localhost
   CHROMA_PORT=8000

   # AI (your OpenAI key)
   AI_API_KEY=sk-your-openai-api-key-here

   # CORS (update after frontend deploy)
   CORS_ORIGINS=http://localhost:3000
   ```

6. **Run Migrations**
   - Go to backend service → "Exec" (terminal icon)
   - Run:
   ```bash
   alembic upgrade head
   ```

7. **Copy Backend URL**
   - Railway will show: `https://your-backend.up.railway.app`
   - Copy this URL

## Step 2: Deploy Frontend on Vercel (3 minutes)

1. **Go to Vercel**
   - Visit https://vercel.com and sign up/login
   - Click "Add New" → "Project"

2. **Import Repository**
   - Select your `smartsupport-ai` repository
   - Set root directory to: `apps/frontend`
   - Click "Import"

3. **Add Environment Variable**
   - In project settings → Environment Variables
   - Add:
   ```bash
   NEXT_PUBLIC_API_URL=https://your-backend-url.up.railway.app/api/v1
   ```

4. **Deploy**
   - Click "Deploy"
   - Wait for build to complete
   - Copy the frontend URL: `https://your-app.vercel.app`

## Step 3: Update CORS (1 minute)

1. **Go back to Railway**
   - Backend service → Variables
   - Update CORS_ORIGINS:
   ```bash
   CORS_ORIGINS=https://your-app.vercel.app,http://localhost:3000
   ```

2. **Railway will auto-redeploy**

## Step 4: Test (2 minutes)

1. **Visit your frontend URL**
   - You should see the login page

2. **Test registration**
   - Create an account
   - Login

3. **Test document upload**
   - Upload a PDF
   - Wait for processing

4. **Test chat**
   - Ask a question about your document

## Done! 🎉

Your app is now live at:
- **Frontend**: `https://your-app.vercel.app`
- **Backend**: `https://your-backend.up.railway.app`
- **API Docs**: `https://your-backend.up.railway.app/docs`

## Free Tier Limits

| Service | Limit |
|---------|-------|
| Railway | $5/month credit (~500 hours runtime) |
| Vercel | 100GB bandwidth/month |
| PostgreSQL | 1GB storage (Railway) |
| Volume | 1GB storage (Railway) |

## Troubleshooting

**Backend won't start?**
- Check Railway logs
- Verify SECRET_KEY is set
- Ensure database is attached

**CORS errors?**
- Make sure CORS_ORIGINS includes your Vercel URL
- Use HTTPS, not HTTP

**Database errors?**
- Verify PostgreSQL service is running
- Check database variables are linked correctly

**ChromaDB errors?**
- Ensure volume is mounted at `/chroma`
- Check ChromaDB is running before backend starts

## Need Help?

Check the logs in Railway and Vercel dashboards.
