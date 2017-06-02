from flask import Blueprint

main = Blueprint('main', __name__)
thread = None

from . import routes, sockets
