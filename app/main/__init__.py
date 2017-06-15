from flask import Blueprint

from app.main.stats import StatsManager

main = Blueprint('main', __name__)
thread = None
stats = StatsManager()

from . import routes, sockets
