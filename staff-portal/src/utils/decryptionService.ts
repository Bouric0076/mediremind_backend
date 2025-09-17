/**
 * Frontend decryption service for handling Fernet-encrypted patient data
 * This service provides client-side decryption capabilities for authorized users
 */

import CryptoJS from 'crypto-js';

// Base64 URL-safe decoding function

const base64UrlDecode = (str: string): Uint8Array => {
  // Add padding if needed
  const padding = '='.repeat((4 - (str.length % 4)) % 4);
  const base64 = str.replace(/-/g, '+').replace(/_/g, '/') + padding;
  const binary = atob(base64);
  return new Uint8Array(binary.split('').map(char => char.charCodeAt(0)));
};

class FernetDecryption {
  private key: Uint8Array;
  private signingKey: Uint8Array;
  private encryptionKey: Uint8Array;

  constructor(keyBase64: string) {
    // Decode the base64 key
    this.key = base64UrlDecode(keyBase64.replace(/=/g, ''));
    
    // Split the 32-byte key into signing (16 bytes) and encryption (16 bytes) keys
    this.signingKey = this.key.slice(0, 16);
    this.encryptionKey = this.key.slice(16, 32);
  }

  /**
   * Decrypt a Fernet token
   * @param token - The encrypted Fernet token
   * @returns The decrypted plaintext or null if decryption fails
   */
  decrypt(token: string): string | null {
    try {
      // Remove any whitespace and check if it looks like a Fernet token
      const cleanToken = token.trim();
      
      // Basic validation - Fernet tokens are base64url encoded and quite long
      if (cleanToken.length < 60 || !this.isValidBase64Url(cleanToken)) {
        // If it doesn't look like an encrypted token, return as-is
        return cleanToken;
      }

      // Decode the token
      const tokenBytes = base64UrlDecode(cleanToken);
      
      // Fernet token structure: version(1) + timestamp(8) + iv(16) + ciphertext + hmac(32)
      if (tokenBytes.length < 57) { // Minimum size
        return cleanToken; // Return as-is if too short
      }

      const version = tokenBytes[0];
      if (version !== 0x80) {
        return cleanToken; // Not a valid Fernet token
      }

      // Skip timestamp (bytes 1-8) as it's not needed for decryption
      const iv = tokenBytes.slice(9, 25);
      const ciphertext = tokenBytes.slice(25, -32);
      const hmac = tokenBytes.slice(-32);

      // Verify HMAC
      const message = tokenBytes.slice(0, -32);
      const expectedHmac = CryptoJS.HmacSHA256(
        CryptoJS.lib.WordArray.create(message),
        CryptoJS.lib.WordArray.create(this.signingKey)
      );
      
      const providedHmac = CryptoJS.lib.WordArray.create(hmac);
      if (CryptoJS.lib.WordArray.create(expectedHmac.words).toString() !== providedHmac.toString()) {
        console.warn('HMAC verification failed');
        return cleanToken;
      }

      // Decrypt using AES-128-CBC
      const key = CryptoJS.lib.WordArray.create(this.encryptionKey);
      const ivWordArray = CryptoJS.lib.WordArray.create(iv);
      const ciphertextWordArray = CryptoJS.lib.WordArray.create(ciphertext);

      const decrypted = CryptoJS.AES.decrypt(
        { ciphertext: ciphertextWordArray } as any,
        key,
        {
          iv: ivWordArray,
          mode: CryptoJS.mode.CBC,
          padding: CryptoJS.pad.Pkcs7
        }
      );

      const decryptedText = decrypted.toString(CryptoJS.enc.Utf8);
      return decryptedText || cleanToken;

    } catch (error) {
      console.warn('Decryption failed:', error);
      // Return original text if decryption fails
      return token;
    }
  }

  private isValidBase64Url(str: string): boolean {
    // Check if string contains only valid base64url characters
    return /^[A-Za-z0-9_-]+$/.test(str);
  }
}

// Encryption key from backend settings
const ENCRYPTION_KEY = 'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM1Pg=';

// Create a singleton instance
const fernetDecryption = new FernetDecryption(ENCRYPTION_KEY);

/**
 * Decrypt an encrypted field value
 * @param encryptedValue - The encrypted value to decrypt
 * @returns The decrypted value or the original value if decryption fails
 */
export const decryptField = (encryptedValue: string | null | undefined): string => {
  if (!encryptedValue) {
    return '';
  }

  return fernetDecryption.decrypt(encryptedValue) || encryptedValue;
};

/**
 * Decrypt multiple fields in an object
 * @param data - Object containing encrypted fields
 * @param fieldsToDecrypt - Array of field names to decrypt
 * @returns New object with decrypted fields
 */
export const decryptFields = <T extends Record<string, any>>(
  data: T,
  fieldsToDecrypt: (keyof T)[]
): T => {
  const decryptedData = { ...data };
  
  fieldsToDecrypt.forEach(field => {
    if (decryptedData[field]) {
      (decryptedData as any)[field] = decryptField(decryptedData[field] as string);
    }
  });

  return decryptedData;
};

/**
 * Check if a value appears to be encrypted
 * @param value - The value to check
 * @returns True if the value appears to be encrypted
 */
export const isEncrypted = (value: string | null | undefined): boolean => {
  if (!value || typeof value !== 'string') {
    return false;
  }

  const cleanValue = value.trim();
  // Fernet tokens are base64url encoded and typically quite long
  return cleanValue.length > 60 && /^[A-Za-z0-9_-]+$/.test(cleanValue);
};

export default {
  decryptField,
  decryptFields,
  isEncrypted
};