-- Launch exams and Stripe orders
INSERT INTO exams (slug, name, description, tools, display_order) VALUES
    ('usmle-step-1', 'USMLE Step 1', 'Timed Step 1 practice blocks', '["lab_values", "notes"]'::jsonb, 1),
    ('sat', 'SAT', 'Digital SAT practice tests', '["calculator", "reference_sheet", "notes"]'::jsonb, 2)
ON CONFLICT (slug) DO NOTHING;

CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    package_id INTEGER NOT NULL REFERENCES packages(id),
    status VARCHAR NOT NULL DEFAULT 'pending',
    amount_cents INTEGER NOT NULL,
    currency VARCHAR NOT NULL,
    stripe_checkout_session_id VARCHAR UNIQUE,
    stripe_payment_intent_id VARCHAR,
    user_package_id INTEGER REFERENCES user_packages(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP WITH TIME ZONE,
    refunded_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_payment_intent ON orders(stripe_payment_intent_id);
