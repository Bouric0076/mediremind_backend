/**
 * Phone number formatting utilities for Kenyan numbers
 */

/**
 * Format phone number to Kenyan format (254XXXXXXXXX)
 * @param phone - Phone number in various formats (e.g., "0712345678", "+254712345678", "(126) 088-1599")
 * @returns Formatted phone number in 254XXXXXXXXX format
 */
export const formatKenyanPhoneNumber = (phone: string): string => {
  if (!phone) return '';
  
  // Remove all non-digit characters
  const cleaned = phone.replace(/\D/g, '');
  
  // Handle different formats
  if (cleaned.length === 9 && cleaned.startsWith('7')) {
    // 712345678 -> 254712345678
    return `254${cleaned}`;
  } else if (cleaned.length === 10 && cleaned.startsWith('07')) {
    // 0712345678 -> 254712345678
    return `254${cleaned.slice(1)}`;
  } else if (cleaned.length === 10 && cleaned.startsWith('7')) {
    // 7123456789 (assuming first 7 is country code indicator) -> 254712345678
    return `254${cleaned}`;
  } else if (cleaned.length === 12 && cleaned.startsWith('254')) {
    // Already in correct format
    return cleaned;
  } else if (cleaned.length === 11 && cleaned.startsWith('1') && cleaned.slice(1, 4) === '26') {
    // Handle US format like "12608815999" -> remove the "1" prefix
    // This appears to be (126) 088-1599 format without formatting
    // Assuming it's actually 2608815999 (Kenyan number)
    if (cleaned.length === 11 && cleaned.startsWith('126')) {
      // Remove the "1" prefix and add "254"
      return `254${cleaned.slice(3)}`;
    }
  } else if (cleaned.length === 13 && cleaned.startsWith('254')) {
    // 2547123456789 (too long, truncate to 12 digits)
    return cleaned.slice(0, 12);
  }
  
  // If none of the above formats match, return as-is
  return cleaned;
};

/**
 * Format phone number for display purposes (Kenyan format)
 * @param phone - Phone number in various formats
 * @returns Formatted phone number for display (e.g., "+254 712 345 678")
 */
export const formatPhoneForDisplay = (phone: string): string => {
  if (!phone) return 'Not provided';
  
  try {
    const formatted = formatKenyanPhoneNumber(phone);
    // Format as +254 712 345 678
    return `+254 ${formatted.slice(3, 6)} ${formatted.slice(6, 9)} ${formatted.slice(9)}`;
  } catch (error) {
    // Return original if formatting fails
    return phone;
  }
};

/**
 * Format phone number for SMS sending (Kenyan format)
 * @param phone - Phone number in various formats
 * @returns Formatted phone number for SMS (254XXXXXXXXX)
 */
export const formatPhoneForSMS = (phone: string): string => {
  if (!phone) return '';
  
  try {
    return formatKenyanPhoneNumber(phone);
  } catch (error) {
    // Return original if formatting fails
    return phone;
  }
};

/**
 * Validate if a phone number is in a valid Kenyan format
 * @param phone - Phone number to validate
 * @returns True if valid, false otherwise
 */
export const isValidKenyanPhoneNumber = (phone: string): boolean => {
  if (!phone) return false;
  
  try {
    const formatted = formatKenyanPhoneNumber(phone);
    // Valid Kenyan numbers should be 12 digits starting with 254
    return formatted.length === 12 && formatted.startsWith('254') && formatted[3] === '7';
  } catch (error) {
    return false;
  }
};