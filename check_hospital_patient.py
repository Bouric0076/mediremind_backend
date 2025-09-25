import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mediremind_backend.settings")
django.setup()

from accounts.models import HospitalPatient

def check_hospital_patient_entry(email):
    try:
        exists = HospitalPatient.objects.filter(patient__user__email=email).exists()
        if exists:
            print(f"HospitalPatient entry exists for email: {email}")
        else:
            print(f"No HospitalPatient entry found for email: {email}")
    except Exception as e:
        print(f"Error occurred while checking HospitalPatient entry: {str(e)}")

if __name__ == "__main__":
    email_to_check = input("Enter the email to check: ")
    check_hospital_patient_entry(email_to_check)