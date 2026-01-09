# Private Deployment Guide
## Keep Code Private, Make App Public

This guide shows how to deploy your app so everyone can use it, but they can't see or copy your code.

---

## Step 1: Make GitHub Repository Private

1. Go to your repository: https://github.com/Quan-CodeGit/CAPM-Gordon-valuation-model
2. Click **Settings** (top right)
3. Scroll down to **Danger Zone**
4. Click **Change visibility** → **Make private**
5. Confirm by typing the repository name

✅ **Result**: Your code is now hidden. Only you can see it.

---

## Step 2: Deploy Backend on Render (Private Repo Supported)

Render can deploy from private GitHub repositories!

### 2.1: Sign up on Render
1. Go to https://render.com
2. Click **Get Started for Free**
3. Sign up with your GitHub account
4. Authorize Render to access your **private repositories**

### 2.2: Create Web Service
1. Click **New +** → **Web Service**
2. Find and select your private repository: `CAPM-Gordon-valuation-model`
3. Configure:
   - **Name**: `capm-gordon-api`
   - **Region**: Singapore (closest to Vietnam)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements_tradingview.txt`
   - **Start Command**: `python backend_tradingview.py`
   - **Instance Type**: `Free` (or Starter $7/month for better performance)

4. Click **Create Web Service**

### 2.3: Wait for Deployment
- Render will build and deploy (takes 2-5 minutes)
- You'll get a URL like: `https://capm-gordon-api.onrender.com`
- Test it: `https://capm-gordon-api.onrender.com/health`

✅ **Result**: Your backend API is public, but source code stays private on GitHub.

---

## Step 3: Update Frontend to Use Deployed Backend

Since the repository is private, we need to host the frontend separately.

### 3.1: Update index.html
1. Open `index.html`
2. Find line 94 (search for `API_URL`)
3. Change from:
   ```javascript
   const API_URL = 'http://localhost:5000';
   ```
   To:
   ```javascript
   const API_URL = 'https://capm-gordon-api.onrender.com'; // Your Render URL
   ```

4. Save the file

### 3.2: Commit and Push (so Render stays updated)
```bash
git add index.html
git commit -m "Update API URL to production backend"
git push origin main
```

---

## Step 4: Deploy Frontend (Multiple Options)

### Option A: Netlify (Recommended - Easiest)

**Why Netlify?**
- ✅ Can deploy from private GitHub repos
- ✅ Automatic HTTPS
- ✅ Custom domains
- ✅ Auto-updates on git push

**Steps:**
1. Go to https://netlify.com
2. Sign up with GitHub
3. Click **Add new site** → **Import an existing project**
4. Choose **GitHub** → Select your private repository
5. Configure:
   - **Build command**: Leave empty (no build needed)
   - **Publish directory**: `/` (root)
6. Click **Deploy**

You'll get: `https://your-app-name.netlify.app`

**Custom domain (optional):**
- Go to Site settings → Domain management
- Add your domain (e.g., `capm-calculator.com`)

### Option B: Vercel (Also supports private repos)

1. Go to https://vercel.com
2. Sign up with GitHub
3. Click **Add New** → **Project**
4. Import your private repository
5. Click **Deploy**

You'll get: `https://your-app.vercel.app`

### Option C: Render Static Site (All-in-one)

1. In Render dashboard, click **New +** → **Static Site**
2. Connect your private repository
3. Configure:
   - **Build Command**: Leave empty
   - **Publish Directory**: `/`
4. Click **Create Static Site**

You'll get: `https://your-app.onrender.com`

### Option D: Host on Your Own Server (Full Control)

If you have a web server or want to use a service like DigitalOcean:

1. Copy `index.html` to your server
2. Serve it via Apache/Nginx/any web server
3. Point your domain to it

---

## Step 5: Test Your Deployment

1. **Backend Health Check:**
   ```
   https://capm-gordon-api.onrender.com/health
   ```
   Should return: `{"status": "healthy", ...}`

2. **Frontend Access:**
   ```
   https://your-app.netlify.app
   ```
   Should show the calculator interface

3. **Try a stock:**
   - Select Vietnam market
   - Enter "VNM"
   - Click "Calculate Valuation"
   - Should return results!

---

## What Users See vs. What They Can't See

### ✅ Users CAN:
- Use your calculator at `https://your-app.netlify.app`
- Analyze stocks
- See results and warnings
- Share the URL with others

### ❌ Users CANNOT:
- See your source code (private GitHub)
- Download your code
- Fork your repository
- See your Python backend logic
- Copy your valuation algorithms

**How?**
- GitHub repo is **private** → Code hidden
- Frontend is compiled HTML → Hard to copy logic
- Backend is on Render → They only see API responses, not Python code

---

## Automatic Updates

Even with a private repo, automatic updates work!

```bash
# Make changes
git add .
git commit -m "Update feature"
git push origin main
```

**What happens:**
- ✅ Render backend auto-redeploys (2-3 min)
- ✅ Netlify/Vercel frontend auto-updates (1-2 min)
- ✅ Users see new version immediately
- ❌ Users still can't see your code

---

## Cost Summary

### Free Tier (Recommended for Starting)
- **Render Free**: 750 hours/month backend
- **Netlify Free**: 100GB bandwidth/month frontend
- **Total**: **$0/month**

**Limitations:**
- Render: Cold start after 15 min inactivity (30-60 sec delay)
- Netlify: Public facing, but code stays private

### Paid Tier (Better Performance)
- **Render Starter**: $7/month - Always on, no cold starts
- **Netlify Pro**: $19/month - More bandwidth, better support
- **Total**: **$7-26/month**

**Recommended**: Start free, upgrade to Render Starter ($7) if cold starts are annoying

---

## Protecting Your Deployed Frontend

Even though the frontend HTML is public, here's how to make it harder to copy:

### Option 1: Obfuscate JavaScript (Optional)

1. Install JavaScript obfuscator:
   ```bash
   npm install -g javascript-obfuscator
   ```

2. Obfuscate your inline JavaScript:
   ```bash
   javascript-obfuscator index.html --output index.min.html
   ```

3. Use `index.min.html` for deployment

### Option 2: Add Copyright Notice

Add this to your `index.html` in the `<head>`:
```html
<!--
  CAPM & Gordon Model Stock Valuation Calculator
  Copyright (c) 2026 Bobby. All Rights Reserved.
  Unauthorized copying, modification, or distribution is prohibited.
-->
```

### Option 3: Disable Right-Click (Annoying but effective)

Add to your HTML before `</body>`:
```html
<script>
  document.addEventListener('contextmenu', e => e.preventDefault());
  document.addEventListener('keydown', e => {
    if (e.key === 'F12' || (e.ctrlKey && e.shiftKey && e.key === 'I')) {
      e.preventDefault();
    }
  });
</script>
```

**Note:** These are deterrents, not foolproof. The real protection is your **private GitHub repo** keeping the backend logic secret.

---

## Sharing Your App

Once deployed, share your URL:

- ✅ **Public URL**: `https://your-app.netlify.app`
- ❌ **GitHub Repo**: Private, don't share

Users can:
- Use the calculator
- Share the link
- Bookmark it

But they can't:
- See your algorithms
- Copy your backend logic
- Fork or modify your code

---

## Monitoring Usage

### Render Dashboard
- View API requests
- Monitor performance
- See error logs
- Track bandwidth usage

### Netlify/Vercel Dashboard
- View page views
- Monitor bandwidth
- See deployment history
- Analytics (paid plans)

---

## Next Steps

1. ✅ Make GitHub repo private
2. ✅ Deploy backend on Render
3. ✅ Update frontend with backend URL
4. ✅ Deploy frontend on Netlify/Vercel
5. ✅ Share public URL with users

Your code stays private, but everyone can use your app! 🎉
