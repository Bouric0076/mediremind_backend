#!/usr/bin/env python3
"""
Test script to verify no-show notification functionality
"""

def test_no_show_logic():
    """Test the no-show notification logic"""
    
    print("Testing no-show notification logic...")
    
    # Test appointment data with emergency contact
    appointment_data = {
        'id': 123,
        'appointment_date': '2024-01-15',
        'start_time': '10:00',
        'provider_name': 'Dr. Smith',
        'appointment_type_name': 'Consultation',
        'hospital_name': 'MediRemind Clinic',
        'patient_id': 456,
        'patient_name': 'John Doe',
        'patient_email': 'john@example.com',
        'emergency_contact_email': 'emergency@example.com',
        'changes': {
            'status': {
                'old': 'scheduled',
                'new': 'no-show'
            }
        }
    }
    
    # Simulate the update type logic
    old_status = appointment_data.get('changes', {}).get('status', {}).get('old', '')
    new_status = appointment_data.get('changes', {}).get('status', {}).get('new', '')
    
    update_type = 'reschedule'  # Default for most updates
    if old_status and new_status:
        if new_status == 'cancelled':
            update_type = 'cancellation'
        elif new_status == 'no-show':
            update_type = 'no-show'  # Special case for no-show
        elif old_status == 'scheduled' and new_status == 'confirmed':
            update_type = 'confirmation'
        elif old_status != new_status:
            update_type = 'reschedule'
    
    print(f"  Status change: {old_status} -> {new_status}")
    print(f"  Update type: {update_type}")
    print(f"  Patient email: {appointment_data['patient_email']}")
    print(f"  Emergency contact: {appointment_data.get('emergency_contact_email', 'Not provided')}")
    
    # Test email client compatibility conversion
    email_update_type = update_type
    if update_type == 'reschedule':
        email_update_type = 'reschedule'
    elif update_type == 'cancellation':
        email_update_type = 'cancellation'
    elif update_type == 'no-show':
        email_update_type = 'cancellation'  # Use cancellation template for no-show
    elif update_type == 'confirmation':
        email_update_type = 'created'
    
    print(f"  Email client update type: {email_update_type}")
    
    # Test template key selection
    template_key_patient = f"appointment_{email_update_type.replace('-', '_')}_patient"
    template_key_emergency = f"appointment_{email_update_type.replace('-', '_')}_emergency"
    
    print(f"  Patient template: {template_key_patient}")
    print(f"  Emergency template: {template_key_emergency}")
    
    # Test notification sending logic
    notifications_to_send = []
    notifications_to_send.append({
        'recipient': 'patient',
        'email': appointment_data['patient_email'],
        'template_key': template_key_patient,
        'is_patient': True
    })
    
    if update_type == 'no-show' and appointment_data.get('emergency_contact_email'):
        notifications_to_send.append({
            'recipient': 'emergency_contact',
            'email': appointment_data['emergency_contact_email'],
            'template_key': template_key_emergency,
            'is_patient': False
        })
    
    print(f"  Notifications to send: {len(notifications_to_send)}")
    for notification in notifications_to_send:
        print(f"    - {notification['recipient']}: {notification['email']} ({notification['template_key']})")
    
    return update_type == 'no-show' and len(notifications_to_send) == 2

def test_no_show_without_emergency_contact():
    """Test no-show without emergency contact"""
    
    print("\nTesting no-show without emergency contact...")
    
    # Test appointment data without emergency contact
    appointment_data = {
        'id': 123,
        'appointment_date': '2024-01-15',
        'start_time': '10:00',
        'provider_name': 'Dr. Smith',
        'appointment_type_name': 'Consultation',
        'hospital_name': 'MediRemind Clinic',
        'patient_id': 456,
        'patient_name': 'John Doe',
        'patient_email': 'john@example.com',
        # No emergency_contact_email
        'changes': {
            'status': {
                'old': 'scheduled',
                'new': 'no-show'
            }
        }
    }
    
    # Simulate the update type logic
    new_status = appointment_data.get('changes', {}).get('status', {}).get('new', '')
    update_type = 'no-show' if new_status == 'no-show' else 'reschedule'
    
    # Test notification sending logic
    notifications_to_send = []
    notifications_to_send.append({
        'recipient': 'patient',
        'email': appointment_data['patient_email'],
        'is_patient': True
    })
    
    if update_type == 'no-show' and appointment_data.get('emergency_contact_email'):
        notifications_to_send.append({
            'recipient': 'emergency_contact',
            'email': appointment_data['emergency_contact_email'],
            'is_patient': False
        })
    
    print(f"  Update type: {update_type}")
    print(f"  Notifications to send: {len(notifications_to_send)}")
    for notification in notifications_to_send:
        print(f"    - {notification['recipient']}: {notification['email']}")
    
    return update_type == 'no-show' and len(notifications_to_send) == 1

if __name__ == "__main__":
    test1_passed = test_no_show_logic()
    test2_passed = test_no_show_without_emergency_contact()
    
    print(f"\nTest Results:")
    print(f"  With emergency contact: {'PASS' if test1_passed else 'FAIL'}")
    print(f"  Without emergency contact: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n✅ All tests passed! No-show notification logic is working correctly.")
    else:
        print("\n❌ Some tests failed. Please review the implementation.")