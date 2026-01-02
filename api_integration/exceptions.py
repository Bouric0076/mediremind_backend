from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """Custom exception handler for API integration"""
    
    # Call REST framework's default exception handler first,
    # to get the standard error response.
    response = exception_handler(exc, context)
    
    # Now add the HTTP status code to the response.
    if response is not None:
        response.data['status_code'] = response.status_code
        response.data['request_id'] = context['request'].META.get('HTTP_X_REQUEST_ID', 'unknown')
    
    # Handle specific exceptions
    if isinstance(exc, ValidationError):
        return Response({
            'success': False,
            'error_code': 'VALIDATION_ERROR',
            'message': 'Validation error occurred',
            'errors': exc.message_dict if hasattr(exc, 'message_dict') else str(exc),
            'request_id': context['request'].META.get('HTTP_X_REQUEST_ID', 'unknown'),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Log unhandled exceptions
    if response is None:
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return Response({
            'success': False,
            'error_code': 'INTERNAL_ERROR',
            'message': 'An unexpected error occurred',
            'request_id': context['request'].META.get('HTTP_X_REQUEST_ID', 'unknown'),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response