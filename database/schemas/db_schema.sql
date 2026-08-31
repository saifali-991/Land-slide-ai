-- NER Landslide AI — PostgreSQL reference schema
-- (SQLite is the zero-setup default; SQLAlchemy creates this automatically.
--  Use this DDL when deploying to PostgreSQL via NER_DATABASE_URL.)

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    email         VARCHAR(255) NOT NULL UNIQUE,
    name          VARCHAR(120) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          VARCHAR(30)  NOT NULL DEFAULT 'public',   -- public | authority | researcher
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_users_email ON users (email);

CREATE TABLE IF NOT EXISTS saved_locations (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    name            VARCHAR(160) NOT NULL,
    state_name      VARCHAR(80)  NOT NULL DEFAULT '',
    lat             DOUBLE PRECISION NOT NULL,
    lon             DOUBLE PRECISION NOT NULL,
    notes           TEXT         NOT NULL DEFAULT '',
    last_risk_score DOUBLE PRECISION,
    last_risk_level VARCHAR(20),
    last_checked_at TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_saved_locations_user ON saved_locations (user_id);

CREATE TABLE IF NOT EXISTS risk_checks (
    id                  SERIAL PRIMARY KEY,
    user_id             INTEGER REFERENCES users (id) ON DELETE SET NULL,
    location_name       VARCHAR(160) NOT NULL DEFAULT '',
    state_name          VARCHAR(80)  NOT NULL DEFAULT '',
    lat                 DOUBLE PRECISION NOT NULL,
    lon                 DOUBLE PRECISION NOT NULL,
    temperature_c       DOUBLE PRECISION,
    humidity_pct        DOUBLE PRECISION,
    wind_kmph           DOUBLE PRECISION,
    rainfall_current_mm DOUBLE PRECISION,
    rainfall_24h_mm     DOUBLE PRECISION,
    rainfall_72h_mm     DOUBLE PRECISION,
    soil_moisture       DOUBLE PRECISION,
    elevation_m         DOUBLE PRECISION,
    slope_deg           DOUBLE PRECISION,
    risk_score          DOUBLE PRECISION NOT NULL,
    risk_level          VARCHAR(20)  NOT NULL,             -- LOW | MODERATE | HIGH | CRITICAL
    factors_json        JSONB        NOT NULL DEFAULT '{}',
    model_type          VARCHAR(40)  NOT NULL DEFAULT 'rule_based_v1',
    observed_landslide  BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_risk_checks_user ON risk_checks (user_id);
CREATE INDEX IF NOT EXISTS ix_risk_checks_state ON risk_checks (state_name);
CREATE INDEX IF NOT EXISTS ix_risk_checks_level ON risk_checks (risk_level);
CREATE INDEX IF NOT EXISTS ix_risk_checks_created ON risk_checks (created_at);

CREATE TABLE IF NOT EXISTS alerts (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER REFERENCES users (id) ON DELETE CASCADE,  -- NULL = public broadcast
    title         VARCHAR(200) NOT NULL,
    message       TEXT         NOT NULL,
    location_name VARCHAR(160) NOT NULL DEFAULT '',
    state_name    VARCHAR(80)  NOT NULL DEFAULT '',
    lat           DOUBLE PRECISION,
    lon           DOUBLE PRECISION,
    risk_score    DOUBLE PRECISION,
    risk_level    VARCHAR(20)  NOT NULL,
    channels      JSONB        NOT NULL DEFAULT '[]',              -- ["in_app","email","sms"]
    is_read       BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_alerts_user ON alerts (user_id);
CREATE INDEX IF NOT EXISTS ix_alerts_created ON alerts (created_at);

CREATE TABLE IF NOT EXISTS notification_preferences (
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER NOT NULL UNIQUE REFERENCES users (id) ON DELETE CASCADE,
    in_app        BOOLEAN     NOT NULL DEFAULT TRUE,
    email         BOOLEAN     NOT NULL DEFAULT FALSE,
    email_address VARCHAR(255),
    sms           BOOLEAN     NOT NULL DEFAULT FALSE,
    min_level     VARCHAR(20) NOT NULL DEFAULT 'HIGH',            -- MODERATE | HIGH | CRITICAL
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
