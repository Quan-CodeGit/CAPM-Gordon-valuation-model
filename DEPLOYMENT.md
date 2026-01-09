# Deployment Guide

This guide explains how to deploy the CAPM & Gordon Model Calculator with automatic updates from GitHub.

## Quick Start: Deploy on Render (Recommended)

Render offers free hosting with automatic deployments from GitHub.

### Step 1: Sign Up for Render

1. Go to https://render.com
2. Sign up with your GitHub account
3. Authorize Render to access your repositories

### Step 2: Deploy the Backend

1. Click "New +" → "Web Service"
2. Connect your repository: `Quan-CodeGit/CAPM-Gordon-valuation-model`
3. Configure the service:
   - **Name**: `capm-gordon-api` (or your preferred name)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements_tradingview.txt`
   - **Start Command**: `python backend_tradingview.py`
   - **Instance Type**: `Free`
4. Click "Create Web Service"

Render will automatically deploy and give you a URL like:
```
https://capm-gordon-api.onrender.com
```

### Step 3: Update Frontend to Use Deployed Backend

1. Edit `index.html` line 94
2. Change:
   ```javascript
   const API_URL = 'http://localhost:5000';
   ```
   To:
   ```javascript
   const API_URL = 'https://capm-gordon-api.onrender.com'; // Your Render URL
   ```
3. Commit and push:
   ```bash
   git add index.html
   git commit -m "Update API URL to Render deployment"
   git push origin main
   ```

### Step 4: Deploy Frontend on GitHub Pages

1. Go to your GitHub repository settings
2. Navigate to **Settings** → **Pages**
3. Under "Source":
   - Branch: `main`
   - Folder: `/ (root)`
4. Click "Save"

After a few minutes, your site will be live at:
```
https://quan-codegit.github.io/CAPM-Gordon-valuation-model/
```

## Automatic Updates

Once deployed, any push to GitHub will automatically:

- ✅ **Backend (Render)**: Auto-deploys within 2-3 minutes
- ✅ **Frontend (GitHub Pages)**: Auto-updates within 1-2 minutes

Simply:
```bash
# Make your changes
git add .
git commit -m "Your update message"
git push origin main
```

Both backend and frontend will update automatically!

## Alternative: Deploy Everything on Render

If you prefer to host both frontend and backend on Render:

### Option 1: Use render.yaml (Included)

The `render.yaml` file is already configured. Just:

1. Click "New +" → "Blueprint"
2. Connect your repository
3. Render will automatically create the service from `render.yaml`

### Option 2: Serve Frontend from Backend

Add this to `backend_tradingview.py` after the imports:

```python
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)
```

Then deploy as a single web service on Render.

## Alternative: Deploy on Vercel

Vercel supports Python backends and offers automatic deployments:

### Step 1: Install Vercel CLI
```bash
npm i -g vercel
```

### Step 2: Deploy
```bash
vercel
```

Follow the prompts and your app will be live!

Vercel automatically:
- Detects your Python backend
- Serves your frontend
- Sets up automatic deployments from GitHub

## Alternative: Deploy on Railway

Railway is another excellent option:

1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway automatically detects and deploys your Flask app
5. Get your deployment URL

## Monitoring & Logs

### Render
- Dashboard shows deployment status
- Click "Logs" to see real-time application logs
- Health endpoint: `https://your-app.onrender.com/health`

### GitHub Pages
- Check Actions tab for deployment status
- Usually deploys within 1-2 minutes

## Troubleshooting

### Backend Not Starting on Render
- Check logs in Render dashboard
- Verify `requirements_tradingview.txt` has all dependencies
- Check Python version compatibility

### CORS Issues
- Make sure Flask-CORS is installed: `pip install flask-cors`
- Backend already has CORS enabled in `backend_tradingview.py`

### Frontend Can't Connect to Backend
- Verify API_URL in `index.html` points to your deployed backend
- Check browser console for errors
- Test backend directly: `https://your-app.onrender.com/health`

### GitHub Pages Not Updating
- Go to Actions tab to see deployment status
- May need to clear browser cache
- Check that branch and folder are correct in Settings → Pages

## Cost

All options above offer **free tiers**:

- ✅ **Render Free**: 750 hours/month, sleeps after 15 min inactivity
- ✅ **GitHub Pages**: Free for public repositories, unlimited bandwidth
- ✅ **Vercel Free**: 100 GB bandwidth/month
- ✅ **Railway Free**: $5 credit/month

**Recommendation**:
- Backend on Render (free)
- Frontend on GitHub Pages (free)
- Total cost: **$0/month**

## Performance Notes

**Render Free Tier**:
- Cold start: 30-60 seconds (first request after inactivity)
- Subsequent requests: Fast (<1 second)
- Stays active for 15 minutes after last request

**Tip**: For better performance, upgrade to Render Starter ($7/month) for always-on instance with no cold starts.

## Custom Domain (Optional)

### GitHub Pages
1. Go to Settings → Pages
2. Add your custom domain
3. Update DNS records as instructed

### Render
1. Go to your service → Settings
2. Add custom domain
3. Update DNS records as instructed

Both platforms provide SSL certificates automatically!
