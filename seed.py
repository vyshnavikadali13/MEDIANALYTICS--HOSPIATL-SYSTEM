"""Generate realistic (but fake) patient records for demos and testing."""
from datetime import date, timedelta

import numpy as np
from werkzeug.security import generate_password_hash

from db import get_db
from patients import DB_COLUMNS, calculate_bmi

DEFAULT_ADMIN = ("admin", "admin123")

FIRST_NAMES = {
    "Male": ["Arjun", "Rahul", "Vikram", "Suresh", "Kiran", "Ravi", "Anil", "Harsha",
             "Venkat", "Srinivas", "Mahesh", "Aditya", "Rohit", "Naveen", "Praveen", "Sai"],
    "Female": ["Priya", "Lakshmi", "Divya", "Swathi", "Keerthi", "Anusha", "Sravani", "Pooja",
               "Meena", "Kavya", "Sneha", "Harika", "Bhavana", "Deepika", "Ramya", "Sindhu"],
}
SURNAMES = ["Reddy", "Rao", "Sharma", "Naidu", "Kumar", "Varma", "Chowdary", "Goud",
            "Patel", "Iyer", "Gupta", "Murthy", "Prasad", "Shetty"]
AREAS = ["Kukatpally", "Ameerpet", "Madhapur", "Gachibowli", "Secunderabad", "Dilsukhnagar",
         "LB Nagar", "Miyapur", "Begumpet", "Uppal", "Kondapur", "Mehdipatnam"]
DOCTORS = ["Dr. A. Sharma", "Dr. K. Reddy", "Dr. S. Rao", "Dr. M. Iyer", "Dr. P. Naidu"]

# disease: (share of patients, mean age, std of age)
DISEASES = {
    "Diabetes": (0.18, 55, 12),
    "Hypertension": (0.15, 58, 11),
    "Heart Disease": (0.08, 62, 10),
    "Thyroid Disorder": (0.08, 40, 12),
    "Asthma": (0.10, 30, 16),
    "Migraine": (0.08, 32, 10),
    "Viral Fever": (0.15, 28, 18),
    "Typhoid": (0.09, 25, 14),
    "Dengue": (0.09, 27, 13),
}
BLOOD_GROUPS = {"B+": 0.33, "O+": 0.30, "A+": 0.22, "AB+": 0.08,
                "O-": 0.02, "A-": 0.02, "B-": 0.02, "AB-": 0.01}


def make_patient(rng, today):
    gender = str(rng.choice(["Male", "Female", "Other"], p=[0.49, 0.49, 0.02]))
    first_names = FIRST_NAMES.get(gender, FIRST_NAMES["Male"] + FIRST_NAMES["Female"])
    name = f"{rng.choice(first_names)} {rng.choice(SURNAMES)}"

    disease = str(rng.choice(list(DISEASES), p=[d[0] for d in DISEASES.values()]))
    _, mean_age, sd_age = DISEASES[disease]
    age = int(np.clip(rng.normal(mean_age, sd_age), 2, 90))

    # Height: adults by gender, children grow roughly 6 cm a year
    adult_height = rng.normal(168, 7) if gender == "Male" else rng.normal(155, 6)
    height = adult_height if age >= 18 else min(adult_height, 75 + 5.8 * age + rng.normal(0, 4))

    # Weight from a target BMI; lifestyle diseases push BMI up
    target_bmi = rng.normal(17, 2) if age < 18 else rng.normal(24, 3.5)
    if disease in ("Diabetes", "Hypertension", "Heart Disease"):
        target_bmi += 3
    weight = round(float(np.clip(target_bmi * (height / 100) ** 2, 8, 180)), 1)
    height = round(float(height), 1)
    bmi = calculate_bmi(height, weight)

    # Fasting blood sugar: high for diabetics, slightly higher with higher BMI
    if disease == "Diabetes":
        sugar = rng.normal(175, 35)
    else:
        sugar = rng.normal(92, 9) + max(0, bmi - 25) * 2.5
    sugar = round(float(np.clip(sugar, 65, 400)), 1)

    systolic = rng.normal(115, 9) + max(0, age - 40) * 0.4
    if disease in ("Hypertension", "Heart Disease"):
        systolic += 28
    systolic = int(np.clip(systolic, 85, 210))
    diastolic = int(np.clip(systolic * 0.65 + rng.normal(0, 4), 50, systolic - 20))

    # More admissions in recent months, so the trend line has a shape
    days_ago = int(rng.triangular(0, 0, 365))

    return {
        "name": name,
        "age": age,
        "gender": gender,
        "phone": "9" + "".join(str(d) for d in rng.integers(0, 10, 9)),
        "address": f"{rng.choice(AREAS)}, Hyderabad",
        "blood_group": str(rng.choice(list(BLOOD_GROUPS), p=list(BLOOD_GROUPS.values()))),
        "height_cm": height,
        "weight_kg": weight,
        "bmi": bmi,
        "blood_sugar": sugar,
        "bp_systolic": systolic,
        "bp_diastolic": diastolic,
        "disease": disease,
        "doctor": str(rng.choice(DOCTORS)),
        "admission_date": (today - timedelta(days=days_ago)).isoformat(),
        "notes": None,
    }


def seed_database(count=100, random_seed=4):
    """Replace all patients with `count` generated ones and make sure the admin user exists."""
    rng = np.random.default_rng(random_seed)
    today = date.today()
    db = get_db()

    username, password = DEFAULT_ADMIN
    db.execute("INSERT OR IGNORE INTO users (username, password_hash) VALUES (?, ?)",
               (username, generate_password_hash(password)))

    db.execute("DELETE FROM patients")
    db.execute("DELETE FROM sqlite_sequence WHERE name = 'patients'")  # restart IDs at 1
    rows = [make_patient(rng, today) for _ in range(count)]
    placeholders = ", ".join(["?"] * len(DB_COLUMNS))
    db.executemany(
        f"INSERT INTO patients ({', '.join(DB_COLUMNS)}) VALUES ({placeholders})",
        [[row[col] for col in DB_COLUMNS] for row in rows],
    )
    db.commit()
    return count
