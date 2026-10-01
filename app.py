"""MediAnalytics: Hospital Patient Data Analyzer and Visualization System.

Run with:  python app.py   (or:  flask --app app run)
"""
import os

import click
from flask import Flask, Response, abort, render_template

import analytics
import charts
import db
import seed
from auth import bp as auth_bp, login_required
from config import Config
from patients import bp as patients_bp
from reports import bp as reports_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(reports_bp)
    app.add_template_filter(analytics.bmi_category, "bmi_category")
    app.add_template_filter(analytics.sugar_status, "sugar_status")

    @app.route("/")
    @login_required
    def dashboard():
        df = analytics.preprocess(analytics.load_df())
        stats = analytics.summary_stats(df)
        return render_template("dashboard.html", stats=stats, charts=charts.CHARTS)

    @app.route("/charts/<name>.png")
    @login_required
    def chart_image(name):
        if name not in charts.CHARTS:
            abort(404)
        df = analytics.preprocess(analytics.load_df())
        png = charts.to_png(charts.build_chart(name, df))
        return Response(png, mimetype="image/png", headers={"Cache-Control": "no-store"})

    @app.cli.command("seed")
    @click.option("--count", default=100, help="Number of fake patients to generate.")
    def seed_command(count):
        """Replace all patients with generated sample data."""
        seed.seed_database(count)
        click.echo(f"Added {count} sample patients. Login: {seed.DEFAULT_ADMIN[0]} / {seed.DEFAULT_ADMIN[1]}")

    # First run: create the database with sample data so the app works immediately
    if not os.path.exists(app.config["DATABASE"]):
        with app.app_context():
            db.init_db()
            seed.seed_database()
        print("Created medianalytics.db with 100 sample patients (login: admin / admin123)")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
