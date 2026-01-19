# How to Run the Calculator

## 🚀 Local Development (Your Computer)

### One-Click Start (Easiest!)

**Just double-click:** `START_APP.bat`

That's it! The app will:
1. ✅ Start the backend server
2. ✅ Start the frontend server
3. ✅ Open your browser automatically
4. ✅ Ready to use!

**To stop:** Close the batch file window or press any key

---

## 🌐 Render Deployment (Share with Others)

Your app is deployed at: `https://capm-gordon-calculator.onrender.com`

**Note:** First visit after 15 minutes takes 30-60 seconds to wake up (free tier limitation)

---

## 📁 Project Files

- `START_APP.bat` - One-click launcher for local use
- `backend_tradingview.py` - Flask API server
- `index.html` - Calculator interface
- `config.js` - Configuration file

---

## 🔧 Troubleshooting

### "Cannot connect to backend"
1. Make sure you're using `START_APP.bat`
2. Don't close the batch file window
3. Wait 3-5 seconds for servers to start

### Port already in use
1. Close any Python processes
2. Run `START_APP.bat` again (it will clean up automatically)

### Render not working
1. Check https://dashboard.render.com for build status
2. Wait for rebuild to complete (2-5 minutes)
3. First request after sleep takes 30-60 seconds

---

## 💡 Tips

- **Local:** Use `START_APP.bat` - opens at `http://localhost:8000`
- **Share:** Send people the Render URL
- **Deploy:** Push to GitHub and Render rebuilds automatically

---

## 📚 Deployment Guides

- `FREE_DEPLOY.md` - 100% free deployment options
- `QUICK_DEPLOY.md` - Quick Render deployment
- `PRIVATE_DEPLOYMENT.md` - Detailed deployment guide
- `DEPLOYMENT_OPTIONS.md` - Compare all options

---

**Need help?** Check the deployment guides or open an issue on GitHub!
