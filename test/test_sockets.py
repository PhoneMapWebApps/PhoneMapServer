import unittest

from app import create_app, app, db, socketio


class TestSockets(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(False, True)

    def test_socket_idk(self):
        # TODO: this
        pass

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
