from supabase_client import supabase, admin_client

class AuthenticatedUser:
    """Class to represent an authenticated user with their profile data"""
    def __init__(self, auth_user, profile_data):
        self.id = auth_user.id
        self.email = auth_user.email
        self.profile = profile_data

def get_authenticated_user(access_token):
    """Get authenticated user from Supabase or Django token"""
    if not access_token:
        print("No access token provided")
        return None
        
    try:
        # First try Django token authentication
        from rest_framework.authtoken.models import Token
        from django.contrib.auth import get_user_model
        
        try:
            django_token = Token.objects.get(key=access_token)
            user = django_token.user
            print(f"Successfully authenticated Django user: {user.id} ({user.email})")
            
            # Create a simple user object that matches the expected interface
            class DjangoAuthenticatedUser:
                def __init__(self, user):
                    self.id = str(user.id)
                    self.email = user.email
                    self.profile = {'role': user.role, 'full_name': user.full_name}
            
            return DjangoAuthenticatedUser(user)
            
        except Token.DoesNotExist:
            print("Not a Django token, trying Supabase...")
            pass
        
        # Fallback to Supabase token authentication
        print(f"Attempting to get user data with Supabase token: {access_token[:10]}...")
        response = supabase.auth.get_user(access_token)
        
        if not response:
            print("No response from auth.get_user")
            return None
            
        if not response.user:
            print("No user in auth response")
            return None
            
        if not response.user.id:
            print("No user ID in auth response")
            return None

        # Get full user data from database
        print(f"Getting user data from database for ID: {response.user.id}")
        user_data = admin_client.table("users").select("*").eq("id", response.user.id).single().execute()
        
        if not user_data.data:
            print(f"No user data found in database for ID: {response.user.id}")
            return None

        # Create authenticated user instance with profile data
        auth_user = AuthenticatedUser(response.user, user_data.data)
        print(f"Successfully authenticated Supabase user: {auth_user.id} with role: {auth_user.profile.get('role')}")
        return auth_user

    except Exception as e:
        print(f"Authentication error in get_authenticated_user: {str(e)}")
        return None

def get_user_by_id(user_id):
    """Get user by ID from database"""
    try:
        user_data = admin_client.table("users").select("*").eq("id", user_id).single().execute()
        return user_data.data if user_data.data else None
    except Exception as e:
        print(f"Error getting user by ID {user_id}: {str(e)}")
        return None

def get_user_profile(user_id, role=None):
    """Get user profile based on role"""
    try:
        if role == 'patient':
            profile_data = admin_client.table("enhanced_patients").select("*").eq("user_id", user_id).single().execute()
        elif role in ['doctor', 'nurse', 'staff']:
            profile_data = admin_client.table("enhanced_staff_profiles").select("*").eq("user_id", user_id).single().execute()
        else:
            # Try to determine role from user data
            user_data = get_user_by_id(user_id)
            if user_data and user_data.get('role') == 'patient':
                profile_data = admin_client.table("enhanced_patients").select("*").eq("user_id", user_id).single().execute()
            else:
                profile_data = admin_client.table("enhanced_staff_profiles").select("*").eq("user_id", user_id).single().execute()
        
        return profile_data.data if profile_data.data else None
    except Exception as e:
        print(f"Error getting user profile for {user_id}: {str(e)}")
        return None