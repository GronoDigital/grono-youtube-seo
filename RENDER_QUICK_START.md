# ⚡ Render Quick Start Guide

## 🚀 Deploy in 5 Minutes

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Verify email

### Step 3: Create Web Service
1. Click "New +" → "Web Service"
2. Connect: `GronoDigital/grono-youtube-seo`
3. Configure:
   - **Name**: `grono-youtube-seo`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### Step 4: Set Environment Variables
Click "Advanced" → Add these:

| Variable | Value |
|----------|-------|
| `YOUTUBE_API_KEY` | `AIzaSyAONIZtF-KpxJrTvXm3dtMWh2gRFllWEfs` |
| `SECRET_KEY` | Generate: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `FLASK_ENV` | `production` |

### Step 5: Deploy
1. Click "Create Web Service"
2. Wait 5-10 minutes
3. Visit your URL: `https://grono-youtube-seo.onrender.com`

### Step 6: First Login
- Username: `admin`
- Password: `admin123`
- **Change password immediately!**

---

## ✅ What's Already Configured

- ✅ API key uses environment variable
- ✅ Gunicorn configured for production
- ✅ Database auto-creates on first run
- ✅ All sensitive files in .gitignore
- ✅ Production-ready code

---

## 📝 Notes

- **Free Tier**: Service sleeps after 15 min (database resets)
- **Starter Plan ($7/month)**: Always-on, persistent database
- **Database**: Created automatically, no setup needed

---

**That's it! Your app is live! 🎉**

