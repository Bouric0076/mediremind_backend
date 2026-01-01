#!/usr/bin/env python
"""
Test script to verify emergency contact template time display fix
"""
import os
import sys
import django
from django.template.loader import render_to_string
from django.conf import settings

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mediremind_backend.settings')
django.setup()

def test_emergency_contact_template():
    """Test the emergency contact template rendering with proper time display"""
    print("Testing emergency contact template rendering...")
    
    # Test data that mimics what would be passed to the template
    test_data = {
        'emergency_contact_name': 'Jane Doe',
        'emergency_contact_relationship': 'Spouse',
        'patient_name': 'John Doe',
        'appointment_date': '2026-01-02',
        'appointment_time': '14:30',
        'doctor_name': 'Dr. Smith',
        'appointment': {
            'doctor_name': 'Dr. Smith',
            'location': 'Main Hospital, Room 101',
            'type': 'General Checkup',
            'preparation_instructions': 'Please bring your insurance card and ID.'
        },
        'support_phone': '(555) 123-4567',
        'support_email': 'support@mediremind.com'
    }
    
    try:
        # Test the reminder template
        html_content = render_to_string(
            'notifications/email/emergency_contact_appointment_reminder.html',
            test_data
        )
        
        print("✅ Template rendered successfully!")
        
        # Check if TBD appears in the rendered template
        if 'TBD' in html_content:
            print("❌ Found 'TBD' in rendered template!")
            # Find the specific lines with TBD
            lines = html_content.split('\n')
            for i, line in enumerate(lines):
                if 'TBD' in line:
                    print(f"   Line {i+1}: {line.strip()}")
            return False
        else:
            print("✅ No 'TBD' found in rendered template")
        
        # Check if the time is displayed correctly
        if '14:30' in html_content:
            print("✅ Time (14:30) found in rendered template")
        else:
            print("❌ Time (14:30) not found in rendered template")
            return False
            
        # Check if the date is displayed correctly  
        if '2026-01-02' in html_content:
            print("✅ Date (2026-01-02) found in rendered template")
        else:
            print("❌ Date (2026-01-02) not found in rendered template")
            return False
        
        # Show a snippet of the rendered template around the time display
        lines = html_content.split('\n')
        for i, line in enumerate(lines):
            if 'Time:' in line and '14:30' in line:
                print(f"\n📅 Time display section (lines {max(0, i-2)}-{min(len(lines), i+3)}):")
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    print(f"   {j+1:3d}: {lines[j]}")
                break
        
        return True
        
    except Exception as e:
        print(f"❌ Template rendering failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_with_missing_data():
    """Test template behavior when appointment_time is missing"""
    print("\n" + "="*60)
    print("Testing template with missing appointment_time...")
    
    # Test data with missing time
    test_data_missing = {
        'emergency_contact_name': 'Jane Doe',
        'emergency_contact_relationship': 'Spouse', 
        'patient_name': 'John Doe',
        'appointment_date': '2026-01-02',
        # Note: appointment_time is missing
        'doctor_name': 'Dr. Smith',
        'appointment': {
            'doctor_name': 'Dr. Smith',
            'location': 'Main Hospital, Room 101'
        }
    }
    
    try:
        html_content = render_to_string(
            'notifications/email/emergency_contact_appointment_reminder.html',
            test_data_missing
        )
        
        print("✅ Template rendered with missing data!")
        
        # Should show TBD when appointment_time is missing
        if 'TBD' in html_content:
            print("✅ 'TBD' correctly shown when appointment_time is missing")
        else:
            print("❌ 'TBD' not shown when appointment_time is missing")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Template rendering with missing data failed: {str(e)}")
        return False

if __name__ == '__main__':
    success1 = test_emergency_contact_template()
    success2 = test_with_missing_data()
    
    if success1 and success2:
        print("\n🎉 All tests passed! Emergency contact template time display issue is fixed.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. The template fix may not be complete.")
        sys.exit(1)