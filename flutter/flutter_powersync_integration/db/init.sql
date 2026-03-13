CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE lists (
    id TEXT PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    name TEXT NOT NULL,
    owner_id TEXT,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE todos (
    id TEXT PRIMARY KEY DEFAULT uuid_generate_v4()::text,
    list_id TEXT REFERENCES lists(id),
    description TEXT NOT NULL,
    completed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- PowerSync requires a publication for logical replication
CREATE PUBLICATION powersync FOR TABLE lists, todos;
