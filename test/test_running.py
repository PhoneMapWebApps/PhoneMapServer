import unittest

from app import create_app, app, db


class TestRunning(unittest.TestCase):
    def setUp(self):
        create_app(debug=False, testing=True)

    def test_successful_start(self):
        with app.app_context():
            with app.test_client() as client:
                resp = client.get('/')
                print(resp.status_code)

    def tearDown(self):
        with app.app_context():
            db.drop_all()
