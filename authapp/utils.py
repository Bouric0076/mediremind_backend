from supabase_client import supabase, admin_client

class AuthenticatedUser:
    """Class to represent an authenticated user with their profile data"""
    def __init__(self, auth_user, profile_data):
        self.id = auth_user.id
        self.email = auth_user.email
        self.profile = profile_data

def get_authenticated_user(access_token):
    """Get authenticated user from Supabase token"""
    if not access_token:
        print("No access token provided")
        return None
        
    try:
        # Get user data from auth
        print(f"Attempting to get user data with token: {access_token[:10]}...")
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
        print(f"Successfully authenticated user: {auth_user.id} with role: {auth_user.profile.get('role')}")
        return auth_user

    except Exception as e:
        print(f"Authentication error in get_authenticated_user: {str(e)}")
        return None

def get_user_by_id(user_id):
    """Get user by ID from database"""
    if not user_id:
        print("No user ID provided")
        return None
        
    try:
        response = admin_client.table("users").select("*").eq("id", user_id).single().execute()
        if not response.data:
            print(f"No user found for ID: {user_id}")
            return None
        return response.data
    except Exception as e:
        print(f"Database error in get_user_by_id: {str(e)}")
        return None
    
def get_user_by_email(email):
    """Get user by email from database"""
    if not email:
        print("No email provided")
        return None
        
    try:
        response = admin_client.table("users").select("*").eq("email", email).single().execute()
        if not response.data:
            print(f"No user found for email: {email}")
            return None
        return response.data
    except Exception as e:
        print(f"Database error in get_user_by_email: {str(e)}")
        return None

    

