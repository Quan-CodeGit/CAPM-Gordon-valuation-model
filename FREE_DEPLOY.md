# 100% Free Deployment Guide

Deploy your CAPM calculator for **$0/month** using free services!

---

## Strategy: Frontend on Vercel + Backend on Free Service

- ✅ **Frontend (Vercel)**: Free forever, fast, great UX
- ✅ **Backend (Choose one)**: PythonAnywhere, Glitch, or Replit

---

## Step 1: Deploy Backend (Choose ONE)

### Option A: PythonAnywhere (Recommended - Always On!)

**Why PythonAnywhere?**
- ✅ 100% free forever
- ✅ No sleep mode (always responsive!)
- ✅ Built for Python/Flask
- ✅ 100 seconds/day CPU time (enough for this app)

**Steps:**

1. **Sign up**: https://www.pythonanywhere.com/registration/register/beginner/
2. **Upload your code**:
   - Go to **Files** tab
   - Click **Upload a file**
   - Upload `backend_tradingview.py` and `requirements_tradingview.txt`
3. **Install dependencies**:
   - Go to **Consoles** tab → **Bash**
   - Run:
     ```bash
     pip3 install --user -r requirements_tradingview.txt
     ```
4. **Create Web App**:
   - Go to **Web** tab
   - Click **Add a new web app**
   - Choose **Flask**
   - Python version: **3.10**
   - WSGI file path: `/home/yourusername/backend_tradingview.py`
5. **Configure WSGI**:
   - Click on WSGI configuration file
   - Replace content with:
     ```python
     import sys
     path = '/home/yourusername'  # Change to your username
     if path not in sys.path:
         sys.path.append(path)

     from backend_tradingview import app as application
     ```
6. **Enable CORS** (already in your backend code)
7. **Reload** web app
8. **Get your URL**: `https://yourusername.pythonanywhere.com`

**Test it**: Visit `https://yourusername.pythonanywhere.com/health`

---

### Option B: Glitch (Easy Setup)

**Why Glitch?**
- ✅ Free forever
- ✅ Easy to use
- ✅ 1000 hours/month
- ⚠️ Sleeps after 5 min (wakes in ~5 seconds)

**Steps:**

1. **Go to**: https://glitch.com/
2. **Sign up** with GitHub
3. **New Project** → **Import from GitHub**
4. Enter: `https://github.com/Quan-CodeGit/CAPM-Gordon-valuation-model`
5. **Create `.glitch-assets` file** (empty, just to indicate it's a Glitch project)
6. **Glitch auto-detects Python** and installs dependencies
7. **Get your URL**: `https://your-project.glitch.me`

**Test it**: Visit `https://your-project.glitch.me/health`

---

### Option C: Replit (Free with Limits)

**Why Replit?**
- ✅ Easy setup
- ✅ Built-in code editor
- ⚠️ Sleeps after inactivity on free tier

**Steps:**

1. **Go to**: https://replit.com/
2. **Sign up** with GitHub
3. **Create Repl** → **Import from GitHub**
4. Paste your repo URL
5. **Run** button starts your Flask app
6. **Get your URL**: `https://your-app.your-username.repl.co`

**Test it**: Visit your URL + `/health`

---

## Step 2: Deploy Frontend on Vercel

1. **Go to**: https://vercel.com/
2. **Sign up** with GitHub (if not already)
3. **Update config.js**:
   - Open `config.js` locally
   - Change `BACKEND_URL`:
     ```javascript
     window.CONFIG = {
         BACKEND_URL: 'https://yourusername.pythonanywhere.com'  // Your backend URL
     };
     ```
4. **Commit and push**:
   ```bash
   git add config.js index.html
   git commit -m "Configure backend URL for free deployment"
   git push origin main
   ```
5. **Deploy on Vercel**:
   - Click **Add New** → **Project**
   - Import your GitHub repo
   - Click **Deploy**
6. **Get your URL**: `https://your-app.vercel.app`

---

## Step 3: Test Your App

1. **Visit**: `https://your-app.vercel.app`
2. **Try Vietnamese stock**: Enter "VNM"
3. **Try US stock**: Enter "AAPL"
4. Should work!

---

## 🎉 What You Get (100% Free)

### Your URLs:
- **Frontend**: `https://your-app.vercel.app` ← Share this!
- **Backend**: `https://yourusername.pythonanywhere.com` (hidden from users)

### Free Tier Limits:

| Service | Free Tier | Limits |
|---------|-----------|--------|
| **Vercel** | Forever | 100GB bandwidth/month |
| **PythonAnywhere** | Forever | 100 sec/day CPU, always-on |
| **Glitch** | Forever | 1000 hours/month, sleeps after 5min |
| **Replit** | Forever | Sleeps after inactivity |

---

## 💡 Best Free Combination

**Recommended Setup:**
- Frontend: **Vercel** (fast, reliable, no limits)
- Backend: **PythonAnywhere** (always-on, no sleep!)

**Why?**
- Both services are free forever
- PythonAnywhere doesn't sleep (unlike Render/Glitch)
- 100 seconds CPU/day is enough for moderate use
- Perfect for personal projects and sharing

---

## 🔄 Automatic Updates

### Update Backend:
1. Make changes to `backend_tradingview.py`
2. Upload to PythonAnywhere via **Files** tab
3. Click **Reload** on Web tab

### Update Frontend:
1. Make changes locally
2. Push to GitHub:
   ```bash
   git add .
   git commit -m "Update feature"
   git push origin main
   ```
3. Vercel auto-redeploys!

---

## 🔧 Troubleshooting

### Frontend can't connect to backend:
1. Check `config.js` has correct backend URL
2. Test backend directly: `https://yourusername.pythonanywhere.com/health`
3. Check browser console (F12) for CORS errors
4. Verify CORS is enabled in Flask (already done in your code)

### PythonAnywhere "CPU limit exceeded":
- Free tier has 100 sec/day CPU time
- Your app uses ~1-2 seconds per request
- Can handle ~50 requests/day
- Upgrade to paid ($5/month) for unlimited CPU

### Glitch app sleeping:
- First request after sleep takes ~5 seconds
- Use UptimeRobot (free) to ping it every 5 minutes
- Or upgrade to Glitch Pro ($8/month) for always-on

---

## 📤 Share Your App

Send this URL to anyone:

```
Check out my CAPM & Gordon Model Stock Calculator!
Analyze Vietnamese and US stocks:
https://your-app.vercel.app
```

They can:
- ✅ Use the calculator
- ✅ Share the link
- ✅ Analyze any stock

But they can't:
- ❌ See your code (if repo is private)
- ❌ Access your backend directly
- ❌ Copy your algorithms

---

## 🚀 Summary

### Total Cost: **$0/month**

### Your Setup:
1. **Frontend**: Vercel (free forever)
2. **Backend**: PythonAnywhere (free forever)
3. **Total deployment time**: 15-20 minutes

### What's Included:
- ✅ Public URL
- ✅ Automatic HTTPS
- ✅ Auto-deploy from GitHub (frontend)
- ✅ No sleep mode (PythonAnywhere)
- ✅ Private code (if repo is private)

**Perfect for**: Personal projects, sharing with friends, portfolio

---

## 📈 When to Upgrade

**Upgrade if:**
- You get >50 daily users (PythonAnywhere CPU limit)
- You want faster backend (Render Starter $7/month)
- You need analytics (Vercel Pro $20/month)

**But for now:** Free tier is perfect! 🎉

---

## Alternative Free Backends

If PythonAnywhere doesn't work for you:

1. **Koyeb**: https://www.koyeb.com/ (free tier, Docker support)
2. **Fly.io**: https://fly.io/ (free tier, global deployment)
3. **Cyclic**: https://www.cyclic.sh/ (free tier, Node.js/Python)
4. **Deta**: https://www.deta.sh/ (free tier, Python support)

All support Flask and have free tiers!

---

## Need Help?

- **PythonAnywhere Help**: https://help.pythonanywhere.com/
- **Vercel Docs**: https://vercel.com/docs
- **Glitch Support**: https://help.glitch.com/

Your app is ready to deploy for free! 🚀
