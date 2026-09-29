BEGIN;

CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL, 
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

-- Running upgrade  -> 0b9345094ff9

CREATE TABLE states (
    name VARCHAR(100) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (name)
);

CREATE TABLE districts (
    state_id VARCHAR(36) NOT NULL, 
    name VARCHAR(100) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(state_id) REFERENCES states (id), 
    UNIQUE (state_id, name)
);

CREATE INDEX ix_districts_state_id ON districts (state_id);

CREATE TABLE government_schemes (
    name VARCHAR(200) NOT NULL, 
    authority VARCHAR(200) NOT NULL, 
    description TEXT NOT NULL, 
    benefits TEXT NOT NULL, 
    application_process TEXT NOT NULL, 
    source_url VARCHAR(500) NOT NULL, 
    state_id VARCHAR(36), 
    is_demo BOOLEAN NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(state_id) REFERENCES states (id)
);

CREATE INDEX ix_government_schemes_state_id ON government_schemes (state_id);

CREATE TABLE ngos (
    name VARCHAR(160) NOT NULL, 
    district_id VARCHAR(36) NOT NULL, 
    latitude FLOAT, 
    longitude FLOAT, 
    phone VARCHAR(40) NOT NULL, 
    availability VARCHAR(120) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90)), 
    CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180)), 
    FOREIGN KEY(district_id) REFERENCES districts (id)
);

CREATE INDEX ix_ngos_district_id ON ngos (district_id);

CREATE TABLE prosecutors (
    name VARCHAR(120) NOT NULL, 
    district_id VARCHAR(36) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(district_id) REFERENCES districts (id)
);

CREATE TABLE scheme_documents (
    scheme_id VARCHAR(36) NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(scheme_id) REFERENCES government_schemes (id)
);

CREATE INDEX ix_scheme_documents_scheme_id ON scheme_documents (scheme_id);

CREATE TABLE scheme_eligibility (
    scheme_id VARCHAR(36) NOT NULL, 
    field VARCHAR(80) NOT NULL, 
    operator VARCHAR(20) NOT NULL, 
    value JSON NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(scheme_id) REFERENCES government_schemes (id)
);

CREATE INDEX ix_scheme_eligibility_scheme_id ON scheme_eligibility (scheme_id);

CREATE TABLE users (
    email VARCHAR(254) NOT NULL, 
    name VARCHAR(120) NOT NULL, 
    password_hash TEXT NOT NULL, 
    role VARCHAR(14) NOT NULL, 
    district_id VARCHAR(36), 
    state_id VARCHAR(36), 
    active BOOLEAN NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CHECK (role != 'DISTRICT_ADMIN' OR district_id IS NOT NULL), 
    CHECK (role != 'STATE_ADMIN' OR state_id IS NOT NULL), 
    FOREIGN KEY(district_id) REFERENCES districts (id), 
    FOREIGN KEY(state_id) REFERENCES states (id), 
    UNIQUE (email)
);

CREATE INDEX ix_users_district_id ON users (district_id);

CREATE INDEX ix_users_state_id ON users (state_id);

CREATE TABLE audit_logs (
    actor_id VARCHAR(36), 
    action VARCHAR(100) NOT NULL, 
    resource_type VARCHAR(80) NOT NULL, 
    resource_id VARCHAR(120), 
    outcome VARCHAR(40) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(actor_id) REFERENCES users (id)
);

CREATE INDEX ix_audit_logs_actor_id ON audit_logs (actor_id);

CREATE TABLE counsellors (
    user_id VARCHAR(36) NOT NULL, 
    specialization VARCHAR(120) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id)
);

CREATE TABLE legal_officers (
    user_id VARCHAR(36) NOT NULL, 
    designation VARCHAR(120) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id)
);

CREATE TABLE ngo_languages (
    ngo_id VARCHAR(36) NOT NULL, 
    language VARCHAR(60) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ngo_id) REFERENCES ngos (id), 
    UNIQUE (ngo_id, language)
);

CREATE INDEX ix_ngo_languages_ngo_id ON ngo_languages (ngo_id);

CREATE TABLE ngo_services (
    ngo_id VARCHAR(36) NOT NULL, 
    service VARCHAR(80) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(ngo_id) REFERENCES ngos (id), 
    UNIQUE (ngo_id, service)
);

CREATE INDEX ix_ngo_services_ngo_id ON ngo_services (ngo_id);

CREATE TABLE victims (
    user_id VARCHAR(36) NOT NULL, 
    district_id VARCHAR(36) NOT NULL, 
    language VARCHAR(60) NOT NULL, 
    age INTEGER, 
    annual_income INTEGER, 
    support_category VARCHAR(80), 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CHECK (age IS NULL OR (age >= 0 AND age <= 130)), 
    CHECK (annual_income IS NULL OR annual_income >= 0), 
    FOREIGN KEY(district_id) REFERENCES districts (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id)
);

CREATE INDEX ix_victims_district_id ON victims (district_id);

CREATE TABLE cases (
    case_id VARCHAR(60) NOT NULL, 
    victim_id VARCHAR(36) NOT NULL, 
    district_id VARCHAR(36) NOT NULL, 
    case_type VARCHAR(100) NOT NULL, 
    fir_number VARCHAR(80), 
    fir_date DATE, 
    police_station VARCHAR(160), 
    investigation_status VARCHAR(40) NOT NULL, 
    chargesheet_date DATE, 
    chargesheet_reference VARCHAR(160), 
    court VARCHAR(160), 
    prosecutor_id VARCHAR(36), 
    legal_officer_id VARCHAR(36), 
    status VARCHAR(40) NOT NULL, 
    compensation_status VARCHAR(40) NOT NULL, 
    rehabilitation_status VARCHAR(40) NOT NULL, 
    protection_status VARCHAR(40) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(district_id) REFERENCES districts (id), 
    FOREIGN KEY(legal_officer_id) REFERENCES legal_officers (id), 
    FOREIGN KEY(prosecutor_id) REFERENCES prosecutors (id), 
    FOREIGN KEY(victim_id) REFERENCES victims (id), 
    UNIQUE (case_id)
);

CREATE INDEX ix_cases_district_id ON cases (district_id);

CREATE INDEX ix_cases_legal_officer_id ON cases (legal_officer_id);

CREATE INDEX ix_cases_victim_id ON cases (victim_id);

CREATE TABLE chat_messages (
    victim_id VARCHAR(36) NOT NULL, 
    sender_id VARCHAR(36) NOT NULL, 
    recipient_id VARCHAR(36) NOT NULL, 
    body TEXT NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(recipient_id) REFERENCES users (id), 
    FOREIGN KEY(sender_id) REFERENCES users (id), 
    FOREIGN KEY(victim_id) REFERENCES victims (id)
);

CREATE INDEX ix_chat_messages_victim_id ON chat_messages (victim_id);

CREATE TABLE counsellor_assignments (
    counsellor_id VARCHAR(36) NOT NULL, 
    victim_id VARCHAR(36) NOT NULL, 
    active BOOLEAN NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(counsellor_id) REFERENCES counsellors (id), 
    FOREIGN KEY(victim_id) REFERENCES victims (id), 
    UNIQUE (counsellor_id, victim_id)
);

CREATE INDEX ix_counsellor_assignments_counsellor_id ON counsellor_assignments (counsellor_id);

CREATE INDEX ix_counsellor_assignments_victim_id ON counsellor_assignments (victim_id);

CREATE TABLE distress_assessments (
    victim_id VARCHAR(36) NOT NULL, 
    instrument VARCHAR(100) NOT NULL, 
    score FLOAT NOT NULL, 
    assessed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(victim_id) REFERENCES victims (id)
);

CREATE INDEX ix_distress_assessments_victim_id ON distress_assessments (victim_id);

CREATE TABLE distress_predictions (
    victim_id VARCHAR(36) NOT NULL, 
    external_id VARCHAR(120) NOT NULL, 
    score FLOAT NOT NULL, 
    level VARCHAR(20) NOT NULL, 
    trend VARCHAR(20) NOT NULL, 
    confidence FLOAT NOT NULL, 
    factors JSON NOT NULL, 
    recommended_action TEXT NOT NULL, 
    model_version VARCHAR(120) NOT NULL, 
    observed_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    CHECK (confidence >= 0 AND confidence <= 1), 
    CHECK (score >= 0 AND score <= 100), 
    FOREIGN KEY(victim_id) REFERENCES victims (id), 
    UNIQUE (external_id)
);

CREATE INDEX ix_distress_predictions_observed_at ON distress_predictions (observed_at);

CREATE INDEX ix_distress_predictions_victim_id ON distress_predictions (victim_id);

CREATE TABLE followups (
    victim_id VARCHAR(36) NOT NULL, 
    counsellor_id VARCHAR(36) NOT NULL, 
    due_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    status VARCHAR(40) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(counsellor_id) REFERENCES counsellors (id), 
    FOREIGN KEY(victim_id) REFERENCES victims (id)
);

CREATE INDEX ix_followups_due_at ON followups (due_at);

CREATE INDEX ix_followups_victim_id ON followups (victim_id);

CREATE TABLE alerts (
    victim_id VARCHAR(36) NOT NULL, 
    prediction_id VARCHAR(36), 
    severity VARCHAR(20) NOT NULL, 
    message TEXT NOT NULL, 
    acknowledged_by VARCHAR(36), 
    acknowledged_at TIMESTAMP WITH TIME ZONE, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(acknowledged_by) REFERENCES users (id), 
    FOREIGN KEY(prediction_id) REFERENCES distress_predictions (id), 
    FOREIGN KEY(victim_id) REFERENCES victims (id), 
    UNIQUE (prediction_id)
);

CREATE INDEX ix_alerts_victim_id ON alerts (victim_id);

CREATE TABLE case_documents (
    case_id VARCHAR(36) NOT NULL, 
    name VARCHAR(200) NOT NULL, 
    document_type VARCHAR(80) NOT NULL, 
    storage_key VARCHAR(300) NOT NULL, 
    uploaded_by VARCHAR(36) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(case_id) REFERENCES cases (id), 
    FOREIGN KEY(uploaded_by) REFERENCES users (id)
);

CREATE INDEX ix_case_documents_case_id ON case_documents (case_id);

CREATE TABLE case_events (
    case_id VARCHAR(36) NOT NULL, 
    event_type VARCHAR(80) NOT NULL, 
    stage VARCHAR(80) NOT NULL, 
    description TEXT NOT NULL, 
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    actor_id VARCHAR(36), 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(actor_id) REFERENCES users (id), 
    FOREIGN KEY(case_id) REFERENCES cases (id)
);

CREATE INDEX ix_case_events_case_id ON case_events (case_id);

CREATE INDEX ix_case_events_occurred_at ON case_events (occurred_at);

CREATE TABLE case_permissions (
    case_id VARCHAR(36) NOT NULL, 
    legal_officer_id VARCHAR(36) NOT NULL, 
    can_edit BOOLEAN NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(case_id) REFERENCES cases (id), 
    FOREIGN KEY(legal_officer_id) REFERENCES legal_officers (id), 
    UNIQUE (case_id, legal_officer_id)
);

CREATE INDEX ix_case_permissions_case_id ON case_permissions (case_id);

CREATE TABLE case_sections (
    case_id VARCHAR(36) NOT NULL, 
    act VARCHAR(200) NOT NULL, 
    section VARCHAR(80) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(case_id) REFERENCES cases (id), 
    UNIQUE (case_id, act, section)
);

CREATE INDEX ix_case_sections_case_id ON case_sections (case_id);

CREATE TABLE counselling_notes (
    followup_id VARCHAR(36) NOT NULL, 
    author_id VARCHAR(36) NOT NULL, 
    note TEXT NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(author_id) REFERENCES users (id), 
    FOREIGN KEY(followup_id) REFERENCES followups (id), 
    UNIQUE (followup_id)
);

CREATE TABLE hearings (
    case_id VARCHAR(36) NOT NULL, 
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    purpose VARCHAR(200) NOT NULL, 
    outcome TEXT, 
    status VARCHAR(40) NOT NULL, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(case_id) REFERENCES cases (id)
);

CREATE INDEX ix_hearings_case_id ON hearings (case_id);

CREATE INDEX ix_hearings_scheduled_at ON hearings (scheduled_at);

CREATE TABLE notifications (
    user_id VARCHAR(36) NOT NULL, 
    alert_id VARCHAR(36), 
    title VARCHAR(160) NOT NULL, 
    read_at TIMESTAMP WITH TIME ZONE, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(alert_id) REFERENCES alerts (id), 
    FOREIGN KEY(user_id) REFERENCES users (id), 
    UNIQUE (user_id, alert_id)
);

CREATE INDEX ix_notifications_user_id ON notifications (user_id);

CREATE TABLE notification_outbox (
    notification_id VARCHAR(36) NOT NULL, 
    channel VARCHAR(40) NOT NULL, 
    status VARCHAR(40) NOT NULL, 
    attempts INTEGER NOT NULL, 
    delivered_at TIMESTAMP WITH TIME ZONE, 
    id VARCHAR(36) NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    FOREIGN KEY(notification_id) REFERENCES notifications (id), 
    UNIQUE (notification_id)
);

INSERT INTO alembic_version (version_num) VALUES ('0b9345094ff9') RETURNING alembic_version.version_num;

-- Running upgrade 0b9345094ff9 -> 72ac9e13

CREATE TABLE user_settings (
    id VARCHAR(36) NOT NULL, 
    user_id VARCHAR(36) NOT NULL, 
    photo TEXT, 
    language VARCHAR(60) NOT NULL, 
    theme VARCHAR(20) NOT NULL, 
    text_size VARCHAR(20) NOT NULL, 
    high_contrast BOOLEAN NOT NULL, 
    reduced_motion BOOLEAN NOT NULL, 
    created_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL, 
    PRIMARY KEY (id), 
    UNIQUE (user_id), 
    FOREIGN KEY(user_id) REFERENCES users (id)
);

UPDATE alembic_version SET version_num='72ac9e13' WHERE alembic_version.version_num = '0b9345094ff9';

-- Running upgrade 72ac9e13 -> 86d8e04f1741

CREATE TABLE law_enforcement_officers (
    user_id VARCHAR(36) NOT NULL,
    police_station VARCHAR(160) NOT NULL,
    id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(user_id) REFERENCES users (id),
    UNIQUE (user_id)
);

CREATE TABLE complaints (
    victim_id VARCHAR(36) NOT NULL,
    district_id VARCHAR(36) NOT NULL,
    officer_id VARCHAR(36),
    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    incident_date DATE,
    location VARCHAR(250) NOT NULL,
    status VARCHAR(30) NOT NULL,
    id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    CHECK (status IN ('SUBMITTED', 'IN_REVIEW', 'FIR_REGISTERED', 'CLOSED')),
    FOREIGN KEY(district_id) REFERENCES districts (id),
    FOREIGN KEY(officer_id) REFERENCES law_enforcement_officers (id),
    FOREIGN KEY(victim_id) REFERENCES victims (id)
);

CREATE INDEX ix_complaints_district_id ON complaints (district_id);

CREATE INDEX ix_complaints_officer_id ON complaints (officer_id);

CREATE INDEX ix_complaints_victim_id ON complaints (victim_id);

CREATE TABLE complaint_messages (
    complaint_id VARCHAR(36) NOT NULL,
    sender_id VARCHAR(36) NOT NULL,
    body TEXT NOT NULL,
    id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(complaint_id) REFERENCES complaints (id),
    FOREIGN KEY(sender_id) REFERENCES users (id)
);

CREATE INDEX ix_complaint_messages_complaint_id ON complaint_messages (complaint_id);

CREATE TABLE fir_registrations (
    complaint_id VARCHAR(36) NOT NULL,
    registered_by VARCHAR(36) NOT NULL,
    district_id VARCHAR(36) NOT NULL,
    number VARCHAR(80) NOT NULL,
    police_station VARCHAR(160) NOT NULL,
    registered_on DATE NOT NULL,
    registration_year INTEGER NOT NULL,
    id VARCHAR(36) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY(complaint_id) REFERENCES complaints (id),
    FOREIGN KEY(district_id) REFERENCES districts (id),
    FOREIGN KEY(registered_by) REFERENCES law_enforcement_officers (id),
    UNIQUE (complaint_id),
    CONSTRAINT uq_fir_reference UNIQUE (district_id, police_station, registration_year, number)
);

CREATE INDEX ix_fir_registrations_district_id ON fir_registrations (district_id);

ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(15);

UPDATE alembic_version SET version_num='86d8e04f1741' WHERE alembic_version.version_num = '72ac9e13';

COMMIT;

