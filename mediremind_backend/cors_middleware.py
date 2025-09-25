class CustomCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Define allowed origins for development
        self.allowed_origins = [
            'http://localhost:3000',
            'http://localhost:5173',  # Vite default port
            'http://localhost:8080',  # Flutter web app port
            'http://127.0.0.1:3000',
            'http://127.0.0.1:5173',
            'http://127.0.0.1:8080',
        ]

    def __call__(self, request):
        response = self.get_response(request)
        
        # Get the origin from the request
        origin = request.META.get('HTTP_ORIGIN')
        
        # Check if the origin is allowed
        if origin in self.allowed_origins:
            response['Access-Control-Allow-Origin'] = origin
        else:
            # Fallback to localhost:5173 for development
            response['Access-Control-Allow-Origin'] = 'http://localhost:5173'
            
        response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response['Access-Control-Allow-Credentials'] = 'true'
        response['Access-Control-Max-Age'] = '86400'
        
        # Handle preflight requests
        if request.method == 'OPTIONS':
            response.status_code = 200
            response.content = b''
            
        return response