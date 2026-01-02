# API Integration

This module provides a secure, KDPA-compliant API interface for Hospital Management Systems (HMS) to integrate with Mediremind's automatic appointment reminder system.

## Features

### Security & Compliance
- **KDPA Compliance**: Full compliance with Kenya Data Protection Act requirements
- **HMAC Authentication**: Secure API key and signature-based authentication
- **Data Encryption**: All sensitive data encrypted using Fernet encryption
- **Audit Logging**: Complete audit trail of all API activities
- **Rate Limiting**: Protection against abuse and DDoS attacks
- **Consent Management**: Explicit consent required for all data processing

### API Endpoints

#### Authentication
- `POST /api/integration/auth/setup/` - Create new hospital integration
- `POST /api/integration/auth/verify/` - Verify API key
- `POST /api/integration/auth/rotate-key/` - Rotate API key

#### Data Processing
- `GET/POST /api/integration/patients/` - Patient data operations
- `GET/POST /api/integration/appointments/` - Appointment data operations
- `GET /api/integration/reminders/` - Reminder data retrieval

#### Consent Management
- `POST /api/integration/consents/request/` - Request consent
- `GET /api/integration/consents/verify/` - Verify consent status
- `POST /api/integration/consents/withdraw/` - Withdraw consent

#### Compliance
- `GET /api/integration/compliance/status/` - Get compliance status
- `GET /api/integration/compliance/report/` - Generate compliance report

### Key Components

#### Models
- `HospitalIntegration` - Manages hospital API integrations
- `DataProcessingConsent` - Tracks data processing consents
- `APILog` - Logs all API activities
- `SecurityIncident` - Tracks security incidents
- `DataEncryption` - Handles data encryption/decryption

#### Security Features
- HMAC signature verification
- Rate limiting with Redis
- IP-based access control
- Data encryption at rest
- Automated security incident detection

#### Compliance Features
- Data retention policies (7-year minimum)
- Consent expiry and renewal
- Automated compliance maintenance
- ODPC reporting capabilities
- Breach notification system

### Usage

1. **Setup Integration**: Use the setup endpoint to create a new integration
2. **Authentication**: Include API key and HMAC signature in all requests
3. **Consent Management**: Request and manage consents before processing data
4. **Data Operations**: Use patient and appointment endpoints for data exchange
5. **Compliance Monitoring**: Regularly check compliance status and reports

### Testing

Run the test suite:
```bash
python manage.py test api_integration
```

### Documentation

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for detailed API documentation with examples.

### Compliance

This module ensures full compliance with:
- Kenya Data Protection Act (KDPA)
- Office of Data Protection Commissioner (ODPC) requirements
- Healthcare data protection standards
- International data protection best practices