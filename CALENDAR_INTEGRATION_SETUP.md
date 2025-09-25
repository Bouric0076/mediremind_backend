# 🚀 Calendar Integration Quick Setup Guide

## 🎯 Overview
This guide will help you set up the calendar integration system that gives MediRemind a massive competitive advantage by connecting with providers' existing Google Calendar, Outlook, and other scheduling tools.

## ⚡ Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client
pip install msal  # For Microsoft Graph API
pip install celery redis  # For background tasks
```

### 2. Environment Variables
Add these to your `.env` file:

```env
# Google Calendar Integration
GOOGLE_CALENDAR_CLIENT_ID=your_google_client_id
GOOGLE_CALENDAR_CLIENT_SECRET=your_google_client_secret
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:8000/api/calendar/oauth/callback/

# Microsoft Outlook Integration
OUTLOOK_CALENDAR_CLIENT_ID=your_outlook_client_id
OUTLOOK_CALENDAR_CLIENT_SECRET=your_outlook_client_secret
OUTLOOK_TENANT_ID=common

# Calendly Integration
CALENDLY_CLIENT_ID=your_calendly_client_id
CALENDLY_CLIENT_SECRET=your_calendly_client_secret

# Security
CALENDAR_TOKEN_ENCRYPTION_KEY=your_encryption_key

# Redis for Celery (background tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
```

### 3. Update Django Settings
Add to your `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps
    'calendar_integrations',
    'djcelery',  # If using django-celery
]
```

### 4. Run Migrations
```bash
python manage.py makemigrations calendar_integrations
python manage.py migrate
```

### 5. Update Main URLs
Add to your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns
    path('api/calendar/', include('calendar_integrations.urls')),
]
```

### 6. Start Background Tasks
```bash
# Terminal 1: Start Celery worker
celery -A your_project_name worker --loglevel=info

# Terminal 2: Start Celery beat (scheduler)
celery -A your_project_name beat --loglevel=info

# Terminal 3: Start Django server
python manage.py runserver
```

## 🔧 OAuth Setup Instructions

### Google Calendar Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google Calendar API
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:8000/api/calendar/oauth/callback/`
6. Copy Client ID and Secret to your `.env` file

### Microsoft Outlook Setup
1. Go to [Azure Portal](https://portal.azure.com/)
2. Navigate to Azure Active Directory > App registrations
3. Create new registration
4. Add redirect URI: `http://localhost:8000/api/calendar/oauth/outlook/callback/`
5. Grant Calendar permissions
6. Copy Application ID and Secret to your `.env` file

### Calendly Setup
1. Go to [Calendly Developer Portal](https://developer.calendly.com/)
2. Create new OAuth application
3. Set redirect URI: `http://localhost:8000/api/calendar/oauth/calendly/callback/`
4. Copy Client ID and Secret to your `.env` file

## 🎮 Testing the Integration

### 1. Test Google Calendar Connection
```bash
curl -X POST http://localhost:8000/api/calendar/integrations/ \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "provider_profile_id": 1
  }'
```

### 2. Test OAuth Flow
Visit: `http://localhost:8000/api/calendar/oauth/google/?provider_profile_id=1`

### 3. Test Sync
```bash
curl -X POST http://localhost:8000/api/calendar/sync/ \
  -H "Content-Type: application/json" \
  -d '{
    "integration_id": 1,
    "force_full_sync": true
  }'
```

## 📊 Monitoring & Analytics

### View Integration Status
```bash
curl http://localhost:8000/api/calendar/integrations/
```

### Check Sync Logs
```bash
curl http://localhost:8000/api/calendar/sync-logs/
```

### View Conflicts
```bash
curl http://localhost:8000/api/calendar/conflicts/
```

### Check Availability
```bash
curl http://localhost:8000/api/calendar/availability/?provider_id=1&date=2024-01-15
```

## 🚨 Troubleshooting

### Common Issues

#### 1. OAuth Redirect Mismatch
**Error**: `redirect_uri_mismatch`
**Solution**: Ensure redirect URIs in OAuth apps match exactly with your `.env` settings

#### 2. Token Refresh Failures
**Error**: `invalid_grant`
**Solution**: Check system clock synchronization and token expiration handling

#### 3. Sync Task Failures
**Error**: Celery tasks not running
**Solution**: Ensure Redis is running and Celery worker is started

#### 4. Rate Limit Errors
**Error**: `quotaExceeded`
**Solution**: Implement exponential backoff and respect API rate limits

### Debug Mode
Set `DEBUG=True` in settings for detailed error messages and test configurations.

## 🎯 Next Steps

### Phase 1: Basic Integration (Week 1)
- [x] Set up Google Calendar OAuth
- [ ] Test bi-directional sync
- [ ] Implement conflict detection
- [ ] Create provider onboarding flow

### Phase 2: Multi-Platform (Week 2-3)
- [ ] Add Outlook integration
- [ ] Implement Calendly webhooks
- [ ] Create unified dashboard
- [ ] Add Apple Calendar support

### Phase 3: AI Features (Week 4-6)
- [ ] Smart appointment detection
- [ ] Predictive conflict resolution
- [ ] Availability optimization
- [ ] Patient preference learning

## 💡 Pro Tips

### 1. Gradual Rollout
Start with a few test providers before full deployment.

### 2. Provider Training
Create simple video tutorials showing the 2-minute setup process.

### 3. Marketing Advantage
Emphasize "Keep your Google Calendar, add medical intelligence" in marketing.

### 4. Support Strategy
Prepare support team for OAuth troubleshooting and integration questions.

### 5. Performance Monitoring
Monitor sync performance and API usage to optimize costs.

## 🏆 Success Metrics

Track these KPIs to measure competitive advantage:

- **Adoption Rate**: % of providers who enable calendar integration
- **Time to Value**: Minutes from signup to first successful sync
- **Conflict Resolution**: % of conflicts automatically resolved
- **User Satisfaction**: Rating for calendar integration features
- **Retention Impact**: Retention difference for integrated vs non-integrated users

## 🔒 Security Checklist

- [ ] OAuth tokens encrypted at rest
- [ ] HTTPS enforced for production OAuth flows
- [ ] Patient data anonymized in external calendars
- [ ] Regular security audits of calendar access
- [ ] Compliance with healthcare data regulations

---

**Remember**: This isn't just a feature - it's your competitive moat. No other medical appointment system offers this level of calendar integration. You're not asking providers to change their workflow; you're adapting to theirs. That's the ultimate competitive advantage! 🚀