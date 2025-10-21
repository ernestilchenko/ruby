# Railway Deployment Guide

This guide explains how to deploy the Ruby API (Polish Cadastral Data API) to Railway.

## Prerequisites

- Railway account (sign up at https://railway.app)
- GitHub account (for connecting your repository)
- This repository pushed to GitHub

## Architecture on Railway

Railway will run two separate services:
1. **Web Service** - Django application with Gunicorn
2. **Redis Service** - Railway managed Redis for caching and Celery broker

## Step-by-Step Deployment

### 1. Create a New Project on Railway

1. Go to https://railway.app/new
2. Click "Deploy from GitHub repo"
3. Select your repository
4. Railway will automatically detect the Dockerfile

### 2. Add Redis Service

1. In your Railway project, click "+ New"
2. Select "Database" → "Add Redis"
3. Railway will automatically create a Redis instance and provide `REDIS_URL` environment variable

### 3. Configure Environment Variables

In your Railway web service settings, add these environment variables:

#### Required Variables

```bash
SECRET_KEY=your-super-secret-key-here-generate-a-strong-one
```

Generate a secure SECRET_KEY using Python:
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

#### Optional Variables

```bash
# Production settings
DEBUG=False
ALLOWED_HOSTS=your-app.railway.app,yourdomain.com

# Redis is automatically configured via REDIS_URL by Railway
# No need to set REDIS_URL manually - Railway does this automatically

# If you want custom cache URL (defaults to REDIS_URL with /1 database)
CACHE_URL=redis://default:password@host:6379/1

# Celery configuration (defaults to REDIS_URL)
CELERY_BROKER_URL=redis://default:password@host:6379/0
CELERY_RESULT_BACKEND=redis://default:password@host:6379/0
```

### 4. Deploy

1. Railway will automatically build and deploy your application
2. Wait for the build to complete (this may take 5-10 minutes due to QGIS installation)
3. Once deployed, Railway will provide a public URL (e.g., `https://your-app.railway.app`)

### 5. Run Database Migrations

After first deployment, you may need to run migrations:

1. Go to your Railway project
2. Click on the web service
3. Go to "Settings" → "Deploy"
4. Or use Railway CLI:

```bash
railway run python manage.py migrate
railway run python manage.py collectstatic --noinput
```

## Accessing Your API

After deployment, your API will be available at:

- **API Base**: `https://your-app.railway.app/api/`
- **Swagger Docs**: `https://your-app.railway.app/api/docs/`
- **OpenAPI Schema**: `https://your-app.railway.app/api/schema/`

## Example API Endpoints

```bash
# Search parcel by coordinates
curl "https://your-app.railway.app/api/search-parcel-xy/?x=500000&y=250000&epsg=2180"

# Search building by coordinates
curl "https://your-app.railway.app/api/search-building-xy/?x=500000&y=250000&epsg=2180"

# Get commune by coordinates
curl "https://your-app.railway.app/api/commune-xy/?x=500000&y=250000&epsg=2180"
```

## Optional: Add Celery Worker Service

If you need Celery for async task processing:

1. In Railway project, click "+ New"
2. Select "Empty Service"
3. Connect to the same GitHub repository
4. Set custom start command in Settings:
   ```bash
   celery -A ruby worker -l info
   ```
5. Add environment variables (same as web service)

## Monitoring and Logs

- **View Logs**: Go to your service → "Deployments" → Click on a deployment
- **Metrics**: Railway provides CPU, memory, and network metrics
- **Health Check**: Add a `/health` endpoint to monitor service status

## Troubleshooting

### Build Fails

- Check the build logs in Railway dashboard
- Ensure Dockerfile builds successfully locally first
- QGIS installation can be slow - be patient

### Redis Connection Issues

- Verify `REDIS_URL` is set automatically by Railway
- Check Redis service is running in Railway project
- Test connection: `redis-cli -u $REDIS_URL ping`

### Static Files Not Loading

- Ensure `collectstatic` was run after deployment
- Check STATIC_ROOT and WhiteNoise configuration
- Verify staticfiles are included in Docker image

### Application Errors

- Check logs: `railway logs`
- Verify all environment variables are set
- Ensure migrations have been run

## Useful Railway CLI Commands

Install Railway CLI:
```bash
npm install -g @railway/cli
railway login
```

Useful commands:
```bash
# Link to your project
railway link

# View logs
railway logs

# Run commands in Railway environment
railway run python manage.py migrate
railway run python manage.py collectstatic --noinput

# Open railway dashboard
railway open

# SSH into container (if needed)
railway shell
```

## Cost Optimization

Railway pricing is based on usage:
- **Starter Plan**: $5/month includes $5 credit
- **Developer Plan**: $20/month includes $20 credit
- Monitor your usage in Railway dashboard

Tips to reduce costs:
- Use sleep mode for non-production environments
- Optimize Docker image size (already using multi-stage build)
- Monitor Redis memory usage
- Use caching effectively to reduce CPU usage

## Environment-Specific Settings

### Development (Local)
```bash
DEBUG=True
REDIS_URL=redis://redis:6379/0
```

### Production (Railway)
```bash
DEBUG=False
SECRET_KEY=strong-secret-key
ALLOWED_HOSTS=your-app.railway.app
# REDIS_URL automatically provided by Railway
```

## Next Steps

1. Set up custom domain (Railway Settings → Domains)
2. Add monitoring and alerting
3. Implement health check endpoints
4. Set up CI/CD with GitHub Actions
5. Add SSL certificate (automatic with Railway)

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: https://github.com/your-username/ruby/issues
