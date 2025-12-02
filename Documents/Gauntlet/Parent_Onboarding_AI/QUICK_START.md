# ⚡ QUICK START - DEPLOYMENT IN 20 MINUTES

## 🎯 TLDR - Deploy Now

### Copy & Paste These Commands

#### Step 1: Push to GitHub
```bash
cd /Users/akhilp/Documents/Gauntlet/Parent_Onboarding_AI

git remote add origin https://github.com/YOUR_USERNAME/office-hours-matching.git
git branch -M main
git push -u origin main
```

#### Step 2: Deploy to Vercel
```bash
# Install Vercel CLI
npm i -g vercel

# Login
vercel login

# Deploy
vercel deploy --prod
```

#### Step 3: Set Environment Variables
```bash
# In Vercel Dashboard → Settings → Environment Variables
# Add all variables from DEPLOYMENT_GUIDE.md (Step 3)
```

#### Step 4: Redeploy with Environment Variables
```bash
vercel deploy --prod --force
```

---

## 📋 REQUIRED ENVIRONMENT VARIABLES

```bash
# Copy this and add to Vercel

NEXTAUTH_URL=https://YOUR_DOMAIN.vercel.app
NEXTAUTH_SECRET=rN7x+K9mL2pQ4vW5jX8yZ1aB2cD3eF4gH5iJ6kL7m
AIRTABLE_API_KEY=YOUR_API_KEY
AIRTABLE_BASE_ID=YOUR_BASE_ID
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=YOUR_KEY
AWS_SECRET_ACCESS_KEY=YOUR_SECRET
AWS_SES_FROM_EMAIL=noreply@yourdomain.com
OPENAI_API_KEY=YOUR_KEY
NEXT_PUBLIC_API_URL=https://YOUR_DOMAIN.vercel.app
NODE_ENV=production
```

---

## ✅ VERIFY DEPLOYMENT

```bash
# 1. Test homepage
curl https://YOUR_DOMAIN.vercel.app

# 2. Test login
# Visit: https://YOUR_DOMAIN.vercel.app/auth/signin
# Email: founder@example.com
# Password: password

# 3. Test API
curl https://YOUR_DOMAIN.vercel.app/api/mentors
```

---

## 🆘 COMMON ISSUES

| Issue | Solution |
|-------|----------|
| **Build fails** | `vercel deploy --prod --force` |
| **Env vars not working** | Redeploy with `--force` |
| **404 on routes** | Check Next.js build in Vercel logs |
| **Email not sending** | Verify AWS SES credentials & sandbox mode |
| **Can't login** | Check NEXTAUTH_SECRET is set |

---

## 📊 WHAT'S DEPLOYED

✅ Full Next.js application
✅ All API routes
✅ Authentication system
✅ Matching engine
✅ Admin dashboard
✅ Static assets
✅ Serverless functions

---

## 🚀 YOU'RE DONE!

Your app is now live at: **https://YOUR_DOMAIN.vercel.app**

Next:
1. Add data to Airtable
2. Invite users to test
3. Monitor in Vercel dashboard
4. Iterate based on feedback

---

**For detailed guide, see: DEPLOYMENT_GUIDE.md**
