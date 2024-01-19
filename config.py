import os
from pathlib import Path


class Config:
    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://{dbuser}:{dbpass}@{dbhost}/{dbname}'.format(
        dbhost=os.environ['POSTGRES_HOST'],
        dbuser=os.environ['POSTGRES_USER'],
        dbpass=os.environ['POSTGRES_PASSWORD'],
        dbname=os.environ['POSTGRES_DB'],
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class SQLiteConfig:
    SECRET_KEY = os.environ['SECRET_KEY']
    BASE_DIR = Path(__file__).resolve().parent
    DBNAME = 'app_db.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR}/{DBNAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
