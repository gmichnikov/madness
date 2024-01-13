from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config.from_object('config')

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

from .models import Region
with app.app_context():
    if Region.query.count() == 0:
        for i in range(1, 5):
            db.session.add(Region(name=f"Region {i}"))
        db.session.commit()