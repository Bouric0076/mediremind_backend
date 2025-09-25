"""
Comprehensive datetime validation utilities for appointment system
Provides robust datetime parsing, validation, and timezone handling
"""

import logging
from datetime import datetime, time, date, timedelta
from typing import Tuple, Optional, Union, Dict, Any
from django.utils import timezone
from django.core.exceptions import ValidationError
import pytz

logger = logging.getLogger(__name__)

class DateTimeValidator:
    """Comprehensive datetime validation for appointments"""
    
    # Working hours configuration
    WORKING_START = time(8, 0)  # 8:00 AM
    WORKING_END = time(18, 0)   # 6:00 PM
    
    # Maximum future booking (1 year)
    MAX_FUTURE_DAYS = 365
    
    # Supported datetime formats
    DATE_FORMATS = [
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%m/%d/%Y',
        '%Y/%m/%d'
    ]
    
    TIME_FORMATS = [
        '%H:%M',
        '%H:%M:%S',
        '%I:%M %p',
        '%I:%M:%S %p'
    ]
    
    DATETIME_FORMATS = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%fZ',
        '%Y-%m-%dT%H:%M:%S%z'
    ]
    
    @classmethod
    def parse_date(cls, date_input: Union[str, date, datetime]) -> Optional[date]:
        """
        Parse date from various input formats
        
        Args:
            date_input: Date string, date object, or datetime object
            
        Returns:
            Parsed date object or None if parsing fails
        """
        if isinstance(date_input, date):
            return date_input
        elif isinstance(date_input, datetime):
            return date_input.date()
        elif isinstance(date_input, str):
            for fmt in cls.DATE_FORMATS:
                try:
                    return datetime.strptime(date_input, fmt).date()
                except ValueError:
                    continue
            
            # Try parsing as ISO format
            try:
                return datetime.fromisoformat(date_input.replace('Z', '+00:00')).date()
            except ValueError:
                pass
                
        logger.warning(f"Failed to parse date: {date_input}")
        return None
    
    @classmethod
    def parse_time(cls, time_input: Union[str, time, datetime]) -> Optional[time]:
        """
        Parse time from various input formats
        
        Args:
            time_input: Time string, time object, or datetime object
            
        Returns:
            Parsed time object or None if parsing fails
        """
        if isinstance(time_input, time):
            return time_input
        elif isinstance(time_input, datetime):
            return time_input.time()
        elif isinstance(time_input, str):
            for fmt in cls.TIME_FORMATS:
                try:
                    return datetime.strptime(time_input, fmt).time()
                except ValueError:
                    continue
                    
        logger.warning(f"Failed to parse time: {time_input}")
        return None
    
    @classmethod
    def parse_datetime(cls, datetime_input: Union[str, datetime], default_timezone=None) -> Optional[datetime]:
        """
        Parse datetime from various input formats with timezone handling
        
        Args:
            datetime_input: Datetime string or datetime object
            default_timezone: Default timezone to use if none specified
            
        Returns:
            Parsed datetime object or None if parsing fails
        """
        if isinstance(datetime_input, datetime):
            if timezone.is_naive(datetime_input):
                if default_timezone:
                    return default_timezone.localize(datetime_input)
                else:
                    return timezone.make_aware(datetime_input)
            return datetime_input
        elif isinstance(datetime_input, str):
            # Try ISO format first
            try:
                return datetime.fromisoformat(datetime_input.replace('Z', '+00:00'))
            except ValueError:
                pass
            
            # Try other formats
            for fmt in cls.DATETIME_FORMATS:
                try:
                    dt = datetime.strptime(datetime_input, fmt)
                    if timezone.is_naive(dt):
                        if default_timezone:
                            return default_timezone.localize(dt)
                        else:
                            return timezone.make_aware(dt)
                    return dt
                except ValueError:
                    continue
                    
        logger.warning(f"Failed to parse datetime: {datetime_input}")
        return None
    
    @classmethod
    def validate_appointment_date(cls, appointment_date: Union[str, date, datetime]) -> Tuple[bool, Optional[str]]:
        """
        Validate appointment date
        
        Args:
            appointment_date: Date to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        parsed_date = cls.parse_date(appointment_date)
        if not parsed_date:
            return False, "Invalid date format"
        
        today = timezone.now().date()
        
        # Check if date is in the past
        if parsed_date <= today:
            return False, "Appointment date must be in the future"
        
        # Check if date is too far in the future
        max_future_date = today + timedelta(days=cls.MAX_FUTURE_DAYS)
        if parsed_date > max_future_date:
            return False, f"Appointment cannot be scheduled more than {cls.MAX_FUTURE_DAYS} days in advance"
        
        return True, None
    
    @classmethod
    def validate_appointment_time(cls, appointment_time: Union[str, time, datetime]) -> Tuple[bool, Optional[str]]:
        """
        Validate appointment time
        
        Args:
            appointment_time: Time to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        parsed_time = cls.parse_time(appointment_time)
        if not parsed_time:
            return False, "Invalid time format"
        
        # Check working hours
        if parsed_time < cls.WORKING_START or parsed_time > cls.WORKING_END:
            return False, f"Appointments must be between {cls.WORKING_START.strftime('%I:%M %p')} and {cls.WORKING_END.strftime('%I:%M %p')}"
        
        return True, None
    
    @classmethod
    def validate_appointment_datetime(cls, appointment_date: Union[str, date, datetime], 
                                    appointment_time: Union[str, time, datetime]) -> Tuple[bool, Optional[str]]:
        """
        Validate complete appointment datetime
        
        Args:
            appointment_date: Date to validate
            appointment_time: Time to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Validate date
        date_valid, date_error = cls.validate_appointment_date(appointment_date)
        if not date_valid:
            return False, date_error
        
        # Validate time
        time_valid, time_error = cls.validate_appointment_time(appointment_time)
        if not time_valid:
            return False, time_error
        
        # Parse both
        parsed_date = cls.parse_date(appointment_date)
        parsed_time = cls.parse_time(appointment_time)
        
        if not parsed_date or not parsed_time:
            return False, "Failed to parse date or time"
        
        # Create datetime and check if it's in the future
        appointment_datetime = timezone.make_aware(datetime.combine(parsed_date, parsed_time))
        current_datetime = timezone.now()
        
        if appointment_datetime <= current_datetime:
            return False, "Appointment must be scheduled for a future date and time"
        
        return True, None
    
    @classmethod
    def create_appointment_datetime(cls, appointment_date: Union[str, date, datetime], 
                                  appointment_time: Union[str, time, datetime]) -> Optional[datetime]:
        """
        Create a timezone-aware datetime from date and time inputs
        
        Args:
            appointment_date: Date input
            appointment_time: Time input
            
        Returns:
            Timezone-aware datetime object or None if parsing fails
        """
        parsed_date = cls.parse_date(appointment_date)
        parsed_time = cls.parse_time(appointment_time)
        
        if not parsed_date or not parsed_time:
            return None
        
        return timezone.make_aware(datetime.combine(parsed_date, parsed_time))
    
    @classmethod
    def format_appointment_datetime(cls, dt: datetime, format_type: str = 'display') -> str:
        """
        Format datetime for display or API responses
        
        Args:
            dt: Datetime to format
            format_type: 'display', 'api', or 'calendar'
            
        Returns:
            Formatted datetime string
        """
        if not dt:
            return ""
        
        if format_type == 'display':
            return dt.strftime('%B %d, %Y at %I:%M %p')
        elif format_type == 'api':
            return dt.isoformat()
        elif format_type == 'calendar':
            return dt.strftime('%Y%m%dT%H%M%SZ')
        else:
            return str(dt)
    
    @classmethod
    def get_duration_minutes(cls, start_time: datetime, end_time: datetime) -> int:
        """
        Calculate duration in minutes between two datetime objects
        
        Args:
            start_time: Start datetime
            end_time: End datetime
            
        Returns:
            Duration in minutes
        """
        if not start_time or not end_time:
            return 0
        
        duration = end_time - start_time
        return int(duration.total_seconds() / 60)
    
    @classmethod
    def add_duration_to_datetime(cls, start_datetime: datetime, duration_minutes: int) -> datetime:
        """
        Add duration in minutes to a datetime
        
        Args:
            start_datetime: Starting datetime
            duration_minutes: Duration to add in minutes
            
        Returns:
            New datetime with duration added
        """
        return start_datetime + timedelta(minutes=duration_minutes)


def validate_appointment_datetime_legacy(date_str: str, time_str: str) -> Tuple[bool, Optional[str]]:
    """
    Legacy function for backward compatibility
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        time_str: Time string in HH:MM format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    return DateTimeValidator.validate_appointment_datetime(date_str, time_str)


def create_appointment_datetime_legacy(date_str: str, time_str: str) -> Optional[datetime]:
    """
    Legacy function for backward compatibility
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        time_str: Time string in HH:MM format
        
    Returns:
        Timezone-aware datetime object or None
    """
    return DateTimeValidator.create_appointment_datetime(date_str, time_str)