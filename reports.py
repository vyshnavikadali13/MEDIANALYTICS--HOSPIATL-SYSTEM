"""Report generation: CSV export of patient data and a PDF analytics report."""
import io
from datetime import date, datetime

from flask import Blueprint, Response, request, send_file
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.figure import Figure

from analytics import load_df, preprocess, summary_stats
from auth import login_required
from charts import CHARTS, SURFACE, TEXT, TEXT_SECONDARY, build_chart

bp = Blueprint("reports", __name__, url_prefix="/export")


@bp.route("/csv")
@login_required
def export_csv():
    """Download the patient list (respecting the current search filters) as CSV."""
    df = load_df(request.args.get("q", "").strip(), request.args.get("gender", ""))
    # utf-8-sig adds a byte-order mark so Excel opens the file with the right encoding
    csv_bytes = df.to_csv(index=False).encode("utf-8-sig")
    return Response(
        csv_bytes, mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=patients_{date.today()}.csv"},
    )


def summary_page(stats):
    """First page of the PDF: the statistical summary as text (A4 portrait)."""
    page_height = 11.69  # inches
    fig = Figure(figsize=(8.27, page_height), facecolor=SURFACE)
    y = 0.95  # current position, as a fraction of the page height

    def write(text="", size=11, color=TEXT, bold=False, mono=False):
        nonlocal y
        fig.text(0.08, y, text, fontsize=size, color=color, va="top",
                 fontweight="bold" if bold else "normal",
                 family="monospace" if mono else "sans-serif")
        y -= size * 1.6 / 72 / page_height  # move down 1.6 line-heights

    def row(label, *values, **style):
        """A fixed-width table row: left-aligned label, right-aligned values."""
        write(f"{label:<24}" + "".join(f"{v:>9}" for v in values), size=10, mono=True, **style)

    write("MediAnalytics - Patient Analytics Report", size=18, bold=True)
    write(f"Generated on {datetime.now():%d %B %Y, %I:%M %p}", size=10, color=TEXT_SECONDARY)
    write()

    if stats["total"] == 0:
        write("No patient records found.")
        return fig

    write("Overview", size=13, bold=True)
    write(f"Total patients: {stats['total']}")
    write(f"Diabetic patients (fasting sugar >= 126 mg/dL): {stats['diabetic']}")
    if stats["bmi_sugar_correlation"] is not None:
        write(f"Correlation between BMI and blood sugar: {stats['bmi_sugar_correlation']}")
    write(size=6)

    write("Statistical measures", size=13, bold=True)
    row("Measure", "Mean", "Median", "Std", "Min", "Max", color=TEXT_SECONDARY, bold=True)
    for label, key in (("Age (years)", "age"), ("BMI (kg/m2)", "bmi"), ("Blood sugar (mg/dL)", "sugar")):
        s = stats[key]
        row(label, s["mean"], s["median"], s["std"], s["min"], s["max"])

    for title, key in (("Patients by disease", "by_disease"), ("Patients by gender", "by_gender"),
                       ("Patients by BMI category", "by_bmi_category"),
                       ("Patients by sugar status", "by_sugar_status")):
        write(size=6)
        write(title, size=13, bold=True)
        for name, count in stats[key].items():
            row(name, count)
    return fig


@bp.route("/pdf")
@login_required
def export_pdf():
    """Download a multi-page PDF: summary statistics followed by all five charts."""
    df = preprocess(load_df())
    buffer = io.BytesIO()
    with PdfPages(buffer) as pdf:
        pdf.savefig(summary_page(summary_stats(df)))
        for name in CHARTS:
            pdf.savefig(build_chart(name, df))
        info = pdf.infodict()
        info["Title"] = "MediAnalytics Patient Analytics Report"
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True,
                     download_name=f"medianalytics_report_{date.today()}.pdf")
