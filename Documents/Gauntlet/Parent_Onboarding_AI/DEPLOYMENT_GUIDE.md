# 🚀 VERCEL DEPLOYMENT GUIDE

**Office Hours Matching Tool - Step-by-Step Deployment**

---

## ✅ PRE-DEPLOYMENT CHECKLIST

- [ ] GitHub account (free at github.com)
- [ ] Vercel account (free at vercel.com)
- [ ] Airtable API key and Base ID
- [ ] AWS credentials for SES
- [ ] OpenAI API key
- [ ] Node.js 18+ installed locally

---

## 📋 STEP 1: PUSH CODE TO GITHUB (5 minutes)

### 1A. Create GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Repository name: `office-hours-matching`
3. Description: "AI-powered mentor-mentee matching platform"
4. Set to **Public** (so Vercel can access it)
5. Click **Create repository**

### 1B. Push Code from Local

Copy and run these commands in your terminal:

```bash
# Navigate to project directory
cd /Users/akhilp/Documents/Gauntlet/Parent_Onboarding_AI

# Add GitHub as remote
git remote add origin https://github.com/YOUR_USERNAME/office-hours-matching.git

# Rename branch to main (if needed)
git branch -M main

# Push code to GitHub
git push -u origin main
```

**Expected output:**
```
Enumerating objects: 42, done.
Counting objects: 100% (42/42), done.
...
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

✅ **Code is now on GitHub!**

---

## 🔗 STEP 2: CONNECT TO VERCEL (2 minutes)

### 2A. Create Vercel Account

1. Go to [vercel.com](https://vercel.com)
2. Click **Sign Up**
3. Choose **Sign up with GitHub**
4. Authorize Vercel to access your GitHub account
5. Complete registration

### 2B. Import Project to Vercel

1. After signing in, click **Add New...** → **Project**
2. Select **Import Git Repository**
3. Paste: `https://github.com/YOUR_USERNAME/office-hours-matching`
4. Click **Continue**

### 2C. Configure Project Settings

**Framework Preset:** Next.js ✓ (auto-detected)

**Build Settings:**
- Build Command: `npm run build` ✓
- Output Directory: `.next` ✓
- Install Command: `npm install` ✓

**Root Directory:** Leave blank (or `.`)

Click **Continue**

---

## 🔐 STEP 3: ADD ENVIRONMENT VARIABLES (5 minutes)

In the Vercel dashboard, go to **Settings** → **Environment Variables**

Add these variables for **Production**:

### Authentication
```
NEXTAUTH_URL = https://YOUR_DOMAIN.vercel.app
NEXTAUTH_SECRET = (generate with: openssl rand -base64 32)
```

### Airtable
```
AIRTABLE_API_KEY = YOUR_AIRTABLE_KEY
AIRTABLE_BASE_ID = YOUR_BASE_ID
```

### AWS SES
```
AWS_REGION = us-east-1
AWS_ACCESS_KEY_ID = YOUR_AWS_KEY
AWS_SECRET_ACCESS_KEY = YOUR_AWS_SECRET
AWS_SES_FROM_EMAIL = noreply@yourdomain.com
```

### OpenAI
```
OPENAI_API_KEY = YOUR_OPENAI_KEY
```

### Application
```
NEXT_PUBLIC_API_URL = https://YOUR_DOMAIN.vercel.app
NODE_ENV = production
```

**To generate NEXTAUTH_SECRET:**
```bash
# Run in terminal
openssl rand -base64 32

# Output example:
# rN7x+K9mL2pQ4vW5jX8yZ1aB2cD3eF4gH5iJ6kL7m
```

Click **Save** for each variable.

---

## 🚀 STEP 4: DEPLOY (Click & Wait)

1. Back on the main project page, click **Deploy**
2. Wait for build to complete (2-3 minutes)
3. You'll see:
   ```
   ✓ Build completed
   ✓ Deployment successful
   ```

4. Your URL will be: `https://office-hours-matching.vercel.app`

✅ **Your app is now live on Vercel!**

---

## 🧪 STEP 5: VERIFY DEPLOYMENT (5 minutes)

### 5A. Check Website Status

```bash
# Test your deployed app
curl https://office-hours-matching.vercel.app

# Expected: HTML response (home page)
```

### 5B. Test Authentication

1. Open your Vercel URL in browser
2. Click **Sign In**
3. Use test credentials:
   - Email: `founder@example.com`
   - Password: `password`
4. Should redirect to `/dashboard`

✅ **Authentication working!**

### 5C. Test API Endpoints

```bash
# Test mentors endpoint
curl -X GET https://office-hours-matching.vercel.app/api/mentors \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test matching endpoint
curl -X POST https://office-hours-matching.vercel.app/api/match \
  -H "Content-Type: application/json" \
  -d '{"founderId": "test-founder-123"}'
```

✅ **APIs are accessible!**

---

## 📊 STEP 6: SET UP PRODUCTION DATABASE (10 minutes)

### 6A. Create PostgreSQL Instance

Choose one of these options:

**Option 1: Supabase (Recommended - Free tier)**
```bash
# 1. Go to supabase.com
# 2. Create project
# 3. Get connection string
# 4. Add to Vercel: DATABASE_URL
```

**Option 2: AWS RDS**
```bash
aws rds create-db-instance \
  --db-instance-identifier office-hours-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --master-username postgres \
  --master-user-password YOUR_SECURE_PASSWORD \
  --allocated-storage 20 \
  --publicly-accessible true
```

**Option 3: Railway (Simple - Free tier)**
```
# Go to railway.app
# Create PostgreSQL project
# Copy connection string
# Add to Vercel environment
```

### 6B. Add DATABASE_URL to Vercel

1. In Vercel dashboard, go to **Settings** → **Environment Variables**
2. Add:
   ```
   DATABASE_URL = postgresql://user:password@host:5432/office_hours
   ```
3. Save and redeploy

---

## 🔍 STEP 7: MONITOR & MAINTAIN

### View Logs
```
Vercel Dashboard → Deployments → Logs
```

### Set Up Monitoring
1. Vercel Dashboard → **Settings** → **Monitoring**
2. Enable:
   - [ ] Web Analytics
   - [ ] Performance Monitoring
   - [ ] Error Tracking

### Check Build Status
```bash
# View recent deployments
# Vercel Dashboard → Deployments tab
```

---

## 📝 TROUBLESHOOTING

### Build Fails with "Module not found"
```bash
# Solution: Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
git add -A && git commit -m "Update deps"
git push origin main
```

### Environment Variables Not Loading
```
Solution:
1. Go to Vercel Dashboard
2. Settings → Environment Variables
3. Redeploy (Deployments → Redeploy)
```

### API Returns 401 Unauthorized
```
Solution:
1. Check NEXTAUTH_SECRET is set
2. Verify NEXTAUTH_URL matches deployment URL
3. Redeploy
```

### Email Not Sending
```
Solution:
1. Verify AWS SES credentials
2. Check SES is in Production mode (not Sandbox)
3. Verify AWS_SES_FROM_EMAIL is verified in SES
4. Check logs in Vercel
```

### Database Connection Fails
```
Solution:
1. Test connection string locally:
   psql $DATABASE_URL
2. Verify DATABASE_URL in Vercel matches
3. Check database is publicly accessible
4. Whitelist Vercel IPs in database firewall
```

---

## ✨ CUSTOM DOMAIN (Optional)

### Connect Custom Domain

1. Vercel Dashboard → **Settings** → **Domains**
2. Add your domain (e.g., `mentoring.capitalfactory.com`)
3. Follow DNS configuration instructions
4. Wait for SSL certificate (2-24 hours)

---

## 📈 PRODUCTION CHECKLIST

- [ ] Site is live and accessible
- [ ] Authentication works (test all 3 roles)
- [ ] Email notifications sending
- [ ] Airtable integration working
- [ ] Database connected and populated
- [ ] Admin dashboard showing data
- [ ] Monitoring configured
- [ ] Error tracking enabled
- [ ] Custom domain configured (optional)
- [ ] SSL certificate valid
- [ ] Analytics enabled
- [ ] Backup strategy in place

---

## 🎯 NEXT STEPS

1. **Populate Data**
   - Create mentor profiles in Airtable
   - Create founder test accounts
   - Schedule some test sessions

2. **User Testing**
   - Invite mentors to test
   - Invite founders to test booking
   - Collect feedback

3. **Optimization**
   - Monitor performance
   - Analyze user behavior
   - Optimize slow pages

4. **Scale**
   - Add more mentors
   - Promote to broader user group
   - Iterate based on feedback

---

## 🆘 GETTING HELP

**Vercel Support:**
- [Vercel Docs](https://vercel.com/docs)
- [Vercel Community](https://vercel.com/community)
- Email: support@vercel.com

**Next.js Support:**
- [Next.js Docs](https://nextjs.org/docs)
- [Next.js Discord](https://discord.gg/bUG2bvbtHc)

**Your Code:**
- See IMPLEMENTATION_COMPLETE.md for feature details
- See README.md for setup information
- Check git history for implementation details

---

## ✅ DEPLOYMENT SUMMARY

**Status:** Ready to deploy
**Estimated Time:** 20-30 minutes
**Cost:** Free tier (upgradeable)
**Uptime SLA:** 99.95%
**Support:** 24/7

---

**Happy deploying! 🚀**

*Your Office Hours Matching Tool will be live shortly.*
