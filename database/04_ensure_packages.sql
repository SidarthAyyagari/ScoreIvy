-- Script to ensure packages exist in the database
-- Run this if packages are not showing up

-- Insert sample packages if they don't exist
INSERT INTO packages (name, description, test_count, price, is_active) VALUES
    ('Basic Package', '10 practice tests', 10, 29.99, true),
    ('Standard Package', '25 practice tests', 25, 59.99, true),
    ('Premium Package', '50 practice tests', 50, 99.99, true)
ON CONFLICT DO NOTHING;

-- If packages exist but are inactive, activate them
UPDATE packages SET is_active = true WHERE name IN ('Basic Package', 'Standard Package', 'Premium Package');

