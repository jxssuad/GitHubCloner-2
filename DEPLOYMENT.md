# TradingView Access Manager - Render Deployment Guide

This guide walks you through deploying the TradingView Access Management system to Render.

## Prerequisites

1. A Render account (free tier available)
2. TradingView account credentials
3. This codebase repository on GitHub/GitLab

## Quick Deploy

### Option 1: One-Click Deploy (Using render.yaml)

1. Fork/clone this repository to your GitHub account
2. Connect your GitHub account to Render
3. Create a new web service and connect it to your repository
4. Render will automatically detect the `render.yaml` configuration
5. Set the required environment variables (see below)

### Option 2: Manual Setup

1. **Create a Web Service**
   - Go to Render Dashboard → New → Web Service
   - Connect your repository
   - Configure as follows:
     - **Environment**: Python
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 1 main:app`

2. **Create PostgreSQL Database**
   - Go to Render Dashboard → New → PostgreSQL
   - Choose free tier (or paid for production)
   - Note the database name (e.g., `tradingview-postgres`)

## Required Environment Variables

Set these in your Render web service environment settings:

### Required Variables
```
TRADINGVIEW_USERNAME=your_tradingview_username
TRADINGVIEW_PASSWORD=your_tradingview_password
```

### Auto-Configured by Render
```
DATABASE_URL=postgresql://...  (set automatically when you add PostgreSQL)
PORT=10000                     (set automatically by Render)
```

### Optional Variables
```
SESSION_SECRET=auto-generated-by-render  (can be auto-generated)
SESSION_TIMEOUT=3600                     (1 hour default)
LOG_LEVEL=INFO                          (INFO default)
```

## Step-by-Step Deployment

### Step 1: Prepare Your Repository
1. Ensure your code is in a GitHub/GitLab repository
2. Verify all deployment files are present:
   - `render.yaml`
   - `requirements.txt` (managed by Replit)
   - `Procfile`
   - `runtime.txt`

### Step 2: Create Render Services

1. **Database First**:
   - Go to Render Dashboard
   - Click "New" → "PostgreSQL"
   - Name: `tradingview-postgres`
   - Region: Choose closest to your users
   - Plan: Free (or paid for production)
   - Click "Create Database"

2. **Web Service**:
   - Click "New" → "Web Service"
   - Connect your repository
   - Configure:
     - **Name**: `tradingview-access-manager`
     - **Environment**: Python
     - **Region**: Same as database
     - **Branch**: `main` (or your default branch)
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn --bind 0.0.0.0:$PORT --workers 1 main:app`

### Step 3: Environment Variables

In your web service settings, add:

1. **TRADINGVIEW_USERNAME**: Your TradingView username
2. **TRADINGVIEW_PASSWORD**: Your TradingView password
3. **DATABASE_URL**: Link to your PostgreSQL database (Render will auto-populate this)

### Step 4: Deploy

1. Click "Create Web Service"
2. Render will automatically build and deploy your application
3. Monitor the build logs for any errors
4. Once deployed, you'll get a public URL (e.g., `https://your-app.onrender.com`)

## Post-Deployment Setup

### 1. Verify Database Tables
The application automatically creates required database tables on first startup.

### 2. Add Pine Scripts
Add your Pine Script configurations through the admin interface or by updating the `DEFAULT_PINE_IDS` environment variable.

### 3. Test the Application
1. Visit your deployed URL
2. Go to `/manage` to test the username validation
3. Try granting and removing access

## Production Considerations

### Security
- Use strong, unique passwords for TradingView account
- Enable two-factor authentication on TradingView (if supported)
- Regularly rotate the SESSION_SECRET

### Performance
- Consider upgrading to paid Render plan for better performance
- Monitor application logs for any issues
- Set up Render health checks

### Monitoring
- Enable Render's built-in monitoring
- Set up alerts for service downtime
- Monitor database performance

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check that `requirements.txt` includes all dependencies
   - Verify Python version in `runtime.txt`

2. **Database Connection Issues**
   - Ensure DATABASE_URL is properly set
   - Check PostgreSQL service is running
   - Verify database connection string format

3. **TradingView API Issues**
   - Verify credentials are correct
   - Check if TradingView account has required permissions
   - Monitor for rate limiting

4. **Application Errors**
   - Check Render logs for detailed error messages
   - Verify all environment variables are set
   - Ensure static files are served correctly

### Logs Access
- View real-time logs: Render Dashboard → Your Service → Logs
- Download logs for detailed analysis

## Scaling

For high-traffic scenarios:
- Upgrade to paid Render plan with more resources
- Consider using Redis for session storage
- Implement database connection pooling optimizations
- Add monitoring and caching layers

## Support

For deployment issues:
- Check Render's documentation: https://render.com/docs
- Review application logs for specific error messages
- Verify environment variable configuration

## Files Overview

- `render.yaml`: Render service configuration
- `Procfile`: Process configuration for deployment
- `runtime.txt`: Python runtime version
- `requirements.txt`: Python dependencies (auto-managed)
- `.env.example`: Example environment variables for local development
- `DEPLOYMENT.md`: This deployment guide