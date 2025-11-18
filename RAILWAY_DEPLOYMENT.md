# Railway Deployment Guide

## Deploy Backend to Railway

1. **Go to Railway**: https://railway.app

2. **Login** with your GitHub account

3. **Deploy from GitHub**:
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `Tarushikha93/MF-FAQs` repository
   - Click "Deploy Now"

4. **Wait for deployment** (takes 2-3 minutes)

5. **Get your Railway URL**:
   - Once deployed, Railway will give you a URL like:
     `https://your-app-name.railway.app`
   - Copy this URL

6. **Update the frontend API URL**:
   - Edit `static/script.js`
   - Replace the placeholder URL with your actual Railway URL
   - Example: `https://mf-faqs-backend-production.up.railway.app/api/chat`

7. **Commit and push the updated script.js**:
   ```bash
   git add static/script.js
   git commit -m "Update API URL for production"
   git push
   ```

8. **Test your Vercel frontend**:
   - Go to https://mf-fa-qs.vercel.app/
   - Test with "Expense ratio ?"
   - Should now work correctly!

## Notes:
- Railway automatically uses the `Procfile` to run `python3 app.py`
- The app is configured to use Railway's dynamic PORT
- Railway will install dependencies from `requirements.txt`
- The health check path is `/api/chat`
