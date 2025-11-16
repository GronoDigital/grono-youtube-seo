# 🚀 Render Deployment Guide - GRONO YouTube SEO Service

Complete step-by-step guide to deploy your GRONO YouTube SEO Service Manager on Render.com.

## 📋 Prerequisites

1. ✅ Code pushed to GitHub: `https://github.com/GronoDigital/grono-youtube-seo`
2. ✅ Render.com account (free tier available)
3. ✅ YouTube Data API v3 key

---

## 🎯 Step-by-Step Deployment

### Step 1: Sign Up for Render

1. Go to [render.com](https://render.com)
2. Click "Get Started for Free"
3. Sign up with GitHub (recommended) or email
4. Verify your email address

### Step 2: Connect GitHub Repository

1. In Render dashboard, click "New +" → "Web Service"
2. Under "Public Git repository", click "Connect account" (if not connected)
3. Authorize Render to access your GitHub account
4. Select repository: `GronoDigital/grono-youtube-seo`
5. Click "Connect"

### Step 3: Configure Web Service

Fill in the following settings:

**Basic Settings:**
- **Name**: `grono-youtube-seo` (or any name you prefer)
- **Region**: Choose closest to you (e.g., `Oregon (US West)`)
- **Branch**: `main`
- **Root Directory**: (leave empty)

**Build & Deploy:**
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

**Plan:**
- **Free**: For testing (service sleeps after 15 min inactivity)
- **Starter ($7/month)**: Always-on, better for production

### Step 4: Set Environment Variables

Click "Advanced" → Scroll to "Environment Variables" → Click "Add Environment Variable"

Add these variables:

1. **YOUTUBE_API_KEY**
   - Value: `AIzaSyAONIZtF-KpxJrTvXm3dtMWh2gRFllWEfs`
   - Description: YouTube Data API v3 key

2. **SECRET_KEY**
   - Generate one: Run `python -c "import secrets; print(secrets.token_hex(32))"` locally
   - Or use: `grono-secret-key-2024-$(openssl rand -hex 16)`
   - Description: Flask session secret key

3. **FLASK_ENV**
   - Value: `production`
   - Description: Flask environment

4. **PORT**
   - Leave empty (Render sets this automatically)

### Step 5: Deploy

1. Review all settings
2. Click "Create Web Service"
3. Wait 5-10 minutes for first deployment
4. Watch the build logs in real-time

### Step 6: Access Your App

After successful deployment:
- Your app will be live at: `https://grono-youtube-seo.onrender.com` (or your custom name)
- First visit may take 30 seconds if service was sleeping (free tier)

---

## 🔐 First Login

1. Visit your Render URL
2. Click "Team Login" or go to `/login`
3. Default admin credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
4. **⚠️ IMPORTANT**: Change the admin password immediately after first login!

---

## 📊 Database

- ✅ Database (`youtube_channels.db`) is created automatically on first run
- ⚠️ **Free Tier Limitation**: Database resets when service sleeps (after 15 min inactivity)
- 💡 **Solution**: Upgrade to Starter plan ($7/month) for persistent database

---

## 🔧 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `YOUTUBE_API_KEY` | ✅ Yes | YouTube Data API v3 key | `AIzaSy...` |
| `SECRET_KEY` | ✅ Yes | Flask session secret | `grono-secret-...` |
| `FLASK_ENV` | ✅ Yes | Environment mode | `production` |
| `PORT` | ❌ No | Server port (auto-set by Render) | - |

---

## 🐛 Troubleshooting

### Build Fails

**Error**: `ModuleNotFoundError: No module named 'gunicorn'`
- **Fix**: Make sure `gunicorn>=21.2.0` is in `requirements.txt`

**Error**: `ImportError: cannot import name 'build'`
- **Fix**: Check that `google-api-python-client` is in `requirements.txt`

### App Crashes on Start

**Error**: `Database locked` or `sqlite3.OperationalError`
- **Fix**: This is normal on free tier. Database resets on sleep. Upgrade to Starter plan.

**Error**: `API quota exceeded`
- **Fix**: Check your YouTube API quota. Wait 24 hours or request quota increase.

### Service Won't Start

**Error**: `Port already in use`
- **Fix**: Make sure Start Command uses `$PORT` variable: `gunicorn app:app --bind 0.0.0.0:$PORT`

### Can't Login

**Error**: `Invalid username or password`
- **Fix**: Database may have reset. Default credentials are `admin` / `admin123`

---

## 🔄 Updating Your App

1. Make changes to your code
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Your update message"
   git push origin main
   ```
3. Render automatically detects the push and redeploys
4. Wait 2-5 minutes for new deployment

---

## 📈 Monitoring

### View Logs
1. Go to your service in Render dashboard
2. Click "Logs" tab
3. View real-time logs

### Check Service Status
- Green dot = Running
- Yellow dot = Deploying
- Red dot = Error

---

## 💰 Pricing

### Free Tier
- ✅ Free forever
- ⚠️ Service sleeps after 15 min inactivity
- ⚠️ Database resets on sleep
- ✅ 750 hours/month

### Starter Plan ($7/month)
- ✅ Always-on service
- ✅ Persistent database
- ✅ Better performance
- ✅ No cold starts

**Recommendation**: Start with Free tier for testing, upgrade to Starter for production.

---

## 🔒 Security Checklist

- [x] Changed default admin password
- [x] SECRET_KEY is set (strong random value)
- [x] YOUTUBE_API_KEY is in environment variables (not in code)
- [x] Sensitive files are in `.gitignore`
- [ ] HTTPS is enabled (automatic on Render)
- [ ] Regular backups (if using Starter plan)

---

## 📞 Support

- Render Docs: https://render.com/docs
- Render Status: https://status.render.com
- Render Community: https://community.render.com

---

## ✅ Deployment Checklist

- [ ] Code pushed to GitHub
- [ ] Render account created
- [ ] Repository connected
- [ ] Environment variables set
- [ ] Service deployed successfully
- [ ] App accessible via URL
- [ ] Can login with admin credentials
- [ ] Changed admin password
- [ ] Tested channel analyzer
- [ ] Tested dashboard features

---

**🎉 Congratulations! Your GRONO YouTube SEO Service is now live on Render!**

