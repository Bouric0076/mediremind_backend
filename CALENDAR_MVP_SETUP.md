# Calendar Integration MVP - Setup Guide

## 🚀 Quick Start

The Calendar Integration MVP is now ready for testing! This implementation provides core functionality for connecting and syncing with Google Calendar.

## ✅ What's Implemented

### Core Features
- **Google Calendar OAuth Authentication** - Secure connection to Google Calendar
- **Basic Calendar Sync** - Bidirectional synchronization of events
- **Conflict Detection System** - Identifies scheduling conflicts
- **Provider Dashboard** - Beautiful web interface for managing integrations
- **Availability Calculation** - Basic availability tracking

### Technical Components
- **Models**: CalendarIntegration, ExternalCalendarEvent, CalendarConflict, CalendarAvailability
- **Views**: Complete API endpoints for all calendar operations
- **Services**: GoogleCalendarService for Google Calendar integration
- **Tasks**: Celery background tasks for sync operations
- **Dashboard**: Modern web interface at `/calendar/`

## 🌐 Access the Dashboard

Visit: **http://localhost:8000/calendar/**

The dashboard provides:
- Visual calendar integration management
- Connection status for providers
- Sync controls and monitoring
- API endpoint documentation

## 🔧 API Endpoints

### Integration Management
- `GET /calendar/integrations/` - List all integrations
- `POST /calendar/integrations/` - Create new integration
- `GET /calendar/integrations/{id}/` - Get integration details

### OAuth Authentication
- `GET /calendar/oauth/google/` - Start Google OAuth flow
- `GET /calendar/oauth/callback/` - Handle OAuth callback

### Sync Operations
- `POST /calendar/sync/{integration_id}/` - Trigger manual sync
- `GET /calendar/events/` - List synchronized events

### Conflict Management
- `GET /calendar/conflicts/` - View scheduling conflicts
- `POST /calendar/conflicts/{id}/resolve/` - Resolve conflicts

### Availability
- `GET /calendar/availability/` - Check availability
- `POST /calendar/availability/calculate/` - Calculate availability

## 🔐 Authentication

All API endpoints require authentication. Include your authentication token in the header:
```
Authorization: Token your_auth_token_here
```

## 📋 Next Steps for Production

### 1. Google OAuth Setup
- Create Google Cloud Project
- Enable Google Calendar API
- Configure OAuth 2.0 credentials
- Set redirect URI: `http://your-domain.com/calendar/oauth/callback/`

### 2. Environment Variables
```bash
# Google Calendar
GOOGLE_CALENDAR_CLIENT_ID=your_client_id
GOOGLE_CALENDAR_CLIENT_SECRET=your_client_secret
GOOGLE_CALENDAR_REDIRECT_URI=http://your-domain.com/calendar/oauth/callback/

# Celery (for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Background Tasks
Start Celery worker for background sync:
```bash
celery -A mediremind_backend worker --loglevel=info
```

### 4. Database
The migrations are already applied. The following tables are created:
- `calendar_integrations_calendarintegration`
- `calendar_integrations_externalcalendarevent`
- `calendar_integrations_calendarconflict`
- `calendar_integrations_calendaravailability`
- `calendar_integrations_calendarsynclog`

## 🧪 Testing

### Test the Dashboard
1. Visit `http://localhost:8000/calendar/`
2. Explore the integration interface
3. Test the visual components

### Test API Endpoints
```bash
# Check health
curl http://localhost:8000/health/

# List integrations (requires auth)
curl -H "Authorization: Token your_token" http://localhost:8000/calendar/integrations/

# Check availability
curl -H "Authorization: Token your_token" http://localhost:8000/calendar/availability/
```

## 🎯 MVP Success Criteria

✅ **Google Calendar OAuth** - Complete authentication flow
✅ **Basic Sync** - Events sync between systems  
✅ **Conflict Detection** - Identifies scheduling conflicts
✅ **Dashboard Interface** - User-friendly management interface
✅ **API Endpoints** - Complete REST API for all operations

## 🔄 Background Sync

The system includes automated background tasks:
- **sync_calendar_events** - Syncs events from external calendars
- **detect_calendar_conflicts** - Identifies scheduling conflicts
- **calculate_availability** - Updates availability data
- **cleanup_old_sync_logs** - Maintains system performance

## 🚀 Ready for Integration

The Calendar Integration MVP is production-ready for basic use cases. The system provides:

1. **Secure Authentication** with OAuth 2.0
2. **Reliable Sync** with error handling
3. **Conflict Management** for scheduling
4. **Modern Interface** for user management
5. **Scalable Architecture** for future enhancements

## 📞 Support

For technical support or feature requests, refer to the main project documentation or contact the development team.

---

**Status**: ✅ MVP Complete - Ready for Testing and Production Deployment