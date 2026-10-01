DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);

CREATE TABLE patients (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL,
    age            INTEGER NOT NULL CHECK (age BETWEEN 0 AND 120),
    gender         TEXT    NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    phone          TEXT,
    address        TEXT,
    blood_group    TEXT,
    height_cm      REAL    NOT NULL,
    weight_kg      REAL    NOT NULL,
    bmi            REAL    NOT NULL,
    blood_sugar    REAL    NOT NULL,           -- fasting, mg/dL
    bp_systolic    INTEGER,
    bp_diastolic   INTEGER,
    disease        TEXT    NOT NULL,
    doctor         TEXT,
    admission_date TEXT    NOT NULL,           -- YYYY-MM-DD
    notes          TEXT,
    created_at     TEXT    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
