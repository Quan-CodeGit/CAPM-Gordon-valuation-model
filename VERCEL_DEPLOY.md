# Vercel Deployment Guide - 3 Minutes Setup

Deploy your CAPM Calculator on Vercel with both frontend and backend in one URL!

---

## Method 1: Deploy via Vercel Dashboard (Easiest)

### Step 1: Make Repository Private (Optional but Recommended)

1. Go to: https://github.com/Quan-CodeGit/CAPM-Gordon-valuation-model/settings
2. Scroll to **Danger Zone** → **Change visibility** → **Make private**
3. Confirm

### Step 2: Deploy on Vercel

1. **Go to**: https://vercel.com/dashboard
2. Click **Add New** → **Project**
3. **Import Git Repository**:
   - Click **Import** next to your repository: `CAPM-Gordon-valuation-model`
   - (If you made it private, you may need to adjust GitHub permissions)
4. **Configure Project**:
   - **Framework Preset**: Other (don't select anything)
   - Leave all settings as default
5. Click **Deploy**

### Step 3: Wait for Deployment (2-3 minutes)

Vercel will:
- Install Python dependencies
- Build and deploy your backend
- Serve your frontend
- Generate your URL

### Step 4: Get Your URL

Once deployed, you'll see:
```
🎉 Your project is live at:
https://capm-gordon-valuation-model.vercel.app
```

**That's it!** Share this URL with anyone. They can use your calculator but can't see your code (if repo is private).

---

## Method 2: Deploy via Vercel CLI (Faster)

If you have Vercel CLI installed:

### In your project directory:

```bash
# Login to Vercel (if not already)
vercel login

# Deploy
vercel

# Follow prompts:
# - Set up and deploy? Yes
# - Which scope? Your account
# - Link to existing project? No
# - Project name: capm-gordon-calculator (or press Enter)
# - Directory: ./ (press Enter)
# - Override settings? No

# Deploy to production
vercel --prod
```

**Get your URL**:
```
https://capm-gordon-calculator.vercel.app
```

---

## ✅ What You Get

### Single URL for Everything:
- **Frontend**: `https://your-app.vercel.app/`
- **Backend API**: `https://your-app.vercel.app/api/valuation/AAPL`
- **Health Check**: `https://your-app.vercel.app/api/health`

### Automatic HTTPS ✅
### Custom Domain Support ✅
### Automatic Deployments ✅

---

## 🔄 Automatic Updates

Every time you push to GitHub:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

→ Vercel automatically detects the push
→ Rebuilds and redeploys (1-2 minutes)
→ Your app updates automatically!

---

## 🎯 Test Your Deployment

1. **Visit your URL**: `https://your-app.vercel.app`
2. **Try the calculator**:
   - Select Vietnam market
   - Enter "VNM"
   - Click "Calculate Valuation"
3. **Should work!** If not, check logs in Vercel dashboard.

---

## 📊 Vercel Dashboard

Access at: https://vercel.com/dashboard

You can:
- ✅ View deployment logs
- ✅ Monitor performance
- ✅ See analytics
- ✅ Configure custom domains
- ✅ Manage environment variables

---

## 🔧 Troubleshooting

### Build Failed
- Check Vercel build logs
- Verify `requirements_tradingview.txt` has all dependencies
- Check `vercel.json` configuration

### Backend Not Working
- Test API directly: `https://your-app.vercel.app/api/health`
- Check Vercel function logs
- Verify Python dependencies installed

### Frontend Can't Connect
- Check browser console (F12)
- API should use relative paths (already configured in index.html)
- Verify CORS is enabled

### Cold Starts
- First request may take 5-10 seconds
- Subsequent requests are fast
- Upgrade to Pro for better performance

---

## 💰 Cost

**Vercel Free Tier**:
- ✅ 100 GB bandwidth/month
- ✅ Unlimited deployments
- ✅ Automatic HTTPS
- ✅ Serverless functions included
- ✅ **Cost: $0/month**

**Vercel Pro** ($20/month):
- Faster cold starts
- More bandwidth
- Better analytics
- Custom domain support
- Priority support

---

## 🌐 Custom Domain (Optional)

### Add Your Domain:

1. Go to your project in Vercel dashboard
2. Click **Settings** → **Domains**
3. Add your domain (e.g., `mycalculator.com`)
4. Update DNS records as shown
5. Wait 5-10 minutes for SSL certificate

**Result**: `https://mycalculator.com` with automatic HTTPS!

---

## 🔒 Keep Code Private

If you made your GitHub repo private:
- ✅ Users can access: `https://your-app.vercel.app`
- ❌ Users can't see: Your source code on GitHub
- ❌ Users can't copy: Your algorithms and logic

**Perfect!** Public app, private code.

---

## 📝 Files Configured

- ✅ `vercel.json` - Vercel configuration
- ✅ `index.html` - Updated to use relative API paths
- ✅ `requirements_tradingview.txt` - Python dependencies

---

## 🚀 Next Steps

1. ✅ Deploy on Vercel (follow steps above)
2. ✅ Get your public URL
3. ✅ Share with users
4. (Optional) Make repo private
5. (Optional) Add custom domain

**Total time**: 3-5 minutes
**Cost**: $0/month
**Result**: Public app URL ready to share! 🎉

---

## 📞 Need Help?

- **Vercel Docs**: https://vercel.com/docs
- **Vercel Support**: https://vercel.com/support
- **Check logs**: Vercel Dashboard → Your Project → Logs

---

## Alternative: Separate Backend & Frontend

If you prefer separate deployments:

**Backend**: Deploy on Render (see `QUICK_DEPLOY.md`)
**Frontend**: Deploy on Vercel or Netlify

This can be more reliable for heavy backend processing.
