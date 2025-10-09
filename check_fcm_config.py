import os

# Check FCM configuration
fcm_v1 = os.getenv('FCM_USE_V1', 'false')
project_id = os.getenv('FCM_PROJECT_ID')
credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

print(f'FCM_USE_V1: {fcm_v1}')
print(f'FCM_PROJECT_ID: {project_id}')
print(f'GOOGLE_APPLICATION_CREDENTIALS: {credentials_path}')

# Check if credentials file exists
if credentials_path:
    import os.path
    file_exists = os.path.isfile(credentials_path)
    print(f'Credentials file exists: {file_exists}')
    if file_exists:
        import json
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
                print(f'Credentials type: {creds.get("type", "unknown")}')
                print(f'Project ID from credentials: {creds.get("project_id", "not found")}')
        except Exception as e:
            print(f'Error reading credentials: {e}')
else:
    print('No credentials path configured')

# Test FCM v1 configuration
if fcm_v1.lower() == 'true' and project_id and credentials_path:
    print('\n✅ FCM v1 is properly configured')
    print('The backend will use Firebase Admin SDK with service account credentials')
elif fcm_v1.lower() == 'false':
    print('\n⚠️  FCM v1 is disabled, using legacy FCM server key')
else:
    print('\n❌ FCM v1 configuration is incomplete')