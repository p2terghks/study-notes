-- Run ONCE as campus_admin against the new campus database, before deploying the service.
-- This role owns only the application's schema. Do not give the app the RDS administrator credential.
CREATE ROLE campus_app LOGIN;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT CONNECT ON DATABASE campus TO campus_app;
GRANT USAGE, CREATE ON SCHEMA public TO campus_app;
-- In the interactive psql session, run: \password campus_app
-- Paste the generated password from the AppSecretArn secret when prompted (no SQL/shell history).
