# Quick Deploy Guide - 5 Minutes Setup

Follow these exact steps to make your app public while keeping code private.

---

## Step 1: Make Repository Private (2 minutes)

1. Go to: https://github.com/Quan-CodeGit/CAPM-Gordon-valuation-model/settings
2. Scroll to bottom → **Danger Zone**
3. Click **Change visibility** → **Make private**
4. Type repository name to confirm
5. Click **I understand, make this repository private**

✅ **Done!** Code is now hidden from public.

---

## Step 2: Deploy Backend (3 minutes)

### On Render:

1. **Go to**: https://dashboard.render.com/
2. **Sign up** with GitHub (authorize access to private repos)
3. Click **New +** → **Web Service**
4. **Select repository**: `CAPM-Gordon-valuation-model`
5. **Fill in**:
   ```
   Name: capm-gordon-api
   Runtime: Python 3
   Build Command: pip install -r requirements_tradingview.txt
   Start Command: python backend_tradingview.py
   Plan: Free
   ```
6. Click **Create Web Service**
7. **Wait 3-5 minutes** for build to complete
8. **Copy your URL**: `https://capm-gordon-api.onrender.com` (or similar)

✅ **Test it**: Open `https://your-url.onrender.com/health` in browser
Should show: `{"status": "healthy", ...}`

---

## Step 3: Update Frontend URL (1 minute)

On your computer:

1. Open `index.html` in a text editor
2. Press **Ctrl+F** and search for: `http://localhost:5000`
3. Replace with your Render URL: `https://capm-gordon-api.onrender.com`
4. Save the file

Example:
```javascript
// Before:
const API_URL = 'http://localhost:5000';

// After:
const API_URL = 'https://capm-gordon-api.onrender.com';
```

---

## Step 4: Deploy Frontend (2 minutes)

### Option A: Netlify (Easiest)

1. **Go to**: https://app.netlify.com/
2. **Sign up** with GitHub
3. Click **Add new site** → **Import an existing project**
4. Choose **GitHub**
5. Select your **private** repository: `CAPM-Gordon-valuation-model`
6. Leave all settings default
7. Click **Deploy site**
8. **Get your URL**: `https://random-name.netlify.app`

**Optional - Change URL:**
- Go to **Site settings** → **Change site name**
- Change to: `capm-calculator` (if available)
- New URL: `https://capm-calculator.netlify.app`

✅ **Your app is live!** Share this URL with anyone.

### Option B: Vercel (Alternative)

1. **Go to**: https://vercel.com/
2. **Sign up** with GitHub
3. Click **Add New** → **Project**
4. Import your **private** repository
5. Click **Deploy**
6. **Get your URL**: `https://your-app.vercel.app`

✅ **Your app is live!**

---

## Step 5: Commit Changes (Push to GitHub)

So automatic updates work:

```bash
git add index.html PRIVATE_DEPLOYMENT.md QUICK_DEPLOY.md
git commit -m "Update for production deployment"
git push origin main
```

Now whenever you push to GitHub:
- Render backend auto-updates
- Netlify/Vercel frontend auto-updates

---

## 🎉 You're Done!

### Your App:
- **Public URL**: `https://your-app.netlify.app` ← Share this
- **Backend API**: `https://capm-gordon-api.onrender.com` ← Private
- **Source Code**: Private on GitHub ← Hidden

### What Users Can Do:
✅ Use your calculator
✅ Share the link
✅ Analyze stocks

### What Users CAN'T Do:
❌ See your code
❌ Copy your algorithms
❌ Fork your repository
❌ Download source files

---

## Share Your App

Send this to anyone:
```
Check out my CAPM & Gordon Model Stock Calculator!
Analyze Vietnamese and US stocks:
https://your-app.netlify.app
```

---

## Free Tier Limits

- **Render**: 750 hours/month (enough for most users)
- **Netlify**: 100GB bandwidth/month (very generous)
- **Cost**: $0/month

**Note**: Render free tier "sleeps" after 15 min inactivity. First request after sleep takes 30-60 seconds. To eliminate this, upgrade to Render Starter ($7/month).

---

## If Something Goes Wrong

### Backend not working:
1. Check Render logs: Dashboard → Logs
2. Test health endpoint: `https://your-url.onrender.com/health`
3. Verify build command in Render settings

### Frontend not connecting:
1. Check browser console (F12)
2. Verify API_URL in index.html matches Render URL
3. Check CORS is enabled in backend (already done)

### Need help?
Check the detailed guide: `PRIVATE_DEPLOYMENT.md`

---

## Next Steps

1. ✅ Make repo private
2. ✅ Deploy on Render + Netlify
3. ✅ Share public URL
4. Consider upgrading to Render Starter ($7) for better performance
5. Add custom domain (optional, see PRIVATE_DEPLOYMENT.md)

**Total time**: 8-10 minutes
**Cost**: $0/month
**Result**: Public app, private code! 🎉
