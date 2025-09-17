-- Enhanced Database Schema for Seamless Appointment Reminder System
-- This schema implements robust relationships, indexing, and additional tables for notifications and reminders

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table (enhanced with additional fields)
CREATE TABLE IF NOT EXISTS users (
    id UUID REFERENCES auth.users PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    phone TEXT,
    role TEXT CHECK (role IN ('patient', 'doctor', 'admin')) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    timezone TEXT DEFAULT 'UTC',
    preferred_language TEXT DEFAULT 'en',
    notification_preferences JSONB DEFAULT '{"email": true, "sms": true, "push": true}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Patients table (enhanced with medical information)
CREATE TABLE IF NOT EXISTS patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    date_of_birth DATE,
    gender TEXT CHECK (gender IN ('male', 'female', 'other')),
    emergency_contact TEXT,
    emergency_phone TEXT,
    medical_history JSONB DEFAULT '{}',
    allergies TEXT[],
    current_medications TEXT[],
    insurance_info JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    UNIQUE(user_id)
);

-- Staff profiles table (enhanced with availability and specialization)
CREATE TABLE IF NOT EXISTS staff_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    full_name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    position TEXT,
    department TEXT,
    staff_no TEXT UNIQUE,
    specialization TEXT[],
    license_number TEXT,
    years_of_experience INTEGER DEFAULT 0,
    consultation_fee DECIMAL(10,2),
    working_hours JSONB DEFAULT '{"monday": {"start": "08:00", "end": "17:00"}, "tuesday": {"start": "08:00", "end": "17:00"}, "wednesday": {"start": "08:00", "end": "17:00"}, "thursday": {"start": "08:00", "end": "17:00"}, "friday": {"start": "08:00", "end": "17:00"}}',
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    UNIQUE(user_id)
);

-- Appointments table (enhanced with more detailed tracking)
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    doctor_id UUID REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    time TIME NOT NULL,
    duration_minutes INTEGER DEFAULT 30,
    type TEXT NOT NULL,
    status TEXT CHECK (status IN ('pending', 'confirmed', 'completed', 'cancelled', 'rescheduled', 'no_show')) DEFAULT 'pending',
    priority TEXT CHECK (priority IN ('low', 'medium', 'high', 'urgent')) DEFAULT 'medium',
    notes TEXT,
    location_text TEXT,
    room_number TEXT,
    consultation_fee DECIMAL(10,2),
    payment_status TEXT CHECK (payment_status IN ('pending', 'paid', 'refunded')) DEFAULT 'pending',
    cancellation_reason TEXT,
    rescheduled_from UUID REFERENCES appointments(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Appointment reminders table (new table for tracking reminders)
CREATE TABLE IF NOT EXISTS appointment_reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    appointment_id UUID REFERENCES appointments(id) ON DELETE CASCADE,
    reminder_type TEXT CHECK (reminder_type IN ('24_hours', '2_hours', '30_minutes', 'custom')) NOT NULL,
    scheduled_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status TEXT CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')) DEFAULT 'pending',
    delivery_method TEXT CHECK (delivery_method IN ('email', 'sms', 'push', 'whatsapp')) NOT NULL,
    recipient_id UUID REFERENCES users(id) ON DELETE CASCADE,
    message_content TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Notification logs table (comprehensive notification tracking)
CREATE TABLE IF NOT EXISTS notification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    appointment_id UUID REFERENCES appointments(id) ON DELETE SET NULL,
    reminder_id UUID REFERENCES appointment_reminders(id) ON DELETE SET NULL,
    notification_type TEXT CHECK (notification_type IN ('reminder', 'confirmation', 'cancellation', 'reschedule', 'update')) NOT NULL,
    delivery_method TEXT CHECK (delivery_method IN ('email', 'sms', 'push', 'whatsapp')) NOT NULL,
    recipient_contact TEXT NOT NULL,
    subject TEXT,
    message_content TEXT NOT NULL,
    status TEXT CHECK (status IN ('pending', 'sent', 'delivered', 'failed', 'bounced')) DEFAULT 'pending',
    external_id TEXT, -- For tracking with external services (Twilio, etc.)
    response_data JSONB,
    error_message TEXT,
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Push subscriptions table (enhanced for better device management)
CREATE TABLE IF NOT EXISTS push_subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    endpoint TEXT NOT NULL,
    p256dh TEXT NOT NULL,
    auth TEXT NOT NULL,
    device_type TEXT CHECK (device_type IN ('web', 'android', 'ios')) DEFAULT 'web',
    device_id TEXT,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    UNIQUE(user_id, endpoint)
);

-- System settings table (for configurable reminder settings)
CREATE TABLE IF NOT EXISTS system_settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    setting_key TEXT UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Notification templates table (for consistent messaging)
CREATE TABLE IF NOT EXISTS notification_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_name TEXT UNIQUE NOT NULL,
    template_type TEXT CHECK (template_type IN ('reminder', 'confirmation', 'cancellation', 'reschedule')) NOT NULL,
    delivery_method TEXT CHECK (delivery_method IN ('email', 'sms', 'push', 'whatsapp')) NOT NULL,
    language TEXT DEFAULT 'en',
    subject_template TEXT,
    body_template TEXT NOT NULL,
    variables JSONB DEFAULT '[]', -- Array of available template variables
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Audit logs table (for tracking all system changes)
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    action TEXT CHECK (action IN ('INSERT', 'UPDATE', 'DELETE')) NOT NULL,
    old_values JSONB,
    new_values JSONB,
    changed_by UUID REFERENCES users(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    ip_address INET,
    user_agent TEXT
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_patients_user_id ON patients(user_id);
CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);
CREATE INDEX IF NOT EXISTS idx_patients_email ON patients(email);

CREATE INDEX IF NOT EXISTS idx_staff_profiles_user_id ON staff_profiles(user_id);
CREATE INDEX IF NOT EXISTS idx_staff_profiles_department ON staff_profiles(department);
CREATE INDEX IF NOT EXISTS idx_staff_profiles_is_available ON staff_profiles(is_available);

CREATE INDEX IF NOT EXISTS idx_appointments_patient_id ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_id ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_date_time ON appointments(date, time);
CREATE INDEX IF NOT EXISTS idx_appointments_created_at ON appointments(created_at);

CREATE INDEX IF NOT EXISTS idx_appointment_reminders_appointment_id ON appointment_reminders(appointment_id);
CREATE INDEX IF NOT EXISTS idx_appointment_reminders_scheduled_time ON appointment_reminders(scheduled_time);
CREATE INDEX IF NOT EXISTS idx_appointment_reminders_status ON appointment_reminders(status);
CREATE INDEX IF NOT EXISTS idx_appointment_reminders_delivery_method ON appointment_reminders(delivery_method);

CREATE INDEX IF NOT EXISTS idx_notification_logs_user_id ON notification_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_appointment_id ON notification_logs(appointment_id);
CREATE INDEX IF NOT EXISTS idx_notification_logs_status ON notification_logs(status);
CREATE INDEX IF NOT EXISTS idx_notification_logs_created_at ON notification_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_notification_logs_delivery_method ON notification_logs(delivery_method);

CREATE INDEX IF NOT EXISTS idx_push_subscriptions_user_id ON push_subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_push_subscriptions_is_active ON push_subscriptions(is_active);

CREATE INDEX IF NOT EXISTS idx_audit_logs_table_name ON audit_logs(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_logs_record_id ON audit_logs(record_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_changed_at ON audit_logs(changed_at);

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, description) VALUES
('reminder_intervals', '["24_hours", "2_hours", "30_minutes"]', 'Default reminder intervals for appointments'),
('max_retry_attempts', '3', 'Maximum retry attempts for failed notifications'),
('notification_rate_limit', '{"sms": 100, "email": 1000, "push": 5000}', 'Rate limits per hour for different notification types'),
('working_hours', '{"start": "08:00", "end": "18:00"}', 'Default working hours for the clinic'),
('appointment_duration', '30', 'Default appointment duration in minutes'),
('advance_booking_days', '30', 'Maximum days in advance for booking appointments')
ON CONFLICT (setting_key) DO NOTHING;

-- Insert default notification templates
INSERT INTO notification_templates (template_name, template_type, delivery_method, subject_template, body_template, variables) VALUES
('appointment_reminder_24h_sms', 'reminder', 'sms', NULL, 'Hi {{patient_name}}, you have an appointment with Dr. {{doctor_name}} tomorrow at {{appointment_time}}. Please reply 1 to confirm, 2 to reschedule, or 3 to cancel.', '["patient_name", "doctor_name", "appointment_time", "location"]'),
('appointment_reminder_2h_sms', 'reminder', 'sms', NULL, 'Reminder: Your appointment with Dr. {{doctor_name}} is in 2 hours at {{appointment_time}}. Location: {{location}}', '["patient_name", "doctor_name", "appointment_time", "location"]'),
('appointment_confirmation_email', 'confirmation', 'email', 'Appointment Confirmed - {{appointment_date}}', 'Dear {{patient_name}},\n\nYour appointment has been confirmed:\n\nDoctor: Dr. {{doctor_name}}\nDate: {{appointment_date}}\nTime: {{appointment_time}}\nLocation: {{location}}\n\nPlease arrive 15 minutes early.\n\nBest regards,\nMediRemind Team', '["patient_name", "doctor_name", "appointment_date", "appointment_time", "location"]'),
('appointment_cancellation_push', 'cancellation', 'push', 'Appointment Cancelled', 'Your appointment with Dr. {{doctor_name}} on {{appointment_date}} has been cancelled. {{cancellation_reason}}', '["patient_name", "doctor_name", "appointment_date", "cancellation_reason"]')
ON CONFLICT (template_name) DO NOTHING;

-- Create functions for automatic timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = TIMEZONE('utc'::text, NOW());
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for automatic timestamp updates
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_patients_updated_at BEFORE UPDATE ON patients FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_staff_profiles_updated_at BEFORE UPDATE ON staff_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_appointment_reminders_updated_at BEFORE UPDATE ON appointment_reminders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_notification_templates_updated_at BEFORE UPDATE ON notification_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for automatic reminder scheduling
CREATE OR REPLACE FUNCTION schedule_appointment_reminders()
RETURNS TRIGGER AS $$
DECLARE
    reminder_intervals TEXT[];
    interval_text TEXT;
    reminder_time TIMESTAMP WITH TIME ZONE;
    appointment_datetime TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Only schedule reminders for confirmed appointments
    IF NEW.status = 'confirmed' THEN
        -- Get reminder intervals from system settings
        SELECT setting_value::TEXT[] INTO reminder_intervals 
        FROM system_settings 
        WHERE setting_key = 'reminder_intervals' AND is_active = TRUE;
        
        -- Calculate appointment datetime
        appointment_datetime := (NEW.date + NEW.time);
        
        -- Schedule reminders for each interval
        FOREACH interval_text IN ARRAY reminder_intervals
        LOOP
            CASE interval_text
                WHEN '24_hours' THEN
                    reminder_time := appointment_datetime - INTERVAL '24 hours';
                WHEN '2_hours' THEN
                    reminder_time := appointment_datetime - INTERVAL '2 hours';
                WHEN '30_minutes' THEN
                    reminder_time := appointment_datetime - INTERVAL '30 minutes';
                ELSE
                    CONTINUE;
            END CASE;
            
            -- Only schedule if reminder time is in the future
            IF reminder_time > NOW() THEN
                INSERT INTO appointment_reminders (
                    appointment_id,
                    reminder_type,
                    scheduled_time,
                    delivery_method,
                    recipient_id
                ) VALUES (
                    NEW.id,
                    interval_text,
                    reminder_time,
                    'sms', -- Default to SMS, can be customized based on user preferences
                    NEW.patient_id
                );
            END IF;
        END LOOP;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for automatic reminder scheduling
CREATE TRIGGER schedule_reminders_on_appointment_confirm 
    AFTER INSERT OR UPDATE ON appointments 
    FOR EACH ROW 
    WHEN (NEW.status = 'confirmed')
    EXECUTE FUNCTION schedule_appointment_reminders();

-- Create function for audit logging
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        INSERT INTO audit_logs (table_name, record_id, action, old_values)
        VALUES (TG_TABLE_NAME, OLD.id, TG_OP, row_to_json(OLD));
        RETURN OLD;
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO audit_logs (table_name, record_id, action, old_values, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(OLD), row_to_json(NEW));
        RETURN NEW;
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO audit_logs (table_name, record_id, action, new_values)
        VALUES (TG_TABLE_NAME, NEW.id, TG_OP, row_to_json(NEW));
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Create audit triggers for important tables
CREATE TRIGGER audit_users AFTER INSERT OR UPDATE OR DELETE ON users FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_appointments AFTER INSERT OR UPDATE OR DELETE ON appointments FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
CREATE TRIGGER audit_appointment_reminders AFTER INSERT OR UPDATE OR DELETE ON appointment_reminders FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

-- Create views for common queries
CREATE OR REPLACE VIEW upcoming_appointments AS
SELECT 
    a.id,
    a.date,
    a.time,
    a.type,
    a.status,
    a.location_text,
    p.full_name AS patient_name,
    p.phone AS patient_phone,
    p.email AS patient_email,
    s.full_name AS doctor_name,
    s.phone AS doctor_phone,
    s.email AS doctor_email,
    a.created_at
FROM appointments a
JOIN patients p ON a.patient_id = p.user_id
JOIN staff_profiles s ON a.doctor_id = s.user_id
WHERE a.date >= CURRENT_DATE
  AND a.status IN ('confirmed', 'pending')
ORDER BY a.date, a.time;

CREATE OR REPLACE VIEW pending_reminders AS
SELECT 
    r.id,
    r.appointment_id,
    r.reminder_type,
    r.scheduled_time,
    r.delivery_method,
    r.status,
    a.date AS appointment_date,
    a.time AS appointment_time,
    p.full_name AS patient_name,
    p.phone AS patient_phone,
    p.email AS patient_email
FROM appointment_reminders r
JOIN appointments a ON r.appointment_id = a.id
JOIN patients p ON a.patient_id = p.user_id
WHERE r.status = 'pending'
  AND r.scheduled_time <= NOW() + INTERVAL '1 hour'
ORDER BY r.scheduled_time;

-- Grant necessary permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;

COMMIT;