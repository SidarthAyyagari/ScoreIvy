# Database Migration Instructions

## Run the Migration

Your database needs to be updated to match the new OAuth-based User model. Run this command:

```bash
docker exec -it scoreivy-postgres psql -U postgres -d scoreivy -c "
ALTER TABLE users DROP COLUMN IF EXISTS username;
ALTER TABLE users DROP COLUMN IF EXISTS hashed_password;
ALTER TABLE users ADD COLUMN IF NOT EXISTS name VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS picture VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_provider VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS oauth_id VARCHAR;
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS last_login_at TIMESTAMP WITH TIME ZONE;
"
```

## Create Trigger for updated_at (Optional but Recommended)

To automatically update the `updated_at` timestamp:

```bash
docker exec -it scoreivy-postgres psql -U postgres -d scoreivy -c "
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS \$\$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
\$\$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
"
```

## Verify Migration

Check that the columns exist:

```bash
docker exec -it scoreivy-postgres psql -U postgres -d scoreivy -c "\d users"
```

You should see the new columns: `name`, `picture`, `oauth_provider`, `oauth_id`, `updated_at`, `last_login_at` and the old columns (`username`, `hashed_password`) should be gone.

