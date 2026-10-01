# MediAnalytics: Hospital Patient Data Analyzer and Visualization System

A Flask web application for hospital staff to manage patient records and analyse them with
NumPy, Pandas and Matplotlib.

**Tech stack:** Python, Flask, SQLite, HTML, CSS, JavaScript, NumPy, Pandas, Matplotlib

## How to run

You need **Python 3.10–3.13** and about 5 minutes. Follow the steps for your operating system.

> **Which Python?** Use **Python 3.12 or 3.13**. Avoid 3.14 for now — some of the required
> libraries (NumPy, Pandas, Matplotlib) may not have ready-to-install versions for it yet, which
> can make step 4 fail. Check your version with `python --version`.

### Step 1 — Install Python

1. Download the installer from <https://www.python.org/downloads/> (pick **3.13** or **3.12**).
2. **Windows only:** on the first screen of the installer, tick **"Add python.exe to PATH"**
   before clicking *Install Now*. This is easy to miss and nothing below will work without it.
3. Close and reopen your terminal after installing.

### Step 2 — Open a terminal in this project folder

Open a terminal (Command Prompt, PowerShell, or Git Bash on Windows; Terminal on macOS/Linux)
and move into the folder that contains this README:

```
cd path/to/MediAnalytics
```

Confirm Python is ready — this should print a version number like `Python 3.13.x`:

```
python --version
```

If it says *"Python was not found"* on Windows, see **Troubleshooting** at the bottom.

### Step 3 — Create and activate a virtual environment

A virtual environment keeps this project's libraries separate from the rest of your computer.

**Create it** (do this once):

```
python -m venv venv
```

**Activate it** — use the line that matches your terminal:

| Terminal | Command to activate |
|---|---|
| Windows – Command Prompt (cmd) | `venv\Scripts\activate.bat` |
| Windows – PowerShell | `venv\Scripts\Activate.ps1` |
| Windows – Git Bash | `source venv/Scripts/activate` |
| macOS / Linux | `source venv/bin/activate` |

When it works, your prompt shows `(venv)` at the start of the line. You must activate the
environment every time you open a new terminal to work on this project.

### Step 4 — Install the libraries (once)

```
pip install -r requirements.txt
```

### Step 5 — Start the app

```
python app.py
```

Leave this terminal running. On the **first run** it automatically creates `medianalytics.db`
with 100 sample patients, so there is no separate database setup.

### Step 6 — Open it in your browser

Go to **<http://127.0.0.1:5000>** and log in with:

- **Username:** `admin`
- **Password:** `admin123`

To stop the app, click the terminal and press **Ctrl + C**.

### Useful commands

| Command | What it does |
|---|---|
| `flask --app app init-db` | Delete everything and create empty tables |
| `flask --app app seed` | Replace all patients with 100 generated sample patients (also creates the admin user) |
| `flask --app app seed --count 250` | Same, with 250 patients |

## Features

- **Staff login**: passwords are stored as salted hashes (`werkzeug.security`); every page needs a login.
- **Patient management**: register, view, edit, delete and search patients (by name, `#ID`, disease or doctor, with a gender filter).
- **Validation**: in the browser (JavaScript) for quick feedback, and again on the server.
- **Automatic BMI**: calculated when a patient is saved and previewed live while typing.
- **Dashboard**: summary cards, 5 Matplotlib charts, a statistics table and category breakdowns.
- **Reports**: CSV export of the patient list (respects the current search) and a PDF analytics report.

## Data analytics pipeline (DAE concepts)

| Stage | Where | What happens |
|---|---|---|
| Data collection | `patients.py` (forms), `seed.py` | Staff enter records; the seed script generates realistic sample data with NumPy random distributions |
| Storage | `schema.sql`, `db.py` | SQLite tables with constraints (`CHECK`, `NOT NULL`) |
| Preprocessing | `analytics.preprocess()` | Type conversion, text standardisation, dropping incomplete rows, BMI recalculation, derived columns (`age_group`, `bmi_category`, `sugar_status`) using `pd.cut` |
| Statistical analysis | `analytics.summary_stats()` | Mean, median, standard deviation, min and max with NumPy; distributions with `value_counts()`; BMI vs sugar correlation with `np.corrcoef` |
| Visualization | `charts.py` | Bar (patients per disease), pie (gender), histogram (age), line (admissions per month), scatter (BMI vs blood sugar) |
| Report generation | `reports.py` | CSV via `DataFrame.to_csv`; multi-page PDF via Matplotlib `PdfPages` |

Medical thresholds used:
- **BMI** (WHO): Underweight < 18.5 ≤ Normal < 25 ≤ Overweight < 30 ≤ Obese
- **Fasting blood sugar** (mg/dL): Normal < 100 ≤ Prediabetic < 126 ≤ Diabetic

## Project structure

```
MediAnalytics/
├── app.py            # creates the Flask app, dashboard + chart routes, CLI commands
├── config.py         # secret key and database path
├── db.py             # SQLite connection helpers, init-db command
├── schema.sql        # users and patients tables
├── auth.py           # login / logout, login_required decorator
├── patients.py       # add / view / edit / delete / search, form validation, BMI
├── analytics.py      # Pandas + NumPy: load, preprocess, statistics
├── charts.py         # Matplotlib charts
├── reports.py        # CSV and PDF export
├── seed.py           # sample data generator
├── templates/        # Jinja2 HTML pages
└── static/           # style.css, main.js
```

## Troubleshooting

**"Python was not found" on Windows, even after installing it.**
Windows ships a fake `python` that only opens the Microsoft Store. Turn it off:
open **Settings → Apps → Advanced app settings → App execution aliases** and switch **Off** the
entries for **python.exe** and **python3.exe**. Then close and reopen your terminal. If the
installer's *"Add python.exe to PATH"* box was missed, the simplest fix is to re-run the
installer and tick it (or choose *Modify*).

**`Activate.ps1` is blocked in PowerShell** (*"running scripts is disabled on this system"*).
Run this once, then activate again:
```
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```
Or just use Command Prompt instead, where `venv\Scripts\activate.bat` needs no such change.

**`pip install` fails while building numpy / pandas / matplotlib.**
You are almost certainly on Python 3.14 (or newer). Delete the `venv` folder, install
**Python 3.13**, and start again from Step 3. Check with `python --version` first.

**"Unable to copy ... python.exe" when creating the venv.**
The app is still running from a previous session and is locking the file. Stop it with
**Ctrl + C** in the terminal that is running `python app.py`, then recreate the environment with
`python -m venv --clear venv`.

**Port 5000 is already in use.**
Another program is on that port. Stop it, or run the app on a different port with
`flask --app app run --port 5001` and open <http://127.0.0.1:5001> instead.

## Notes

- Sample patient names, phone numbers and addresses are randomly generated, not real people.
- Before hosting the app anywhere public, set a strong `SECRET_KEY` environment variable and change the admin password.
