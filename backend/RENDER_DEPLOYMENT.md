# Render Deployment Instructions

## Quick Fix for Port Timeout Issue

The port timeout error usually occurs because:
1. The app fails to start before binding to the port
2. The working directory is incorrect
3. Import errors prevent the app from loading

## Solution

### Option 1: Use the Correct Start Command (Recommended)

In Render dashboard, set the **Start Command** to:

```bash
cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Important**: Make sure you include `cd backend` if your repository root is not the backend folder.

### Option 2: Use Python Startup Script

Set the **Start Command** to:

```bash
cd backend && python start.py
```

### Option 3: Use Shell Script

Set the **Start Command** to:

```bash
cd backend && chmod +x start.sh && ./start.sh
```

## Render Dashboard Configuration

### Build Settings

- **Build Command**: `cd backend && pip install -r requirements.txt`
- **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

### Environment Variables (Required)

Add these in Render dashboard → Environment:

```
GOOGLE_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
MONGODB_URI=your_mongodb_uri
SECRET_KEY=your_secret_key
PINECONE_INDEX_NAME=research-index
```

### Service Settings

- **Health Check Path**: `/health`
- **Auto-Deploy**: Yes (if using Git)

## Common Issues

### 1. Port Timeout

**Cause**: App not starting or not binding to port

**Fix**:
- Verify start command includes `--host 0.0.0.0 --port $PORT`
- Check build logs for import errors
- Ensure you're in the correct directory (`cd backend`)

### 2. Import Errors

**Cause**: Missing dependencies or Python version mismatch

**Fix**:
- Check `requirements.txt` has all packages
- Verify Python version (3.11 or 3.12 recommended)
- Review build logs for specific missing packages

### 3. MongoDB Connection Errors

**Cause**: MongoDB URI not set or connection blocked

**Fix**:
- Verify `MONGODB_URI` is set in Render environment variables
- Check MongoDB Atlas IP whitelist (add `0.0.0.0/0` for testing)

### 4. Module Not Found

**Cause**: Working directory issue

**Fix**:
- Use `cd backend &&` prefix in all commands
- Or set root directory to `backend` folder in Render settings

## Verification

After deployment, test:

```bash
curl https://your-service.onrender.com/health
```

Should return: `{"status": "healthy", "service": "Strategic Intelligence Assistant API"}`

## Debugging

1. **Check Build Logs**: Look for installation errors
2. **Check Runtime Logs**: Look for startup errors
3. **Test Locally**: Run `uvicorn main:app --host 0.0.0.0 --port 8000` locally first
4. **Verify Environment**: Ensure all required env vars are set

## Alternative: Manual Deployment

If automatic deployment fails:

1. SSH into Render service (if available)
2. Manually run: `cd backend && pip install -r requirements.txt`
3. Test: `python start.py`
4. Check for specific error messages

