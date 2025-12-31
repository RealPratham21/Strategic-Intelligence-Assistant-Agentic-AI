# Render Deployment Fix - Port Timeout Issue

## Problem
Render is timing out because it can't detect an open port. This happens when the app fails to start before binding to the port.

## Root Causes
1. **Working Directory Issue**: If your repository root is not the `backend` folder, you need to `cd backend` first
2. **Import Errors**: The app might fail to import modules, preventing startup
3. **Missing Dependencies**: Some packages might not be installing correctly
4. **Environment Variables**: Missing required env vars can cause silent failures

## Solution

### Step 1: Update Render Dashboard Settings

Go to your Render service dashboard and update these settings:

#### Build Command:
```bash
cd backend && pip install -r requirements.txt
```

#### Start Command:
```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

**CRITICAL**: Make sure you include `cd backend &&` at the beginning if your `main.py` is in the `backend` folder.

### Step 2: Verify Environment Variables

In Render dashboard → Environment, ensure these are set:

```
GOOGLE_API_KEY=your_key
PINECONE_API_KEY=your_key
MONGODB_URI=your_mongodb_uri
SECRET_KEY=your_secret_key
PINECONE_INDEX_NAME=research-index
```

### Step 3: Check Service Settings

- **Health Check Path**: `/health`
- **Auto-Deploy**: Yes (if using Git)

### Step 4: Alternative Start Commands (if above doesn't work)

Try these alternatives in order:

**Option A - Using Python script:**
```bash
cd backend && python start.py
```

**Option B - Using shell script:**
```bash
cd backend && bash start.sh
```

**Option C - Direct uvicorn with explicit path:**
```bash
cd backend && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Debugging Steps

### 1. Check Build Logs
- Go to Render dashboard → Logs
- Look for any import errors or missing packages
- Common errors: `ModuleNotFoundError`, `ImportError`

### 2. Check Runtime Logs
- After build completes, check runtime logs
- Look for startup errors
- The app should print: "Uvicorn running on..."

### 3. Test Locally First
Before deploying, test locally:

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

If it works locally, it should work on Render.

### 4. Verify Port Binding
The app must bind to `0.0.0.0` (not `127.0.0.1`) and use `$PORT` environment variable.

## Common Errors and Fixes

### Error: "Port scan timeout"
**Fix**: 
- Ensure start command uses `--host 0.0.0.0 --port $PORT`
- Check that `cd backend` is included if needed
- Verify no import errors in build logs

### Error: "ModuleNotFoundError"
**Fix**:
- Check `requirements.txt` has all dependencies
- Verify build command installs from correct directory
- Check Python version compatibility

### Error: "MongoDB connection failed"
**Fix**:
- This shouldn't prevent startup (connections are lazy)
- But verify `MONGODB_URI` is set correctly
- Check MongoDB Atlas IP whitelist

## Verification

After deployment, test the health endpoint:

```bash
curl https://your-service-name.onrender.com/health
```

Expected response:
```json
{"status": "healthy", "service": "Strategic Intelligence Assistant API"}
```

## Files Created

I've created these files to help:

1. **`backend/start.py`** - Python startup script with error handling
2. **`backend/start.sh`** - Bash startup script
3. **`backend/render.yaml`** - Render configuration file (optional)
4. **`backend/RENDER_DEPLOYMENT.md`** - Detailed deployment guide

## Quick Checklist

- [ ] Build command includes `cd backend &&` if needed
- [ ] Start command includes `cd backend &&` if needed
- [ ] Start command uses `--host 0.0.0.0 --port $PORT`
- [ ] All environment variables are set in Render
- [ ] Health check path is set to `/health`
- [ ] App works locally before deploying
- [ ] Build logs show no errors
- [ ] Runtime logs show "Uvicorn running on..."

## Still Having Issues?

1. Check Render service logs for specific error messages
2. Try deploying with the Python startup script: `cd backend && python start.py`
3. Verify your repository structure matches what Render expects
4. Consider setting the root directory to `backend` in Render settings instead of using `cd backend`

