import * as yup from 'yup';

// Step 1: Hospital Information Schema
export const hospitalInfoSchema = yup.object({
  hospital_name: yup.string().required('Hospital name is required'),
  hospital_type: yup.string().required('Hospital type is required'),
  hospital_email: yup.string().email('Invalid email').required('Email is required'),
  hospital_phone: yup.string().required('Phone number is required'),
  hospital_website: yup.string()
    .transform((value) => value === '' ? undefined : value)
    .url('Invalid URL')
    .optional(),
});

// Step 2: Address & Business Information Schema
export const addressBusinessSchema = yup.object({
  address_line_1: yup.string().required('Address is required'),
  address_line_2: yup.string().optional(),
  city: yup.string().required('City is required'),
  state: yup.string().required('State is required'),
  postal_code: yup.string().required('Postal code is required'),
  country: yup.string().required('Country is required'),
  license_number: yup.string().optional(),
  tax_id: yup.string().optional(),
});

// Step 3: Administrator Account Schema
export const administratorSchema = yup.object({
  admin_first_name: yup.string().required('First name is required'),
  admin_last_name: yup.string().required('Last name is required'),
  admin_email: yup.string().email('Invalid email').required('Email is required'),
  admin_phone: yup.string().optional(),
  admin_password: yup.string()
    .min(8, 'Password must be at least 8 characters')
    .matches(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .matches(/[a-z]/, 'Password must contain at least one lowercase letter')
    .matches(/\d/, 'Password must contain at least one number')
    .matches(/[@$!%*?&]/, 'Password must contain at least one special character')
    .required('Password is required'),
  admin_confirm_password: yup.string()
    .oneOf([yup.ref('admin_password')], 'Passwords must match')
    .required('Please confirm your password'),
});

// Combined schema for final validation (optional, for reference)
export const completeRegistrationSchema = yup.object({
  ...hospitalInfoSchema.fields,
  ...addressBusinessSchema.fields,
  ...administratorSchema.fields,
});

// TypeScript interfaces for each step
export interface HospitalInfoData {
  hospital_name: string;
  hospital_type: string;
  hospital_email: string;
  hospital_phone: string;
  hospital_website?: string;
}

export interface AddressBusinessData {
  address_line_1: string;
  address_line_2?: string;
  city: string;
  state: string;
  postal_code: string;
  country: string;
  license_number?: string;
  tax_id?: string;
}

export interface AdministratorData {
  admin_first_name: string;
  admin_last_name: string;
  admin_email: string;
  admin_phone?: string;
  admin_password: string;
  admin_confirm_password: string;
}

// Combined interface for final submission (excludes confirm password)
export interface CompleteRegistrationData extends HospitalInfoData, AddressBusinessData, Omit<AdministratorData, 'admin_confirm_password'> {}

// Full interface including confirm password (for form validation)
export interface FullRegistrationData extends HospitalInfoData, AddressBusinessData, AdministratorData {}