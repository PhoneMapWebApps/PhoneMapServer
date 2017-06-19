import os

from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

socketio = SocketIO()
db = SQLAlchemy()
login_manager = LoginManager()
app = Flask(__name__)

def create_app(debug=False, testing=False):
    if testing:
        if os.path.isfile("config.py"):
            print("using custom config")
            app.config.from_object("config.Testing")
        else:
            app.config.from_object("sampleconfig.Testing")
    else:
        app.config.from_object("config.Development")

    app.debug = debug

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    socketio.init_app(app)

    db.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = "main.login"

    # use correct app context
    with app.app_context():
        db.create_all()
        from app.main.models import Users
        if not Users.query.get(1):  # 1 == root user
            root = Users("root", "toor", "Admin", "No Org")
            db.session.add(root)
            db.session.commit()
