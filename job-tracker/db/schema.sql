CREATE TABLE applications (
    id SERIAL PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    role_title VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'applied',
    date_applied DATE NOT NULL,
    follow_up_date DATE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    application_id INTEGER REFERENCES applications(id),
    event_type VARCHAR(50) NOT NULL,
    message TEXT,
    processed_at TIMESTAMP DEFAULT NOW()
);