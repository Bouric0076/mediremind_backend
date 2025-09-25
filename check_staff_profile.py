import os
import django

# Ensure settings are configured before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mediremind_backend.settings")
django.setup()

from django.core.exceptions import ObjectDoesNotExist
from accounts.models import EnhancedStaffProfile, Hospital, User

def check_staff_profile(email):
    try:
        # Debugging: Print the current DJANGO_SETTINGS_MODULE
        print("DJANGO_SETTINGS_MODULE:", os.environ.get("DJANGO_SETTINGS_MODULE"))

        # Fetch user by email
        user = User.objects.get(email=email)
        print(f"User found: {user}")

        # Check for EnhancedStaffProfile
        try:
            staff_profile = EnhancedStaffProfile.objects.get(user=user)
            print(f"Staff profile found: {staff_profile}")

            # Check for associated hospital
            if staff_profile.hospital:
                print(f"Hospital associated: {staff_profile.hospital}")
            else:
                print("No hospital associated with staff profile.")
        except ObjectDoesNotExist:
            print("No EnhancedStaffProfile found for user.")

    except ObjectDoesNotExist:
        print("No user found with the provided email.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    email = input("Enter the email of the user to check: ")
    check_staff_profile(email)