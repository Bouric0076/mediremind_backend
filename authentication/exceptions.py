"""Custom exceptions for the authentication app."""

class AuthenticationError(Exception):
    """Base exception for authentication errors."""
    pass

class InvalidCredentialsError(AuthenticationError):
    """Raised when invalid credentials are provided."""
    pass

class AccountLockedError(AuthenticationError):
    """Raised when account is locked due to too many failed attempts."""
    pass

class TwoFactorRequiredError(AuthenticationError):
    """Raised when two-factor authentication is required."""
    pass

class MFARequiredError(AuthenticationError):
    """Raised when multi-factor authentication is required."""
    pass

class InvalidMFATokenError(AuthenticationError):
    """Raised when invalid MFA token is provided."""
    pass

class InvalidTwoFactorCodeError(AuthenticationError):
    """Raised when invalid 2FA code is provided."""
    pass

class PermissionDeniedError(Exception):
    """Raised when user doesn't have required permissions."""
    pass

class SessionExpiredError(Exception):
    """Raised when user session has expired."""
    pass

class RateLimitExceededError(AuthenticationError):
    """Raised when rate limit is exceeded for authentication attempts."""
    pass