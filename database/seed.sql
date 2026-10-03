-- Seed data for Digital Evidence Integrity

-- Example starter data. Adjust as needed for your local environment.
INSERT INTO users (username, email, hashed_password, is_active)
VALUES
    ('admin', 'admin@example.com', 'replace-with-hashed-password', TRUE)
ON CONFLICT (username) DO NOTHING;
