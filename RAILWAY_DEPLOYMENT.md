# Railway Deployment Guide

## Deploy Mutual Fund Chatbot to Railway

### Prerequisites
- Railway account (https://railway.app/)
- GitHub repository with the code
- Google Gemini API key

### Steps

1. **Connect Repository to Railway**
   - Go to https://railway.app/
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `MF-FAQs` repository
   - Railway will automatically detect the Python application

2. **Configure Environment Variables**
   - Go to your project settings → "Variables"
   - Add the following environment variables:
     ```
     GEMINI_API_KEY=AIzaSyDMkOAFz8VtY00I9B57qdFzPujqmh8qBR0
     FLASK_ENV=production
     PORT=5000
     ```
   - Optional: Add `OPENAI_API_KEY` if you want OpenAI fallback

3. **Deployment Settings**
   - Railway will automatically use the `Procfile` to start the application
   - The `pyproject.toml` defines dependencies and build configuration
   - Port will be automatically assigned by Railway (overrides PORT=5000)

4. **Deploy**
   - Click "Deploy" button
   - Railway will build and deploy your application
   - Once deployed, you'll get a public URL

### Features After Deployment
- **Google Gemini Integration**: Primary LLM for intelligent responses
- **Fallback System**: OpenAI → Template-based answers
- **Web Interface**: Full chatbot functionality
- **API Endpoints**: `/api/chat`, `/api/health`, `/api/last-refreshed`
- **CORS Enabled**: Frontend can communicate with backend

### Environment Variables Explained
- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `OPENAI_API_KEY`: OpenAI API key (optional fallback)
- `FLASK_ENV`: Set to 'production' for Railway
- `PORT`: Railway will override this with assigned port

### Monitoring
- Check Railway logs for any issues
- Monitor API usage in your Gemini dashboard
- Test the deployed application using the provided URL

### Troubleshooting
- If deployment fails, check the build logs
- Ensure all dependencies are in `pyproject.toml`
- Verify environment variables are correctly set
- Check that `Procfile` points to the correct entry point
