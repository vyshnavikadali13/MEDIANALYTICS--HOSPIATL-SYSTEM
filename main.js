// MediAnalytics front-end helpers (plain JavaScript, no libraries)

document.addEventListener("DOMContentLoaded", () => {
  setupDeleteConfirmation();
  setupBmiPreview();
  setupFormValidation();
  setupLiveSearch();
});

// Ask before deleting a patient
function setupDeleteConfirmation() {
  document.querySelectorAll("form.delete-form").forEach((form) => {
    form.addEventListener("submit", (event) => {
      const name = form.dataset.name || "this patient";
      if (!confirm(`Delete ${name}'s record? This cannot be undone.`)) {
        event.preventDefault();
      }
    });
  });
}

// Same categories as analytics.py (WHO BMI ranges)
function bmiCategory(bmi) {
  if (bmi < 18.5) return "Underweight";
  if (bmi < 25) return "Normal";
  if (bmi < 30) return "Overweight";
  return "Obese";
}

// Show the BMI while height and weight are being typed
function setupBmiPreview() {
  const height = document.getElementById("height_cm");
  const weight = document.getElementById("weight_kg");
  const output = document.getElementById("bmi-preview");
  if (!height || !weight || !output) return;

  const update = () => {
    const heightM = parseFloat(height.value) / 100;
    const weightKg = parseFloat(weight.value);
    if (heightM > 0 && weightKg > 0) {
      const bmi = weightKg / (heightM * heightM);
      output.textContent = `${bmi.toFixed(1)} (${bmiCategory(bmi)})`;
    } else {
      output.textContent = "—";
    }
  };
  height.addEventListener("input", update);
  weight.addEventListener("input", update);
  update();
}

// Check the patient form before sending it (the server checks again)
function setupFormValidation() {
  const form = document.getElementById("patient-form");
  if (!form) return;
  const box = document.getElementById("form-errors");
  const field = (name) => form.elements.namedItem(name);

  form.addEventListener("submit", (event) => {
    const errors = [];

    // Built-in checks from the HTML attributes (required, min, max, pattern)
    for (const input of form.querySelectorAll("input, select, textarea")) {
      input.classList.remove("invalid");
      if (!input.checkValidity()) {
        input.classList.add("invalid");
        const label = form.querySelector(`label[for="${input.id}"]`);
        errors.push(`${label ? label.textContent.replace(" *", "") : input.name}: ${input.validationMessage}`);
      }
    }

    if (!field("name").value.trim()) {
      errors.push("Full name cannot be blank.");
    }
    const systolic = parseInt(field("bp_systolic").value, 10);
    const diastolic = parseInt(field("bp_diastolic").value, 10);
    if (systolic && diastolic && diastolic >= systolic) {
      errors.push("Diastolic BP must be lower than systolic BP.");
    }
    if (errors.length) {
      event.preventDefault();
      box.innerHTML = "<strong>Please fix the following:</strong><ul>" +
        errors.map((e) => `<li>${escapeHtml(e)}</li>`).join("") + "</ul>";
      box.hidden = false;
      box.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  });
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// Filter the patient table instantly while typing (press Enter for a full server search)
function setupLiveSearch() {
  const input = document.getElementById("live-search");
  const rows = document.querySelectorAll("#patients-table tbody tr");
  const count = document.getElementById("result-count");
  if (!input || !rows.length) return;

  input.addEventListener("input", () => {
    const term = input.value.trim().toLowerCase();
    let shown = 0;
    rows.forEach((row) => {
      const match = row.dataset.search.includes(term);
      row.hidden = !match;
      if (match) shown++;
    });
    if (count) count.textContent = shown;
  });
}
