# API Integration Documentation

## Overview

The Mediremind API Integration provides a secure, KDPA-compliant interface for Hospital Management Systems (HMS) to integrate with our automatic appointment reminder system. This API enables hospitals to:

- Send patient and appointment data securely
- Manage consent for data processing
- Track compliance with Kenya Data Protection Act (KDPA)
- Monitor API usage and security incidents
- Generate compliance reports

## Security Features

### 1. Authentication & Authorization
- **API Key Authentication**: Each hospital receives a unique API key and secret
- **HMAC Signature Verification**: All requests must include HMAC signatures for integrity
- **Rate Limiting**: Prevents abuse with configurable rate limits per integration
- **Role-Based Access Control**: Different permission levels for hospital admins and system administrators

### 2. Data Protection
- **Encryption**: All sensitive data is encrypted using Fernet encryption
- **Data Minimization**: Only necessary data is collected and processed
- **Audit Logging**: Complete audit trail of all API activities
- **Consent Management**: Explicit consent required for all data processing activities

### 3. KDPA Compliance
- **Data Retention Policies**: Configurable retention periods (default: 7 years)
- **Right to Access**: Patients can access their data through hospital systems
- **Right to Deletion**: Data can be deleted upon request or after retention period
- **Breach Notification**: Automated security incident reporting
- **ODPC Registration**: Compliance reporting for Office of Data Protection Commissioner

## API Endpoints

### Authentication Endpoints

#### 1. Hospital Integration Setup
```http
POST /api/integration/auth/setup/
```

Creates a new hospital integration with API credentials.

**Request Body:**
```json
{
  "hospital_name": "Nairobi Hospital",
  "hospital_type": "private",
  "contact_email": "admin@nairobihospital.co.ke",
  "contact_phone": "+254700123456",
  "data_retention_days": 2555,
  "encryption_enabled": true
}
```

**Response:**
```json
{
  "status": "success",
  "integration_id": "550e8400-e29b-41d4-a716-446655440000",
  "api_key": "your-api-key-here",
  "message": "Integration created successfully. Please store the API key securely."
}
```

#### 2. Verify API Key
```http
POST /api/integration/auth/verify/
```

Verifies an API key and returns integration details.

**Request Body:**
```json
{
  "api_key": "your-api-key-here"
}
```

**Response:**
```json
{
  "status": "valid",
  "integration_id": "550e8400-e29b-41d4-a716-446655440000",
  "hospital_name": "Nairobi Hospital",
  "status": "active",
  "encryption_enabled": true
}
```

#### 3. Rotate API Key
```http
POST /api/integration/auth/rotate-key/
```

Rotates the API key for enhanced security.

**Request Body:**
```json
{
  "integration_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**
```json
{
  "status": "success",
  "new_api_key": "your-new-api-key-here",
  "message": "API key rotated successfully. Update your systems immediately."
}
```

### Data Processing Endpoints

#### 1. Patient Data
```http
GET /api/integration/patients/
POST /api/integration/patients/
```

**GET Parameters:**
- `patient_id` (optional): Filter by specific patient ID

**POST Request Body:**
```json
{
  "patient_id": "PAT001",
  "name": "John Doe",
  "phone": "+254700123456",
  "email": "john.doe@email.com",
  "date_of_birth": "1980-01-15"
}
```

#### 2. Appointment Data
```http
GET /api/integration/appointments/
POST /api/integration/appointments/
```

**GET Parameters:**
- `start_date` (optional): Filter appointments from this date (YYYY-MM-DD)
- `end_date` (optional): Filter appointments until this date (YYYY-MM-DD)

**POST Request Body:**
```json
{
  "patient_id": "PAT001",
  "appointment_date": "2024-01-15T14:30:00Z",
  "doctor_name": "Dr. Smith",
  "department": "Cardiology",
  "appointment_type": "consultation",
  "send_reminder": true,
  "reminder_time": "2024-01-14T08:00:00Z"
}
```

#### 3. Reminder Data
```http
GET /api/integration/reminders/
```

**GET Parameters:**
- `status` (optional): Filter by reminder status (pending, sent, failed)

### Consent Management Endpoints

#### 1. Request Consent
```http
POST /api/integration/consents/request/
```

**Request Body:**
```json
{
  "consent_type": "patient_data"
}
```

**Consent Types:**
- `patient_data`: Processing of patient personal information
- `appointment_data`: Processing of appointment scheduling data
- `reminder_data`: Processing of reminder notifications

#### 2. Verify Consent
```http
GET /api/integration/consents/verify/?consent_type=patient_data
```

#### 3. Withdraw Consent
```http
POST /api/integration/consents/withdraw/
```

**Request Body:**
```json
{
  "consent_type": "patient_data"
}
```

### Compliance Endpoints

#### 1. Compliance Status
```http
GET /api/integration/compliance/status/
```

**Response:**
```json
{
  "integration_status": "active",
  "data_retention_days": 2555,
  "encryption_enabled": true,
  "consents": {
    "total": 3,
    "active": 3,
    "expired": 0,
    "withdrawn": 0
  },
  "security_incidents": {
    "recent_30_days": 0,
    "high_severity": 0,
    "medium_severity": 0,
    "low_severity": 0
  },
  "api_usage": {
    "recent_30_days": 1250,
    "successful_calls": 1245,
    "failed_calls": 5
  },
  "compliance_score": 100
}
```

#### 2. Compliance Report
```http
GET /api/integration/compliance/report/
```

**Response:**
```json
{
  "report_date": "2024-01-01T00:00:00Z",
  "report_period": "monthly",
  "integrations": {
    "Nairobi Hospital": {
      "status": "active",
      "api_calls": 1250,
      "security_incidents": 0,
      "expired_consents": 0,
      "data_retention_days": 2555,
      "encryption_enabled": true
    }
  },
  "summary": {
    "total_integrations": 1,
    "active_integrations": 1,
    "total_api_calls": 1250,
    "security_incidents": 0,
    "consent_issues": 0
  }
}
```

## Request Authentication

All API requests must include proper authentication headers:

### Required Headers
```http
X-API-Key: your-api-key-here
X-Timestamp: 1704067200
X-Signature: hmac-sha256-signature-here
```

### Signature Generation

The signature is generated using HMAC-SHA256:

```python
import hmac
import hashlib
import time

# Generate timestamp
timestamp = str(int(time.time()))

# Create signature
payload = f"{timestamp}:{request_body}"
signature = hmac.new(
    api_secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()
```

### Example Request

```python
import requests
import hmac
import hashlib
import time
import json

# API credentials
api_key = "your-api-key-here"
api_secret = "your-api-secret-here"

# Request data
url = "https://your-domain.com/api/integration/patients/"
method = "GET"
request_body = ""  # Empty for GET requests

# Generate timestamp and signature
timestamp = str(int(time.time()))
payload = f"{timestamp}:{request_body}"
signature = hmac.new(
    api_secret.encode(),
    payload.encode(),
    hashlib.sha256
).hexdigest()

# Make request
headers = {
    "X-API-Key": api_key,
    "X-Timestamp": timestamp,
    "X-Signature": signature,
    "Content-Type": "application/json"
}

response = requests.get(url, headers=headers)
print(response.json())
```

## Error Handling

### Standard Error Response
```json
{
  "error": "Invalid API key",
  "error_code": "AUTH_INVALID_KEY",
  "timestamp": "2024-01-01T00:00:00Z",
  "request_id": "req_1234567890"
}
```

### Common Error Codes
- `AUTH_INVALID_KEY`: Invalid API key
- `AUTH_INVALID_SIGNATURE`: Invalid HMAC signature
- `AUTH_RATE_LIMITED`: Rate limit exceeded
- `CONSENT_REQUIRED`: No valid consent for requested operation
- `CONSENT_EXPIRED`: Consent has expired
- `DATA_NOT_FOUND`: Requested data not found
- `VALIDATION_ERROR`: Request validation failed
- `SERVER_ERROR`: Internal server error

## Rate Limiting

- **Standard Limit**: 1000 requests per hour per integration
- **Burst Limit**: 100 requests per minute
- **Headers**: Rate limit information included in response headers

**Rate Limit Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1704067200
```

## Data Retention

- **Patient Data**: 7 years (2555 days) by default
- **Appointment Data**: 7 years (2555 days) by default
- **Audit Logs**: 7 years minimum for compliance
- **Consent Records**: Permanent retention for audit purposes

## Compliance Features

### 1. Audit Logging
All API activities are logged with:
- Timestamp and IP address
- Authentication status
- Data categories accessed
- Request/response details (sanitized)

### 2. Consent Management
- Explicit consent required for all data processing
- Granular consent types (patient data, appointments, reminders)
- Consent expiry and renewal notifications
- Withdrawal mechanisms

### 3. Data Breach Response
- Automated security incident detection
- Breach notification within 72 hours (KDPA requirement)
- Incident severity classification
- Remediation tracking

### 4. ODPC Reporting
- Monthly compliance reports
- Data processing activity summaries
- Security incident statistics
- Consent management metrics

## Best Practices

### 1. Security
- Store API credentials securely (environment variables, secure vaults)
- Rotate API keys regularly (recommended: quarterly)
- Use HTTPS for all API communications
- Implement request timeout handling
- Monitor API usage for anomalies

### 2. Data Handling
- Only send necessary data fields
- Implement data validation on your end
- Handle consent expiry gracefully
- Respect data retention policies
- Implement proper error handling

### 3. Integration
- Test in development environment first
- Implement exponential backoff for retries
- Log API interactions for debugging
- Monitor compliance status regularly
- Keep integration documentation updated

## Support

For technical support or compliance questions:
- **Email**: support@mediremind.co.ke
- **Phone**: +254 700 123 456
- **Documentation**: https://docs.mediremind.co.ke
- **Status Page**: https://status.mediremind.co.ke

## Changelog

### Version 1.0.0 (January 2024)
- Initial API release
- KDPA compliance features
- Basic authentication and authorization
- Patient and appointment data endpoints
- Consent management system
- Compliance reporting

---

*This API documentation is compliant with Kenya Data Protection Act (KDPA) requirements and is regularly updated to reflect changes in regulations and best practices.*