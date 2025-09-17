from django.http import JsonResponse
from django.db import connection
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def health_check(request):
    """
    Simple health check endpoint for Render deployment.
    Returns 200 if the application is healthy, 500 otherwise.
    """
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            
        # Basic health response
        health_data = {
            "status": "healthy",
            "database": "connected",
            "debug": settings.DEBUG,
            "environment": "production" if not settings.DEBUG else "development"
        }
        
        return JsonResponse(health_data, status=200)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        
        error_data = {
            "status": "unhealthy",
            "error": str(e),
            "database": "disconnected"
        }
        
        return JsonResponse(error_data, status=500)