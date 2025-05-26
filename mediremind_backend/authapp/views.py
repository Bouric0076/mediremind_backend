from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from supabase_client import supabase, admin_client  # import both clients

@csrf_exempt
def register_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            email = data.get("email")
            password = data.get("password")
            full_name = data.get("full_name")
            phone = data.get("phone")
            role = data.get("role")  # 'patient', 'doctor', etc.

            if not all([email, password, full_name, phone, role]):
                return JsonResponse({"error": "All fields are required"}, status=400)

            # 1. Register with Supabase Auth
            result = supabase.auth.sign_up({
                "email": email,
                "password": password
            })

            if not result.user:
                return JsonResponse({"error": "Sign-up failed"}, status=400)

            user_id = result.user.id

            # 2. First create the base user record using admin client
            base_user = {
                "id": user_id,
                "email": email,
                "full_name": full_name,
                "phone": phone,
                "role": role
            }
            admin_client.table("users").insert(base_user).execute()

            # 3. Insert into profile table using admin client
            profile_data = {
                "user_id": user_id,
                "full_name": full_name,
                "phone": phone,
                "email": email
            }

            if role == "patient":
                admin_client.table("patients").insert(profile_data).execute()
            else:
                profile_data["position"] = role  # e.g., 'doctor', 'admin'
                admin_client.table("staff_profiles").insert(profile_data).execute()

            return JsonResponse({"message": "Registration successful"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def login_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")
            password = data.get("password")

            if not all([email, password]):
                return JsonResponse({"error": "Email and password required"}, status=400)

            result = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })

            session = result.session
            user = result.user

            if not session:
                return JsonResponse({"error": "Login failed"}, status=401)

            return JsonResponse({
                "message": "Login successful",
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "user": {
                    "id": user.id,
                    "email": user.email
                }
            }, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def forgot_password(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            email = data.get("email")

            if not email:
                return JsonResponse({"error": "Email is required"}, status=400)

            supabase.auth.reset_password_email(email)
            return JsonResponse({"message": "Password reset email sent"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)


@csrf_exempt
def logout_user(request):
    if request.method == "POST":
        try:
            # Get the access token from the Authorization header
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                return JsonResponse({"error": "Authorization header missing or invalid"}, status=401)

            # Extract the token
            token = auth_header.split(' ')[1]

            # Sign out the user
            supabase.auth.sign_out()
            return JsonResponse({"message": "Logged out successfully"}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Method not allowed"}, status=405)

@csrf_exempt
def whoami(request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JsonResponse({"error": "Missing or invalid Authorization header"}, status=401)

    token = auth_header.split(" ")[1]

    try:
        # Get user data from auth
        user_data = supabase.auth.get_user(token)
        if not user_data or not user_data.user or not user_data.user.id:
            return JsonResponse({"error": "Invalid or expired token"}, status=401)

        user_id = user_data.user.id

        # First get user role from users table
        user_result = admin_client.table("users").select("role").eq("id", user_id).execute()
        if not user_result.data:
            return JsonResponse({"error": "User not found"}, status=404)

        role = user_result.data[0]['role']

        # Get profile based on role
        if role == "patient":
            profile_res = admin_client.table("patients").select("*").eq("user_id", user_id).execute()
            if profile_res.data:
                return JsonResponse({
                    "role": "patient",
                    "user_id": user_id,
                    "profile": profile_res.data[0]
                })
        else:
            profile_res = admin_client.table("staff_profiles").select("*").eq("user_id", user_id).execute()
            if profile_res.data:
                return JsonResponse({
                    "role": role,
                    "user_id": user_id,
                    "profile": profile_res.data[0]
                })

        return JsonResponse({"error": "User profile not found"}, status=404)

    except Exception as e:
        print(f"Error in whoami: {str(e)}")  # Add logging for debugging
        return JsonResponse({"error": "Authentication failed"}, status=401)