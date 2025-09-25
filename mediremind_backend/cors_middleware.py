import os
from django.conf import settings

class CustomCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define allowed origins based on environment
        if settings.DEBUG:
            self.allowed_origins = [
                'http://localhost:3000',
                'http://localhost:5173',  # Vite default port
                'http://localhost:8080',  # Flutter web app port
                'http://127.0.0.1:3000',
                'http://127.0.0.1:5173',
                'http://127.0.0.1:8080',
            ]
        else:
            # Production origins
            self.allowed_origins = [
                'https://mediremind-frontend.onrender.com',
                'https://mediremind-backend-cl6r.onrender.com',
            ]
            # Add FRONTEND_URL from environment if available
            if 'FRONTEND_URL' in os.environ:
                frontend_url = os.environ['FRONTEND_URL']
                if not frontend_url.startswith(('http://', 'https://')):
                    frontend_url = f"https://{frontend_url}"
                self.allowed_origins.append(frontend_url)

    def __call__(self, request):
        response = self.get_response(request)
        
        # Get the origin from the request
        origin = request.META.get('HTTP_ORIGIN')
        
        # Check if the origin is allowed
        if origin in self.allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
        elif settings.DEBUG:
            # Fallback to localhost:5173 for development
            response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
        else:
            # In production, be more restrictive
            response['Access-Control-Allow-Origin'] = 'https://mediremind-frontend.onrender.com'
            
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With, X-CSRFToken'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'
        
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response.status_code = 200
            response.content = b''
            
        return response