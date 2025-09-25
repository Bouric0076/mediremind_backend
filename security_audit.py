#!/usr/bin/env python3
"""
MediRemind Backend - Security Audit Script
Performs comprehensive security checks for the application.
"""

import os
import re
import json
import hashlib
import secrets
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class SecurityIssue:
    category: str
    severity: str  # 'critical', 'high', 'medium', 'low', 'info'
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: Optional[str] = None

class SecurityAuditor:
    def __init__(self):
        self.issues: List[SecurityIssue] = []
        self.project_root = Path.cwd()
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
    
    def add_issue(self, category: str, severity: str, title: str, description: str, 
                  file_path: Optional[str] = None, line_number: Optional[int] = None,
                  recommendation: Optional[str] = None):
        """Add a security issue."""
        self.issues.append(SecurityIssue(
            category=category,
            severity=severity,
            title=title,
            description=description,
            file_path=file_path,
            line_number=line_number,
            recommendation=recommendation
        ))
        
        # Log the issue
        log_level = {
            'critical': logging.CRITICAL,
            'high': logging.ERROR,
            'medium': logging.WARNING,
            'low': logging.INFO,
            'info': logging.INFO
        }.get(severity, logging.INFO)
        
        location = f" in {file_path}:{line_number}" if file_path and line_number else ""
        logger.log(log_level, f"{severity.upper()}: {title}{location}")
    
    def audit_environment_variables(self):
        """Audit environment variables for security issues."""
        logger.info("Auditing environment variables...")
        
        # Check for weak secret keys
        secret_key = os.getenv('SECRET_KEY')
        if secret_key:
            if len(secret_key) < 32:
                self.add_issue(
                    'Configuration',
                    'high',
                    'Weak SECRET_KEY',
                    f'SECRET_KEY is only {len(secret_key)} characters long',
                    recommendation='Use a secret key of at least 50 characters'
                )
            elif 'django-insecure' in secret_key:
                self.add_issue(
                    'Configuration',
                    'critical',
                    'Insecure SECRET_KEY',
                    'SECRET_KEY contains "django-insecure" prefix',
                    recommendation='Generate a new secure secret key'
                )
        
        # Check JWT secret
        jwt_secret = os.getenv('JWT_SECRET_KEY')
        if jwt_secret and len(jwt_secret) < 32:
            self.add_issue(
                'Configuration',
                'high',
                'Weak JWT Secret',
                f'JWT_SECRET_KEY is only {len(jwt_secret)} characters long',
                recommendation='Use a JWT secret of at least 50 characters'
            )
        
        # Check for debug mode in production
        debug = os.getenv('DEBUG', '').lower()
        environment = os.getenv('ENVIRONMENT', 'development').lower()
        if debug == 'true' and environment == 'production':
            self.add_issue(
                'Configuration',
                'critical',
                'Debug Mode in Production',
                'DEBUG=True is set in production environment',
                recommendation='Set DEBUG=False in production'
            )
        
        # Check for default/weak passwords
        weak_patterns = [
            'password', 'admin', 'test', '123456', 'default',
            'your_password', 'your_key', 'changeme'
        ]
        
        for key, value in os.environ.items():
            if any(pattern in key.lower() for pattern in ['password', 'secret', 'key', 'token']):
                if any(weak in value.lower() for weak in weak_patterns):
                    self.add_issue(
                        'Configuration',
                        'high',
                        'Weak Credential',
                        f'Environment variable {key} contains weak/default value',
                        recommendation='Use strong, unique credentials'
                    )
    
    def audit_file_permissions(self):
        """Audit file permissions for security issues."""
        logger.info("Auditing file permissions...")
        
        sensitive_files = [
            '.env',
            '.env.production',
            'private_key.pem',
            'ssl/key.pem',
            'credentials.json'
        ]
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                # On Windows, we'll check if the file exists and warn about permissions
                self.add_issue(
                    'File Security',
                    'medium',
                    'Sensitive File Present',
                    f'Sensitive file {file_path} found',
                    file_path=file_path,
                    recommendation='Ensure file has restricted permissions and is not committed to version control'
                )
    
    def audit_code_patterns(self):
        """Audit code for security anti-patterns."""
        logger.info("Auditing code patterns...")
        
        # Patterns to look for
        security_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', 'high', 'Hardcoded Password'),
            (r'api_key\s*=\s*["\'][^"\']+["\']', 'high', 'Hardcoded API Key'),
            (r'secret\s*=\s*["\'][^"\']+["\']', 'high', 'Hardcoded Secret'),
            (r'token\s*=\s*["\'][^"\']+["\']', 'medium', 'Hardcoded Token'),
            (r'eval\s*\(', 'critical', 'Use of eval()'),
            (r'exec\s*\(', 'critical', 'Use of exec()'),
            (r'shell=True', 'high', 'Shell Injection Risk'),
            (r'pickle\.loads?', 'high', 'Pickle Deserialization'),
            (r'yaml\.load\s*\(', 'medium', 'Unsafe YAML Loading'),
            (r'sql\s*=.*%', 'high', 'SQL Injection Risk'),
            (r'cursor\.execute.*%', 'high', 'SQL Injection Risk'),
            (r'os\.system', 'high', 'Command Injection Risk'),
            (r'subprocess\.call.*shell=True', 'high', 'Command Injection Risk'),
        ]
        
        # File extensions to check
        code_extensions = ['.py', '.js', '.ts', '.jsx', '.tsx']
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip certain directories
            skip_dirs = {'.git', '.venv', 'node_modules', '__pycache__', '.pytest_cache'}
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in code_extensions):
                    file_path = os.path.join(root, file)
                    self._audit_file_content(file_path, security_patterns)
    
    def _audit_file_content(self, file_path: str, patterns: List[Tuple[str, str, str]]):
        """Audit a single file for security patterns."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                for pattern, severity, title in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip comments and test files
                        if line.strip().startswith('#') or 'test' in file_path.lower():
                            continue
                            
                        self.add_issue(
                            'Code Security',
                            severity,
                            title,
                            f'Potential security issue found: {line.strip()}',
                            file_path=file_path,
                            line_number=line_num,
                            recommendation=f'Review and secure this {title.lower()}'
                        )
        except Exception as e:
            logger.warning(f"Could not audit file {file_path}: {e}")
    
    def audit_dependencies(self):
        """Audit dependencies for known vulnerabilities."""
        logger.info("Auditing dependencies...")
        
        # Check requirements.txt
        requirements_file = 'requirements.txt'
        if os.path.exists(requirements_file):
            with open(requirements_file, 'r') as f:
                requirements = f.read()
                
            # Known vulnerable packages (simplified check)
            vulnerable_patterns = [
                ('django<3.2', 'high', 'Outdated Django Version'),
                ('requests<2.20', 'medium', 'Outdated Requests Library'),
                ('pillow<8.3.2', 'high', 'Vulnerable Pillow Version'),
                ('pyyaml<5.4', 'medium', 'Vulnerable PyYAML Version'),
            ]
            
            for pattern, severity, title in vulnerable_patterns:
                if re.search(pattern.replace('<', r'[<>=]*'), requirements, re.IGNORECASE):
                    self.add_issue(
                        'Dependencies',
                        severity,
                        title,
                        f'Potentially vulnerable dependency: {pattern}',
                        file_path=requirements_file,
                        recommendation='Update to the latest secure version'
                    )
    
    def audit_django_settings(self):
        """Audit Django settings for security issues."""
        logger.info("Auditing Django settings...")
        
        settings_files = [
            'mediremind_backend/settings.py',
            'settings.py',
            'mediremind_backend/settings/production.py'
        ]
        
        for settings_file in settings_files:
            if os.path.exists(settings_file):
                self._audit_django_settings_file(settings_file)
    
    def _audit_django_settings_file(self, file_path: str):
        """Audit a Django settings file."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Security checks
            security_checks = [
                ('ALLOWED_HOSTS = []', 'high', 'Empty ALLOWED_HOSTS'),
                ('DEBUG = True', 'critical', 'Debug Mode Enabled'),
                ('SECURE_SSL_REDIRECT = False', 'medium', 'SSL Redirect Disabled'),
                ('SESSION_COOKIE_SECURE = False', 'medium', 'Insecure Session Cookies'),
                ('CSRF_COOKIE_SECURE = False', 'medium', 'Insecure CSRF Cookies'),
                ('X_FRAME_OPTIONS.*DENY', 'info', 'X-Frame-Options Set'),
            ]
            
            for pattern, severity, title in security_checks:
                if re.search(pattern, content, re.IGNORECASE):
                    if severity == 'info':
                        continue  # Skip positive findings
                    
                    self.add_issue(
                        'Django Security',
                        severity,
                        title,
                        f'Security setting issue in {file_path}',
                        file_path=file_path,
                        recommendation='Review and update Django security settings'
                    )
        except Exception as e:
            logger.warning(f"Could not audit Django settings {file_path}: {e}")
    
    def audit_database_security(self):
        """Audit database security configuration."""
        logger.info("Auditing database security...")
        
        # Check for database credentials in environment
        db_password = os.getenv('DB_PASSWORD')
        if db_password and len(db_password) < 12:
            self.add_issue(
                'Database Security',
                'medium',
                'Weak Database Password',
                f'Database password is only {len(db_password)} characters long',
                recommendation='Use a strong database password (at least 16 characters)'
            )
        
        # Check for SSL configuration
        db_ssl = os.getenv('DB_SSL_MODE', '').lower()
        if db_ssl in ['disable', 'allow']:
            self.add_issue(
                'Database Security',
                'medium',
                'Insecure Database Connection',
                'Database SSL mode is not set to require/verify',
                recommendation='Set DB_SSL_MODE to "require" or "verify-full"'
            )
    
    def audit_api_security(self):
        """Audit API security configuration."""
        logger.info("Auditing API security...")
        
        # Check CORS settings
        cors_origins = os.getenv('CORS_ORIGINS', '')
        if '*' in cors_origins:
            self.add_issue(
                'API Security',
                'high',
                'Permissive CORS Configuration',
                'CORS_ORIGINS allows all origins (*)',
                recommendation='Restrict CORS to specific trusted domains'
            )
        
        # Check rate limiting
        rate_limit_enabled = os.getenv('RATE_LIMIT_ENABLED', 'false').lower()
        if rate_limit_enabled != 'true':
            self.add_issue(
                'API Security',
                'medium',
                'Rate Limiting Disabled',
                'API rate limiting is not enabled',
                recommendation='Enable rate limiting to prevent abuse'
            )
    
    def run_full_audit(self):
        """Run all security audits."""
        logger.info("Starting comprehensive security audit...")
        
        self.audit_environment_variables()
        self.audit_file_permissions()
        self.audit_code_patterns()
        self.audit_dependencies()
        self.audit_django_settings()
        self.audit_database_security()
        self.audit_api_security()
        
        logger.info("Security audit completed")
    
    def generate_report(self) -> Dict:
        """Generate a comprehensive security audit report."""
        # Group issues by severity
        severity_counts = {}
        for issue in self.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        # Calculate security score (100 - weighted penalty)
        severity_weights = {'critical': 25, 'high': 10, 'medium': 5, 'low': 2, 'info': 0}
        total_penalty = sum(severity_weights.get(issue.severity, 0) for issue in self.issues)
        security_score = max(0, 100 - total_penalty)
        
        report = {
            'timestamp': str(Path.cwd()),
            'security_score': security_score,
            'summary': {
                'total_issues': len(self.issues),
                'critical': severity_counts.get('critical', 0),
                'high': severity_counts.get('high', 0),
                'medium': severity_counts.get('medium', 0),
                'low': severity_counts.get('low', 0),
                'info': severity_counts.get('info', 0)
            },
            'issues': [
                {
                    'category': issue.category,
                    'severity': issue.severity,
                    'title': issue.title,
                    'description': issue.description,
                    'file_path': issue.file_path,
                    'line_number': issue.line_number,
                    'recommendation': issue.recommendation
                }
                for issue in self.issues
            ]
        }
        
        return report
    
    def print_report(self):
        """Print a formatted security audit report."""
        print("\n" + "="*80)
        print("MEDIREMIND SECURITY AUDIT REPORT")
        print("="*80)
        
        # Calculate security score
        severity_weights = {'critical': 25, 'high': 10, 'medium': 5, 'low': 2, 'info': 0}
        total_penalty = sum(severity_weights.get(issue.severity, 0) for issue in self.issues)
        security_score = max(0, 100 - total_penalty)
        
        # Summary
        severity_counts = {}
        for issue in self.issues:
            severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
        
        print(f"\nSECURITY SCORE: {security_score}/100")
        
        if security_score >= 90:
            print("🟢 EXCELLENT - Very secure configuration")
        elif security_score >= 75:
            print("🟡 GOOD - Minor security improvements needed")
        elif security_score >= 50:
            print("🟠 FAIR - Several security issues to address")
        else:
            print("🔴 POOR - Critical security issues require immediate attention")
        
        print(f"\nSUMMARY:")
        print(f"  🔴 Critical: {severity_counts.get('critical', 0)}")
        print(f"  🟠 High: {severity_counts.get('high', 0)}")
        print(f"  🟡 Medium: {severity_counts.get('medium', 0)}")
        print(f"  🔵 Low: {severity_counts.get('low', 0)}")
        print(f"  ℹ️  Info: {severity_counts.get('info', 0)}")
        
        if not self.issues:
            print("\n🎉 No security issues found!")
            print("="*80)
            return
        
        # Group issues by severity
        severity_order = ['critical', 'high', 'medium', 'low', 'info']
        severity_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🔵',
            'info': 'ℹ️'
        }
        
        print(f"\nDETAILED FINDINGS:")
        print("-" * 80)
        
        for severity in severity_order:
            issues_of_severity = [i for i in self.issues if i.severity == severity]
            if not issues_of_severity:
                continue
                
            print(f"\n{severity_icons[severity]} {severity.upper()} SEVERITY:")
            for issue in issues_of_severity:
                location = ""
                if issue.file_path:
                    location = f" ({issue.file_path}"
                    if issue.line_number:
                        location += f":{issue.line_number}"
                    location += ")"
                
                print(f"  • {issue.title}{location}")
                print(f"    {issue.description}")
                if issue.recommendation:
                    print(f"    💡 {issue.recommendation}")
                print()
        
        print("="*80)
        
        # Recommendations
        critical_issues = [i for i in self.issues if i.severity == 'critical']
        high_issues = [i for i in self.issues if i.severity == 'high']
        
        if critical_issues or high_issues:
            print("🚨 IMMEDIATE ACTION REQUIRED:")
            print("-" * 80)
            
            if critical_issues:
                print("\n🔴 CRITICAL ISSUES (Fix immediately):")
                for issue in critical_issues[:5]:  # Show top 5
                    print(f"   • {issue.title}")
            
            if high_issues:
                print("\n🟠 HIGH PRIORITY ISSUES:")
                for issue in high_issues[:5]:  # Show top 5
                    print(f"   • {issue.title}")
            
            print("\n📝 Next steps:")
            print("   1. Address critical issues immediately")
            print("   2. Review and fix high priority issues")
            print("   3. Implement security best practices")
            print("   4. Run this audit regularly")
        
        print("\n" + "="*80)

def main():
    """Main function to run security audit."""
    auditor = SecurityAuditor()
    
    try:
        auditor.run_full_audit()
        
        # Generate and save report
        report = auditor.generate_report()
        
        # Save JSON report
        with open('security_audit_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print formatted report
        auditor.print_report()
        
        # Exit with appropriate code
        critical_issues = len([i for i in auditor.issues if i.severity == 'critical'])
        high_issues = len([i for i in auditor.issues if i.severity == 'high'])
        
        if critical_issues > 0:
            exit_code = 2  # Critical issues
        elif high_issues > 0:
            exit_code = 1  # High priority issues
        else:
            exit_code = 0  # No critical/high issues
            
        return exit_code
        
    except KeyboardInterrupt:
        print("\n\nSecurity audit interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Security audit failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)