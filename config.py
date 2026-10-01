import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    # Change SECRET_KEY (or set the environment variable) before deploying anywhere public
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-this-secret-key")
    DATABASE = os.path.join(BASE_DIR, "medianalytics.db")
