# MediRemind Render Deployment Guide

This guide provides step-by-step instructions for deploying the MediRemind system (Django backend + React frontend) to Render.

## Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **Environment Variables**: Prepare your production environment variables

## Deployment Options

You have two deployment options:

### Option 1: Automated Deployment (Recommended)
Use the `render.yaml` file for automated service creation.

### Option 2: Manual Deployment
Create services manually through the Render dashboard.

## Option 1: Automated Deployment with render.yaml

### Step 1: Prepare Your Repository

1. Ensure your code is pushed to GitHub
2. The `render.yaml` file is already configured in your repository root

### Step 2: Create Services on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Select the repository containing your MediRemind code
5. Render will automatically detect the `render.yaml` file

### Step 3: Configure Environment Variables

The following environment variables will be automatically set:
- `DATABASE_URL` (from PostgreSQL service)
- `DJANGO_SECRET_KEY` (auto-generated)
- `DEBUG=false`
- `ENVIRONMENT=production`

You need to manually add these in the Render dashboard:

#### Backend Service Environment Variables:
```
REDIS_URL=redis://default:oE1Gh8TkVwGkuihbKt43XrQeZVTLbl4p@redis-12735.crce204.eu-west-2-3.ec2.redns.redis-cloud.com:12735/0
SENDGRID_API_KEY=your_sendgrid_api_key
SENDGRID_FROM_EMAIL=noreply@yourdomain.com
SENDGRID_FROM_NAME=MediRemind
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
JWT_SECRET_KEY=your_jwt_secret_key_here
```

#### Frontend Service Environment Variables:
```
VITE_API_URL=https://your-backend-service.onrender.com
```

## Option 2: Manual Deployment

### Step 1: Create PostgreSQL Database

1. Go to Render Dashboard
2. Click "New" → "PostgreSQL"
3. Configure:
   - **Name**: `mediremind-db`
   - **Database Name**: `mediremind`
   - **User**: `mediremind`
   - **Region**: Choose your preferred region
   - **Plan**: Select appropriate plan
4. Click "Create Database"
5. Note the connection details for later use

### Step 2: Deploy Backend (Django)

1. Click "New" → "Web Service"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `mediremind-backend`
   - **Runtime**: `Python`
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn mediremind_backend.wsgi:application`
   - **Plan**: Select appropriate plan
   - **Region**: Same as database

4. Add Environment Variables:
   ```
   DATABASE_URL=<from_postgresql_service>
   DJANGO_SECRET_KEY=<generate_secure_key>
   DEBUG=false
   ENVIRONMENT=production
   REDIS_URL=redis://default:oE1Gh8TkVwGkuihbKt43XrQeZVTLbl4p@redis-12735.crce204.eu-west-2-3.ec2.redns.redis-cloud.com:12735/0
   SENDGRID_API_KEY=your_sendgrid_api_key
   SENDGRID_FROM_EMAIL=noreply@yourdomain.com
   SENDGRID_FROM_NAME=MediRemind
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_supabase_anon_key
   SUPABASE_SERVICE_KEY=your_supabase_service_role_key
   JWT_SECRET_KEY=your_jwt_secret_key_here
   ```

5. Click "Create Web Service"

### Step 3: Deploy Frontend (React)

1. Click "New" → "Static Site"
2. Connect your GitHub repository
3. Configure:
   - **Name**: `mediremind-frontend`
   - **Build Command**: `cd staff-portal && npm ci && npm run build`
   - **Publish Directory**: `staff-portal/dist`
   - **Plan**: Select appropriate plan

4. Add Environment Variables:
   ```
   VITE_API_URL=https://your-backend-service.onrender.com
   ```

5. Click "Create Static Site"

## Post-Deployment Configuration

### Step 1: Update CORS Settings

After both services are deployed, update the backend's CORS settings:

1. Go to your backend service settings
2. Add the frontend URL to the `FRONTEND_URL` environment variable
3. The application will automatically update CORS_ALLOWED_ORIGINS

### Step 2: Database Migration

The build script automatically runs migrations, but you can manually trigger them:

1. Go to your backend service
2. Open the "Shell" tab
3. Run: `python manage.py migrate`

### Step 3: Create Superuser (Optional)

To create an admin user:

1. Go to your backend service shell
2. Run: `python manage.py createsuperuser`
3. Follow the prompts

### Step 4: Test the Deployment

1. Visit your frontend URL
2. Test user registration and login
3. Verify appointment scheduling works
4. Check that notifications are sent properly

## Health Checks

Both services include health checks:

- **Backend**: `/health/` endpoint
- **Frontend**: Automatic static file serving check

## Monitoring and Logs

1. **Logs**: Available in each service's "Logs" tab
2. **Metrics**: Available in each service's "Metrics" tab
3. **Health**: Monitor via the health check endpoints

## Troubleshooting

### Common Issues:

1. **Database Connection Errors**:
   - Verify DATABASE_URL is correctly set
   - Check database service is running

2. **Static Files Not Loading**:
   - Ensure WhiteNoise is properly configured
   - Run `python manage.py collectstatic`

3. **CORS Errors**:
   - Verify FRONTEND_URL is set correctly
   - Check CORS_ALLOWED_ORIGINS includes your frontend URL

4. **Build Failures**:
   - Check build logs for specific errors
   - Ensure all dependencies are in requirements.txt/package.json

### Getting Help:

1. Check Render documentation: [docs.render.com](https://docs.render.com)
2. Review service logs for error details
3. Verify environment variables are correctly set

## Security Considerations

1. **Secret Keys**: Use strong, unique secret keys
2. **Environment Variables**: Never commit secrets to version control
3. **HTTPS**: Render provides HTTPS by default
4. **Database**: Use strong passwords and restrict access

## Scaling

Render provides easy scaling options:
- **Horizontal Scaling**: Add more instances
- **Vertical Scaling**: Upgrade to higher-tier plans
- **Database Scaling**: Upgrade database plan as needed

## Cost Optimization

1. Start with Starter plans for testing
2. Monitor usage and scale as needed
3. Use static sites for frontend (cheaper than web services)
4. Consider shared databases for development

---

**Note**: Replace placeholder values (like API keys and URLs) with your actual production values before deployment.