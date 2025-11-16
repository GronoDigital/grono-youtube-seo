# 🚀 Deployment Guide - YouTube SEO Service Manager

This guide will help you deploy your application to the cloud so your team can access it from anywhere.

## 📋 Prerequisites

1. GitHub account (free)
2. Render.com or Railway.app account (both have free tiers)

---

## 🌐 Option 1: Deploy to Render.com (Recommended - Easiest)

### Step 1: Push Code to GitHub

1. Create a new repository on GitHub
2. In your project folder, run:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin YOUR_GITHUB_REPO_URL
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign up (free)
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `youtube-seo-manager` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Plan**: Free (or paid if you need more resources)

5. **Environment Variables** (click "Advanced"):
   - `SECRET_KEY`: Generate a random string (use: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `PORT`: Leave empty (Render sets this automatically)
   - `FLASK_ENV`: `production`

6. Click "Create Web Service"
7. Wait 5-10 minutes for deployment
8. Your app will be live at: `https://youtube-seo-manager.onrender.com` (or your custom name)

### Step 3: Access Your App

1. Visit your Render URL
2. Login with default credentials:
   - Username: `admin`
   - Password: `admin123`
3. **IMPORTANT**: Go to Users page and change admin password immediately!

---

## 🚂 Option 2: Deploy to Railway.app

### Step 1: Push Code to GitHub (same as above)

### Step 2: Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign up (free)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect Python and deploy
5. Click on your service → "Variables" tab
6. Add environment variables:
   - `SECRET_KEY`: Generate random string
   - `PORT`: Leave empty (Railway sets this)
   - `FLASK_ENV`: `production`

7. Click "Settings" → "Generate Domain" to get your URL
8. Your app will be live at: `https://your-app-name.up.railway.app`

---

## 🔐 Security Setup

### Change Default Admin Password

1. Login with default credentials
2. Click "👥 Manage Users" (admin only)
3. You can't change password from UI yet, but you can:
   - Create a new admin user
   - Delete the old admin user
   - Or use SQLite to update password (advanced)

### Set Strong Secret Key

Generate a strong secret key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Add it as `SECRET_KEY` environment variable in your hosting platform.

---

## 👥 Adding Team Members

1. Login as admin
2. Click "👥 Manage Users"
3. Click "Add User"
4. Fill in:
   - Username
   - Email
   - Password
   - Role: "User" (or "Admin" if you want them to manage users)
5. Share the URL and credentials with your team

---

## 📊 Database Persistence

**Important**: The database (`youtube_channels.db`) is stored on the server. 

- **Render Free Tier**: Database persists, but service sleeps after 15 minutes of inactivity
- **Railway Free Tier**: Database persists, but service may sleep after inactivity

**For Production**: Consider using a managed database:
- Render PostgreSQL (paid)
- Railway PostgreSQL (paid)
- Or use SQLite with persistent storage (current setup works for small teams)

---

## 🔄 Updating Your App

1. Make changes to your code
2. Commit and push to GitHub:
```bash
git add .
git commit -m "Your changes"
git push
```
3. Render/Railway will automatically redeploy (takes 2-5 minutes)

---

## 🐛 Troubleshooting

### App won't start
- Check logs in Render/Railway dashboard
- Verify all environment variables are set
- Make sure `requirements.txt` has all dependencies

### Can't login
- Make sure database was initialized
- Check if default admin user exists
- Try resetting by redeploying

### Database issues
- Database file is created automatically on first run
- If you need to reset, delete the service and redeploy

### Port issues
- Make sure `PORT` environment variable is not set (let platform set it)
- Or set it to the port your platform provides

---

## 💰 Cost Estimate

### Free Tier (Good for small teams):
- **Render**: Free tier available (750 hours/month)
- **Railway**: $5 free credit/month
- **Both**: Perfect for 2-10 team members

### Paid Tier (If you grow):
- **Render**: $7/month for always-on service
- **Railway**: Pay-as-you-go (usually $5-20/month)

---

## ✅ Post-Deployment Checklist

- [ ] App is accessible via URL
- [ ] Can login with default admin credentials
- [ ] Changed admin password
- [ ] Added team members
- [ ] Tested fetching channels
- [ ] Tested marking channels as emailed
- [ ] Shared URL and credentials with team

---

## 🆘 Need Help?

If you encounter issues:
1. Check the logs in your hosting platform dashboard
2. Verify all environment variables are set
3. Make sure your GitHub repo is connected
4. Try redeploying the service

---

## 🎉 You're Done!

Your YouTube SEO Service Manager is now live and accessible to your team from anywhere in the world!

**Next Steps**:
1. Share the URL with your team
2. Have them login with their credentials
3. Start managing channels together!

