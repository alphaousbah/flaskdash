from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from flask_migrate import Migrate

db = SQLAlchemy()
session = db.session
migrate = Migrate()
