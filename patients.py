"""Patient records: add, view, update, delete and search."""
from datetime import date, datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from auth import login_required
from db import get_db

bp = Blueprint("patients", __name__, url_prefix="/patients")

GENDERS = ("Male", "Female", "Other")
BLOOD_GROUPS = ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")
COMMON_DISEASES = (
    "Asthma", "Dengue", "Diabetes", "Heart Disease", "Hypertension",
    "Migraine", "Thyroid Disorder", "Typhoid", "Viral Fever",
)

TEXT_FIELDS = ("name", "gender", "phone", "address", "blood_group",
               "disease", "doctor", "admission_date", "notes")
OPTIONAL_TEXT_FIELDS = ("phone", "address", "blood_group", "doctor", "notes")

# (field, label, minimum, maximum, type, required)
NUMERIC_FIELDS = (
    ("age", "Age", 0, 120, int, True),
    ("height_cm", "Height (cm)", 30, 250, float, True),
    ("weight_kg", "Weight (kg)", 1, 300, float, True),
    ("blood_sugar", "Blood sugar (mg/dL)", 20, 600, float, True),
    ("bp_systolic", "Systolic BP", 50, 250, int, False),
    ("bp_diastolic", "Diastolic BP", 30, 150, int, False),
)

DB_COLUMNS = ("name", "age", "gender", "phone", "address", "blood_group",
              "height_cm", "weight_kg", "bmi", "blood_sugar", "bp_systolic",
              "bp_diastolic", "disease", "doctor", "admission_date", "notes")


def calculate_bmi(height_cm, weight_kg):
    """Body Mass Index = weight (kg) / height (m)^2"""
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def validate(form):
    """Check the submitted form. Returns (data, errors)."""
    data = {field: form.get(field, "").strip() for field in TEXT_FIELDS}
    errors = []

    if not data["name"]:
        errors.append("Name is required.")
    if data["gender"] not in GENDERS:
        errors.append("Please select a gender.")
    if data["blood_group"] and data["blood_group"] not in BLOOD_GROUPS:
        errors.append("Please select a valid blood group.")
    if not data["disease"]:
        errors.append("Disease / diagnosis is required.")
    if data["phone"] and not (data["phone"].isdigit() and len(data["phone"]) == 10):
        errors.append("Phone number must be exactly 10 digits.")
    try:
        admitted = datetime.strptime(data["admission_date"], "%Y-%m-%d").date()
        if admitted > date.today():
            errors.append("Admission date cannot be in the future.")
    except ValueError:
        errors.append("Please enter a valid admission date.")

    for field, label, low, high, cast, required in NUMERIC_FIELDS:
        raw = form.get(field, "").strip()
        data[field] = None
        if not raw:
            if required:
                errors.append(f"{label} is required.")
            continue
        try:
            value = cast(raw)
        except ValueError:
            errors.append(f"{label} must be a valid number.")
            continue
        if not low <= value <= high:
            errors.append(f"{label} must be between {low} and {high}.")
        data[field] = value

    if data["bp_systolic"] and data["bp_diastolic"] and data["bp_diastolic"] >= data["bp_systolic"]:
        errors.append("Diastolic BP must be lower than systolic BP.")

    if not errors:
        data["bmi"] = calculate_bmi(data["height_cm"], data["weight_kg"])
        for field in OPTIONAL_TEXT_FIELDS:
            data[field] = data[field] or None  # store blanks as NULL
    return data, errors


def build_search_query(q="", gender=""):
    """SQL and parameters for listing patients, filtered by search text and gender."""
    sql = "SELECT * FROM patients WHERE 1 = 1"
    params = []
    if q:
        like = f"%{q}%"
        sql += " AND (name LIKE ? OR disease LIKE ? OR doctor LIKE ? OR CAST(id AS TEXT) = ?)"
        params += [like, like, like, q.lstrip("#")]
    if gender in GENDERS:
        sql += " AND gender = ?"
        params.append(gender)
    return sql + " ORDER BY id DESC", params


def get_patient(patient_id):
    patient = get_db().execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    if patient is None:
        abort(404, f"Patient #{patient_id} does not exist.")
    return patient


def render_form(patient, patient_id=None):
    return render_template(
        "patients/form.html", patient=patient, patient_id=patient_id,
        genders=GENDERS, blood_groups=BLOOD_GROUPS, diseases=COMMON_DISEASES,
        today=date.today().isoformat(),
    )


@bp.route("/")
@login_required
def list_patients():
    q = request.args.get("q", "").strip()
    gender = request.args.get("gender", "")
    sql, params = build_search_query(q, gender)
    patients = get_db().execute(sql, params).fetchall()
    return render_template("patients/list.html", patients=patients,
                           q=q, gender=gender, genders=GENDERS)


@bp.route("/add", methods=("GET", "POST"))
@login_required
def add():
    if request.method == "POST":
        data, errors = validate(request.form)
        if not errors:
            placeholders = ", ".join(["?"] * len(DB_COLUMNS))
            db = get_db()
            cursor = db.execute(
                f"INSERT INTO patients ({', '.join(DB_COLUMNS)}) VALUES ({placeholders})",
                [data[col] for col in DB_COLUMNS],
            )
            db.commit()
            flash(f"Patient {data['name']} registered successfully.", "success")
            return redirect(url_for("patients.detail", patient_id=cursor.lastrowid))
        for error in errors:
            flash(error, "error")
        return render_form(request.form)

    return render_form({"admission_date": date.today().isoformat()})


@bp.route("/<int:patient_id>")
@login_required
def detail(patient_id):
    return render_template("patients/detail.html", patient=get_patient(patient_id))


@bp.route("/<int:patient_id>/edit", methods=("GET", "POST"))
@login_required
def edit(patient_id):
    patient = get_patient(patient_id)

    if request.method == "POST":
        data, errors = validate(request.form)
        if not errors:
            assignments = ", ".join(f"{col} = ?" for col in DB_COLUMNS)
            db = get_db()
            db.execute(
                f"UPDATE patients SET {assignments} WHERE id = ?",
                [data[col] for col in DB_COLUMNS] + [patient_id],
            )
            db.commit()
            flash("Patient record updated.", "success")
            return redirect(url_for("patients.detail", patient_id=patient_id))
        for error in errors:
            flash(error, "error")
        return render_form(request.form, patient_id)

    return render_form(dict(patient), patient_id)


@bp.route("/<int:patient_id>/delete", methods=("POST",))
@login_required
def delete(patient_id):
    patient = get_patient(patient_id)
    db = get_db()
    db.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    db.commit()
    flash(f"Patient {patient['name']} was deleted.", "info")
    return redirect(url_for("patients.list_patients"))
