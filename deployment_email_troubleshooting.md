# Email Deployment Troubleshooting Guide

## Problem Analysis

Based on the error logs, the issue is a **network connectivity problem** on the deployed server:

```
Error sending email: [Errno 101] Network is unreachable
```

This error indicates that the deployed server cannot establish network connections to external SMTP servers.

## Root Causes

### 1. **Render.com Network Restrictions**
- Render.com's free tier may have outbound network restrictions
- SMTP ports (587, 465, 25) might be blocked for security reasons
- Firewall rules preventing external SMTP connections

### 2. **Gmail SMTP Limitations**
- Gmail SMTP requires "Less secure app access" or App Passwords
- May have rate limiting or IP-based restrictions
- Not ideal for production transactional emails

### 3. **SSL/TLS Configuration Issues**
- Certificate verification problems in containerized environments
- Network policies interfering with SSL handshakes

## Solutions Implemented

### 1. **Enhanced Email Service Configuration**
Added support for multiple email providers in `settings.py`:

- **SendGrid** (Recommended for production)
- **Mailgun** (Good alternative)
- **AWS SES** (If using AWS infrastructure)
- **Gmail SMTP** (Fallback)

### 2. **Improved Network Diagnostics**
Enhanced `email_client.py` with:
- DNS resolution testing
- Port connectivity checks
- Better error logging
- SSL context configuration options

### 3. **Environment Variable Configuration**
Set `EMAIL_SERVICE` environment variable to choose provider:

```bash
# For SendGrid
EMAIL_SERVICE=sendgrid
SENDGRID_API_KEY=your_sendgrid_api_key

# For Mailgun
EMAIL_SERVICE=mailgun
MAILGUN_SMTP_LOGIN=your_mailgun_login
MAILGUN_SMTP_PASSWORD=your_mailgun_password

# For AWS SES
EMAIL_SERVICE=aws_ses
AWS_SES_SMTP_USERNAME=your_ses_username
AWS_SES_SMTP_PASSWORD=your_ses_password
AWS_REGION=us-east-1
```

## Recommended Actions

### Immediate Fix (Recommended)
1. **Switch to SendGrid**:
   - Sign up at https://sendgrid.com/
   - Get API key from dashboard
   - Set environment variables in Render:
     ```
     EMAIL_SERVICE=sendgrid
     SENDGRID_API_KEY=your_api_key_here
     ```

### Alternative Solutions
2. **Use Mailgun**:
   - Sign up at https://www.mailgun.com/
   - Get SMTP credentials
   - Set environment variables

3. **Contact Render Support**:
   - Ask about SMTP port restrictions
   - Request whitelist for smtp.gmail.com:587

### Testing Network Connectivity
Add this environment variable for debugging:
```
EMAIL_SSL_PERMISSIVE=true
```

## Why This Happens on Render.com

1. **Security Policies**: Cloud platforms often restrict outbound SMTP to prevent spam
2. **Network Isolation**: Containers may have limited network access
3. **Port Blocking**: Common SMTP ports are frequently blocked
4. **IP Reputation**: Shared infrastructure IPs may be blacklisted

## Best Practices for Production Email

1. **Use Transactional Email Services**: SendGrid, Mailgun, AWS SES
2. **Avoid Gmail SMTP**: Not designed for application email sending
3. **Implement Retry Logic**: Handle temporary failures gracefully
4. **Monitor Email Delivery**: Track bounces and delivery rates
5. **Use Dedicated IPs**: For high-volume sending

## Environment Variables Summary

```bash
# Choose your email service
EMAIL_SERVICE=sendgrid  # or mailgun, aws_ses, smtp

# SendGrid
SENDGRID_API_KEY=your_sendgrid_api_key

# Mailgun
MAILGUN_SMTP_LOGIN=your_mailgun_login
MAILGUN_SMTP_PASSWORD=your_mailgun_password

# AWS SES
AWS_SES_SMTP_USERNAME=your_ses_username
AWS_SES_SMTP_PASSWORD=your_ses_password
AWS_REGION=us-east-1

# Gmail (fallback)
EMAIL_HOST_USER=your_gmail@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# Optional debugging
EMAIL_SSL_PERMISSIVE=true  # Only for debugging
```

## Next Steps

1. Set up SendGrid account and get API key
2. Add environment variables to Render deployment
3. Redeploy the application
4. Test email functionality
5. Monitor logs for successful email delivery