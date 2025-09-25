#!/usr/bin/env python3
"""
MediRemind Backend - Credential Validation Script
Validates all external service credentials and configurations.
"""

import os
import sys
import json
import asyncio
import aiohttp
import smtplib
import ssl
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import redis
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    service: str
    status: str  # 'success', 'warning', 'error', 'not_configured'
    message: str
    details: Optional[Dict] = None

class CredentialValidator:
    def __init__(self):
        self.results: List[ValidationResult] = []
        self.load_environment()
    
    def load_environment(self):
        """Load environment variables from .env file if it exists."""
        env_file = '.env'
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value
    
    def add_result(self, service: str, status: str, message: str, details: Optional[Dict] = None):
        """Add a validation result."""
        self.results.append(ValidationResult(service, status, message, details))
        
        # Log the result
        log_level = {
            'success': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'not_configured': logging.WARNING
        }.get(status, logging.INFO)
        
        logger.log(log_level, f"{service}: {message}")
    
    def validate_required_env_var(self, var_name: str, service_name: str) -> bool:
        """Check if a required environment variable is set."""
        value = os.getenv(var_name)
        if not value or value in ['your_key_here', 'your_secret_here', 'your_token_here']:
            self.add_result(
                service_name,
                'not_configured',
                f"Environment variable {var_name} is not configured"
            )
            return False
        return True
    
    def validate_database_config(self):
        """Validate Supabase database configuration."""
        logger.info("Validating database configuration...")
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or 'your-project' in supabase_url:
            self.add_result(
                'Database',
                'not_configured',
                'Supabase URL is not configured'
            )
            return
        
        if not supabase_key or 'your_supabase' in supabase_key:
            self.add_result(
                'Database',
                'not_configured',
                'Supabase key is not configured'
            )
            return
        
        # Test connection (basic URL validation)
        if supabase_url.startswith('https://') and '.supabase.co' in supabase_url:
            self.add_result(
                'Database',
                'success',
                'Supabase configuration appears valid'
            )
        else:
            self.add_result(
                'Database',
                'error',
                'Invalid Supabase URL format'
            )
    
    async def validate_redis_config(self):
        """Validate Redis configuration."""
        logger.info("Validating Redis configuration...")
        
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            self.add_result(
                'Redis',
                'not_configured',
                'Redis URL is not configured'
            )
            return
        
        try:
            # Test Redis connection
            r = redis.from_url(redis_url, socket_connect_timeout=5)
            r.ping()
            self.add_result(
                'Redis',
                'success',
                'Redis connection successful'
            )
        except redis.ConnectionError as e:
            self.add_result(
                'Redis',
                'error',
                f'Redis connection failed: {str(e)}'
            )
        except Exception as e:
            self.add_result(
                'Redis',
                'error',
                f'Redis validation error: {str(e)}'
            )
    
    def validate_vapid_keys(self):
        """Validate VAPID keys for web push notifications."""
        logger.info("Validating VAPID keys...")
        
        public_key = os.getenv('VAPID_PUBLIC_KEY')
        private_key = os.getenv('VAPID_PRIVATE_KEY')
        admin_email = os.getenv('VAPID_ADMIN_EMAIL')
        
        if not public_key or 'your_vapid' in public_key:
            self.add_result(
                'VAPID Keys',
                'not_configured',
                'VAPID public key is not configured'
            )
            return
        
        if not private_key or 'your_vapid' in private_key:
            self.add_result(
                'VAPID Keys',
                'not_configured',
                'VAPID private key is not configured'
            )
            return
        
        if not admin_email or '@yourdomain.com' in admin_email:
            self.add_result(
                'VAPID Keys',
                'not_configured',
                'VAPID admin email is not configured'
            )
            return
        
        # Basic validation of key format
        if len(public_key) >= 80 and len(private_key) >= 40:
            self.add_result(
                'VAPID Keys',
                'success',
                'VAPID keys appear to be properly configured'
            )
        else:
            self.add_result(
                'VAPID Keys',
                'error',
                'VAPID keys appear to have invalid format'
            )
    
    async def validate_sendgrid_config(self):
        """Validate SendGrid email configuration."""
        logger.info("Validating SendGrid configuration...")
        
        api_key = os.getenv('SENDGRID_API_KEY')
        from_email = os.getenv('SENDGRID_FROM_EMAIL')
        
        if not api_key or 'your_sendgrid' in api_key:
            self.add_result(
                'SendGrid',
                'not_configured',
                'SendGrid API key is not configured'
            )
            return
        
        if not from_email or '@yourdomain.com' in from_email:
            self.add_result(
                'SendGrid',
                'not_configured',
                'SendGrid from email is not configured'
            )
            return
        
        # Test SendGrid API
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    'https://api.sendgrid.com/v3/user/profile',
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        self.add_result(
                            'SendGrid',
                            'success',
                            'SendGrid API key is valid'
                        )
                    elif response.status == 401:
                        self.add_result(
                            'SendGrid',
                            'error',
                            'SendGrid API key is invalid'
                        )
                    else:
                        self.add_result(
                            'SendGrid',
                            'warning',
                            f'SendGrid API returned status {response.status}'
                        )
        except asyncio.TimeoutError:
            self.add_result(
                'SendGrid',
                'warning',
                'SendGrid API validation timed out'
            )
        except Exception as e:
            self.add_result(
                'SendGrid',
                'error',
                f'SendGrid validation error: {str(e)}'
            )
    
    def validate_smtp_config(self):
        """Validate SMTP configuration."""
        logger.info("Validating SMTP configuration...")
        
        host = os.getenv('SMTP_HOST')
        port = os.getenv('SMTP_PORT', '587')
        username = os.getenv('SMTP_USERNAME')
        password = os.getenv('SMTP_PASSWORD')
        
        if not all([host, username, password]):
            self.add_result(
                'SMTP',
                'not_configured',
                'SMTP configuration is incomplete'
            )
            return
        
        try:
            # Test SMTP connection
            context = ssl.create_default_context()
            with smtplib.SMTP(host, int(port), timeout=10) as server:
                server.starttls(context=context)
                server.login(username, password)
                self.add_result(
                    'SMTP',
                    'success',
                    'SMTP connection and authentication successful'
                )
        except smtplib.SMTPAuthenticationError:
            self.add_result(
                'SMTP',
                'error',
                'SMTP authentication failed - check username/password'
            )
        except smtplib.SMTPException as e:
            self.add_result(
                'SMTP',
                'error',
                f'SMTP error: {str(e)}'
            )
        except Exception as e:
            self.add_result(
                'SMTP',
                'error',
                f'SMTP validation error: {str(e)}'
            )
    
    def validate_fcm_config(self):
        """Validate Firebase Cloud Messaging configuration."""
        logger.info("Validating FCM configuration...")
        
        server_key = os.getenv('FCM_SERVER_KEY')
        project_id = os.getenv('FCM_PROJECT_ID')
        
        if not server_key or 'your_fcm' in server_key:
            self.add_result(
                'FCM',
                'not_configured',
                'FCM server key is not configured'
            )
            return
        
        if not project_id or 'your_firebase' in project_id:
            self.add_result(
                'FCM',
                'not_configured',
                'FCM project ID is not configured'
            )
            return
        
        # Basic validation
        if server_key.startswith('AAAA') and len(server_key) > 100:
            self.add_result(
                'FCM',
                'success',
                'FCM configuration appears valid'
            )
        else:
            self.add_result(
                'FCM',
                'warning',
                'FCM server key format may be invalid'
            )
    
    def validate_aws_config(self):
        """Validate AWS S3 configuration."""
        logger.info("Validating AWS configuration...")
        
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        bucket = os.getenv('AWS_S3_BUCKET')
        
        if not access_key or 'your_aws' in access_key:
            self.add_result(
                'AWS S3',
                'not_configured',
                'AWS access key is not configured'
            )
            return
        
        if not secret_key or 'your_aws' in secret_key:
            self.add_result(
                'AWS S3',
                'not_configured',
                'AWS secret key is not configured'
            )
            return
        
        if not bucket or 'your_s3' in bucket:
            self.add_result(
                'AWS S3',
                'not_configured',
                'AWS S3 bucket is not configured'
            )
            return
        
        # Basic format validation
        if len(access_key) == 20 and len(secret_key) == 40:
            self.add_result(
                'AWS S3',
                'success',
                'AWS credentials appear to have correct format'
            )
        else:
            self.add_result(
                'AWS S3',
                'warning',
                'AWS credentials may have invalid format'
            )
    
    def validate_security_config(self):
        """Validate security configuration."""
        logger.info("Validating security configuration...")
        
        secret_key = os.getenv('SECRET_KEY')
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        field_encryption_key = os.getenv('FIELD_ENCRYPTION_KEY')
        
        if not secret_key or secret_key == 'your_secret_key_here':
            self.add_result(
                'Security',
                'error',
                'Django SECRET_KEY is not configured'
            )
        elif len(secret_key) < 32:
            self.add_result(
                'Security',
                'warning',
                'Django SECRET_KEY is too short (should be at least 32 characters)'
            )
        else:
            self.add_result(
                'Security',
                'success',
                'Django SECRET_KEY is properly configured'
            )
        
        if not jwt_secret or jwt_secret == 'your_jwt_secret_key_here':
            self.add_result(
                'Security',
                'error',
                'JWT secret key is not configured'
            )
        elif len(jwt_secret) < 32:
            self.add_result(
                'Security',
                'warning',
                'JWT secret key is too short'
            )
        
        if field_encryption_key and len(field_encryption_key) == 44:
            self.add_result(
                'Security',
                'success',
                'Field encryption key is properly configured'
            )
        elif not field_encryption_key:
            self.add_result(
                'Security',
                'warning',
                'Field encryption key is not configured'
            )
    
    async def run_all_validations(self):
        """Run all credential validations."""
        logger.info("Starting credential validation...")
        
        # Database validation
        self.validate_database_config()
        
        # Redis validation
        await self.validate_redis_config()
        
        # Notification services
        self.validate_vapid_keys()
        await self.validate_sendgrid_config()
        self.validate_smtp_config()
        self.validate_fcm_config()
        
        # Cloud storage
        self.validate_aws_config()
        
        # Security
        self.validate_security_config()
        
        logger.info("Credential validation completed")
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive validation report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_services': len(self.results),
                'success': len([r for r in self.results if r.status == 'success']),
                'warnings': len([r for r in self.results if r.status == 'warning']),
                'errors': len([r for r in self.results if r.status == 'error']),
                'not_configured': len([r for r in self.results if r.status == 'not_configured'])
            },
            'results': [
                {
                    'service': r.service,
                    'status': r.status,
                    'message': r.message,
                    'details': r.details
                }
                for r in self.results
            ]
        }
        
        return report
    
    def print_report(self):
        """Print a formatted validation report."""
        print("\n" + "="*80)
        print("MEDIREMIND CREDENTIAL VALIDATION REPORT")
        print("="*80)
        
        # Summary
        summary = {
            'success': len([r for r in self.results if r.status == 'success']),
            'warnings': len([r for r in self.results if r.status == 'warning']),
            'errors': len([r for r in self.results if r.status == 'error']),
            'not_configured': len([r for r in self.results if r.status == 'not_configured'])
        }
        
        print(f"\nSUMMARY:")
        print(f"  ✅ Success: {summary['success']}")
        print(f"  ⚠️  Warnings: {summary['warnings']}")
        print(f"  ❌ Errors: {summary['errors']}")
        print(f"  ⚪ Not Configured: {summary['not_configured']}")
        
        # Detailed results
        print(f"\nDETAILED RESULTS:")
        print("-" * 80)
        
        status_icons = {
            'success': '✅',
            'warning': '⚠️',
            'error': '❌',
            'not_configured': '⚪'
        }
        
        for result in self.results:
            icon = status_icons.get(result.status, '❓')
            print(f"{icon} {result.service}: {result.message}")
        
        print("\n" + "="*80)
        
        # Recommendations
        errors = [r for r in self.results if r.status == 'error']
        not_configured = [r for r in self.results if r.status == 'not_configured']
        
        if errors or not_configured:
            print("RECOMMENDATIONS:")
            print("-" * 80)
            
            if not_configured:
                print("\n🔧 CONFIGURATION NEEDED:")
                for result in not_configured:
                    print(f"   • {result.service}: {result.message}")
            
            if errors:
                print("\n🚨 CRITICAL ISSUES:")
                for result in errors:
                    print(f"   • {result.service}: {result.message}")
            
            print("\n📝 Next steps:")
            print("   1. Copy .env.example to .env")
            print("   2. Fill in the required credentials")
            print("   3. Run this script again to verify")
            print("   4. Check the documentation for service setup guides")
        else:
            print("🎉 All credentials are properly configured!")
        
        print("\n" + "="*80)

async def main():
    """Main function to run credential validation."""
    validator = CredentialValidator()
    
    try:
        await validator.run_all_validations()
        
        # Generate and save report
        report = validator.generate_report()
        
        # Save JSON report
        with open('credential_validation_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print formatted report
        validator.print_report()
        
        # Exit with appropriate code
        errors = len([r for r in validator.results if r.status == 'error'])
        sys.exit(1 if errors > 0 else 0)
        
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Validation failed with error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())