"""
Phone number formatting utilities for Kenyan numbers
"""

import re
import logging

logger = logging.getLogger(__name__)

def format_kenyan_phone_number(phone: str) -> str:
    """
    Format a phone number to Kenyan E.164 format (254XXXXXXXXX)
    
    Args:
        phone: Phone number in various formats (e.g., "0712345678", "+254712345678", "(126) 088-1599")
    
    Returns:
        Formatted phone number in 254XXXXXXXXX format
    
    Raises:
        ValueError: If phone number format is invalid
    """
    if not phone:
        raise ValueError("Phone number cannot be empty")
    
    # Remove all non-digit characters
    cleaned = re.sub(r'\D', '', phone)
    
    # Handle different formats
    if len(cleaned) == 9 and cleaned.startswith('7'):
        # 712345678 -> 254712345678
        return f"254{cleaned}"
    elif len(cleaned) == 10 and cleaned.startswith('07'):
        # 0712345678 -> 254712345678
        return f"254{cleaned[1:]}"
    elif len(cleaned) == 10 and cleaned.startswith('7'):
        # 7123456789 (assuming first 7 is country code indicator) -> 254712345678
        return f"254{cleaned}"
    elif len(cleaned) == 12 and cleaned.startswith('254'):
        # Already in correct format
        return cleaned
    elif len(cleaned) == 11 and cleaned.startswith('1') and cleaned[1:4] == '26':
        # Handle US format like "12608815999" -> remove the "1" prefix
        # This appears to be (126) 088-1599 format without formatting
        # Assuming it's actually 2608815999 (Kenyan number)
        if len(cleaned) == 11 and cleaned.startswith('126'):
            # Remove the "1" prefix and add "254"
            return f"254{cleaned[3:]}"
    elif len(cleaned) == 13 and cleaned.startswith('254'):
        # 2547123456789 (too long, truncate to 12 digits)
        return cleaned[:12]
    
    # If none of the above formats match, raise an error
    raise ValueError(f"Invalid Kenyan phone number format: {phone}. Expected format: 07XXXXXXXX or 2547XXXXXXXX")

def validate_kenyan_phone_number(phone: str) -> bool:
    """
    Validate if a phone number is in a valid Kenyan format
    
    Args:
        phone: Phone number to validate
    
    Returns:
        True if valid, False otherwise
    """
    try:
        format_kenyan_phone_number(phone)
        return True
    except ValueError:
        return False

def format_phone_for_display(phone: str) -> str:
    """
    Format phone number for display purposes
    
    Args:
        phone: Phone number in various formats
    
    Returns:
        Formatted phone number for display (e.g., "(254) 712-345-678")
    """
    try:
        formatted = format_kenyan_phone_number(phone)
        # Format as (254) 712-345-678
        return f"(254) {formatted[3:6]}-{formatted[6:9]}-{formatted[9:]}"
    except ValueError:
        # Return original if formatting fails
        return phone