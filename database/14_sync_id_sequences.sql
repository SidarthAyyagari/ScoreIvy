-- Move every id sequence past the highest existing id. Sample data inserts explicit ids, which
-- leaves sequences behind and makes the next insert fail with a duplicate key. Safe to rerun.
DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN
        SELECT c.table_name, pg_get_serial_sequence(quote_ident(c.table_name), 'id') AS seq
        FROM information_schema.columns c
        WHERE c.table_schema = 'public' AND c.column_name = 'id'
          AND pg_get_serial_sequence(quote_ident(c.table_name), 'id') IS NOT NULL
    LOOP
        EXECUTE format(
            'SELECT setval(%L, COALESCE((SELECT MAX(id) FROM %I), 0) + 1, false)',
            r.seq, r.table_name
        );
    END LOOP;
END $$;
