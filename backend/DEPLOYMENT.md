# Render Deployment Guide

## Prerequisites

1. Render account (https://render.com)
2. All environment variables configured in Render dashboard

## Deployment Steps

### 1. Create a New Web Service on Render

1. Go to your Render dashboard
2. Click "New +" → "Web Service"
3. Connect your repository or deploy manually

### 2. Configure Build Settings

- **Name**: `strategic-intelligence-assistant-api` (or your preferred name)
- **Environment**: `Python 3`
- **Build Command**: `cd backend && pip install -r requirements.txt`
- **Start Command**: `cd backend && uvicorn main:app --host 0.0.0.0 --port $PORT`

**OR** use the Python startup script:
- **Start Command**: `cd backend && python start.py`

### 3. Set Environment Variables

In Render dashboard, add these environment variables:

```
GOOGLE_API_KEY=your_google_api_key
PINECONE_API_KEY=your_pinecone_api_key
MONGODB_URI=your_mongodb_connection_string
SECRET_KEY=your_secret_key
PINECONE_INDEX_NAME=research-index
ALLOWED_ORIGINS=* (or specific domains)
```

### 4. Important Settings

- **Auto-Deploy**: Yes (if using Git)
- **Health Check Path**: `/health`
- **Plan**: Free tier or higher

### 5. Common Issues and Solutions

#### Issue: Port scan timeout
**Solution**: 
- Make sure start command uses `$PORT` environment variable
- Ensure the command is: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Check that you're in the correct directory (`cd backend`)

#### Issue: Import errors
**Solution**:
- Verify all dependencies are in `requirements.txt`
- Check that Python version is compatible (3.11 or 3.12 recommended)
- Review build logs for missing packages

#### Issue: MongoDB connection errors
**Solution**:
- Verify `MONGODB_URI` is set correctly in Render environment variables
- Check MongoDB Atlas IP whitelist (add Render's IP or 0.0.0.0/0)

#### Issue: Pinecone connection errors
**Solution**:
- Verify `PINECONE_API_KEY` is set correctly
- Ensure Pinecone index exists and name matches `PINECONE_INDEX_NAME`

### 6. Verify Deployment

After deployment, test the health endpoint:
```
https://your-service-name.onrender.com/health
```

Should return: `{"status": "healthy"}`

### 7. Update Frontend

Update `frontend/streamlit_app.py` to use your Render backend URL:
```python
BASE_URL = "https://your-service-name.onrender.com"
```

## Alternative: Using render.yaml

If you prefer, you can use the `render.yaml` file:

1. Place `render.yaml` in your repository root
2. Render will automatically detect and use it
3. Adjust the configuration as needed

## Troubleshooting

1. **Check Build Logs**: Look for import errors or missing dependencies
2. **Check Runtime Logs**: Look for application startup errors
3. **Test Locally First**: Make sure the app runs locally before deploying
4. **Verify Environment Variables**: Double-check all required variables are set

## Support

If issues persist, check:
- Render service logs
- Application logs in Render dashboard
- Ensure all dependencies install successfully during build

