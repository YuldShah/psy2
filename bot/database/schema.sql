CREATE TABLE IF NOT EXISTS users (
    id BIGINT PRIMARY KEY,
    full_name TEXT,
    student_id TEXT,
    role TEXT DEFAULT 'student',
    banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    student_id BIGINT REFERENCES users(id),
    time_slot TIMESTAMPTZ NOT NULL,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    reason TEXT,
    cancellation_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    sender_id BIGINT REFERENCES users(id),
    receiver_id BIGINT REFERENCES users(id),
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    is_replied BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS forwarded_messages (
    id SERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL,
    forwarded_message_id BIGINT NOT NULL,
    student_id BIGINT REFERENCES users(id) NOT NULL,
    student_message_id BIGINT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
