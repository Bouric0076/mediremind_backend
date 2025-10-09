-- Create system_logs table for application logging
CREATE TABLE IF NOT EXISTS system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    level TEXT NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    category TEXT NOT NULL DEFAULT 'system',
    component TEXT NOT NULL,
    message TEXT NOT NULL,
    user_id UUID,
    appointment_id UUID,
    task_id UUID,
    metadata JSONB,
    error_details TEXT,
    request_id UUID,
    module TEXT,
    function TEXT,
    line_number INTEGER
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(level);
CREATE INDEX IF NOT EXISTS idx_system_logs_category ON system_logs(category);
CREATE INDEX IF NOT EXISTS idx_system_logs_component ON system_logs(component);
CREATE INDEX IF NOT EXISTS idx_system_logs_user_id ON system_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_system_logs_appointment_id ON system_logs(appointment_id);

-- Grant permissions to the application user
GRANT ALL ON system_logs TO postgres;
GRANT ALL ON system_logs TO anon;
GRANT ALL ON system_logs TO authenticated;
GRANT ALL ON system_logs TO service_role;