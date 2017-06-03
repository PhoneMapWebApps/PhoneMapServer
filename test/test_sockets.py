import unittest

from app import create_app, app, db, socketio


class TestSockets(unittest.TestCase):
    def setUp(self):
        create_app(False, True)

    def test_socket_idk(self):
        # TODO: this
        pass

    def tearDown(self):
        with app.app_context():
            db.drop_all()
