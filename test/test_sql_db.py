import unittest

from app import create_app, app, db
from app.main import sql
from app.main.models import AndroidIDs


class TestSQLdb(unittest.TestCase):
    def setUp(self):
        create_app(False, True)

    def test_get_phone_in_db(self):
        with app.app_context():
            id1 = AndroidIDs("Sherlock", "Holmes")
            db.session.add(id1)
            db.session.commit()

            phone = sql.get_phone("Sherlock", "Holmes")

            assert phone.android_id == "Sherlock"
            assert phone.session_id == "Holmes"
            assert phone.is_connected
            assert not phone.is_processing

    def test_get_phone_NOT_in_db(self):
        with app.app_context():
            phone = sql.get_phone("Sherlock", "Holmes")

            assert phone.android_id == "Sherlock"
            assert phone.session_id == "Holmes"
            assert phone.is_connected
            assert not phone.is_processing

    def tearDown(self):
        with app.app_context():
            db.drop_all()
