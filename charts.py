"""Matplotlib charts built from the preprocessed DataFrame.

Figures are created with matplotlib.figure.Figure (not pyplot) because pyplot
is not safe to use from a multi-threaded web server.
"""
import io

from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator

# Colours: one blue for single-series charts; a fixed colour per gender so
# "Female" is the same colour in the pie chart and the scatter plot.
PRIMARY = "#2a78d6"
GENDER_COLORS = {"Male": "#2a78d6", "Female": "#eb6834", "Other": "#1baf7a"}
SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_SECONDARY = "#52514e"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"


def new_figure(title, figsize=(7, 4.5)):
    fig = Figure(figsize=figsize, facecolor=SURFACE, layout="constrained")
    ax = fig.subplots()
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=13, color=TEXT, pad=12)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(AXIS)
    ax.tick_params(colors=TEXT_SECONDARY, labelsize=9)
    ax.xaxis.label.set_color(TEXT_SECONDARY)
    ax.yaxis.label.set_color(TEXT_SECONDARY)
    ax.set_axisbelow(True)
    return fig, ax


def disease_bar(df):
    """Bar chart: number of patients per disease."""
    counts = df["disease"].value_counts().sort_values()
    fig, ax = new_figure("Patients per Disease")
    bars = ax.barh(counts.index, counts.values, color=PRIMARY, height=0.6)
    ax.bar_label(bars, padding=4, color=TEXT_SECONDARY, fontsize=9)
    ax.set_xlabel("Number of patients")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="x", color=GRID, linewidth=0.8)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return fig


def gender_pie(df):
    """Pie chart: gender distribution."""
    counts = df["gender"].value_counts()
    fig, ax = new_figure("Gender Distribution")
    _, _, percent_labels = ax.pie(
        counts.values,
        labels=[f"{g} ({n})" for g, n in counts.items()],
        colors=[GENDER_COLORS.get(g, "#898781") for g in counts.index],
        # Slices under 5% are too thin to hold a label; the outer label still shows the count
        autopct=lambda pct: f"{pct:.1f}%" if pct >= 5 else "",
        pctdistance=0.72, startangle=90, counterclock=False,
        wedgeprops={"edgecolor": SURFACE, "linewidth": 2},
        textprops={"color": TEXT, "fontsize": 10},
    )
    for text in percent_labels:  # these sit on the coloured wedges
        text.set_color("white")
        text.set_fontweight("bold")
    ax.axis("equal")
    return fig


def age_histogram(df):
    """Histogram: age distribution in 10-year bins."""
    fig, ax = new_figure("Age Distribution")
    ax.hist(df["age"], bins=range(0, 101, 10), color=PRIMARY,
            edgecolor=SURFACE, linewidth=2)
    mean_age = df["age"].mean()
    ax.axvline(mean_age, color=TEXT_SECONDARY, linestyle="--", linewidth=1.2)
    ax.annotate(f"Mean {mean_age:.1f} yrs", xy=(mean_age, 1), xycoords=("data", "axes fraction"),
                xytext=(5, -12), textcoords="offset points", color=TEXT_SECONDARY, fontsize=9)
    ax.set_xticks(range(0, 101, 10))
    ax.set_xlabel("Age (years)")
    ax.set_ylabel("Number of patients")
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    return fig


def admissions_line(df):
    """Line graph: admissions per month."""
    monthly = (df.dropna(subset=["admission_date"])
                 .set_index("admission_date")
                 .resample("MS").size())
    fig, ax = new_figure("Admissions per Month")
    labels = monthly.index.strftime("%b %y")
    ax.plot(labels, monthly.values, color=PRIMARY, linewidth=2,
            marker="o", markersize=6, markerfacecolor=PRIMARY,
            markeredgecolor=SURFACE, markeredgewidth=1.5)
    if len(monthly):
        # Label only the latest month instead of every point
        ax.annotate(str(monthly.values[-1]), xy=(len(monthly) - 1, monthly.values[-1]),
                    xytext=(0, -16), textcoords="offset points", ha="center",
                    color=TEXT, fontsize=9, fontweight="bold")
    ax.set_ylabel("Admissions")
    ax.set_ylim(bottom=0)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(axis="x", rotation=45)
    return fig


def bmi_sugar_scatter(df):
    """Scatter plot: BMI vs blood sugar, coloured by gender."""
    fig, ax = new_figure("BMI vs Blood Sugar")
    for gender, group in df.groupby("gender"):
        ax.scatter(group["bmi"], group["blood_sugar"], label=gender, s=40, alpha=0.85,
                   color=GENDER_COLORS.get(gender, "#898781"),
                   edgecolors=SURFACE, linewidths=1)
    # Reference lines: overweight BMI and the diabetic sugar threshold
    ax.axvline(25, color=AXIS, linestyle="--", linewidth=1)
    ax.axhline(126, color=AXIS, linestyle="--", linewidth=1)
    ax.annotate("Diabetic (≥126)", xy=(1, 126), xycoords=("axes fraction", "data"),
                xytext=(-4, 4), textcoords="offset points", ha="right",
                color=TEXT_SECONDARY, fontsize=8)
    ax.annotate("Overweight (≥25)", xy=(25, 1), xycoords=("data", "axes fraction"),
                xytext=(4, -12), textcoords="offset points",
                color=TEXT_SECONDARY, fontsize=8)
    ax.set_xlabel("BMI (kg/m²)")
    ax.set_ylabel("Blood sugar (mg/dL)")
    ax.grid(color=GRID, linewidth=0.8)
    ax.legend(frameon=False, labelcolor=TEXT_SECONDARY, fontsize=9, loc="upper left")
    return fig


# name used in the URL -> (title, function)
CHARTS = {
    "disease": ("Patients per Disease", disease_bar),
    "gender": ("Gender Distribution", gender_pie),
    "age": ("Age Distribution", age_histogram),
    "admissions": ("Admissions per Month", admissions_line),
    "bmi-sugar": ("BMI vs Blood Sugar", bmi_sugar_scatter),
}


def build_chart(name, df):
    title, chart_function = CHARTS[name]
    if df.empty:
        fig, ax = new_figure(title)
        ax.axis("off")
        ax.text(0.5, 0.5, "No patient data yet", ha="center", va="center",
                color=TEXT_SECONDARY, fontsize=12, transform=ax.transAxes)
        return fig
    return chart_function(df)


def to_png(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=110)
    return buffer.getvalue()
