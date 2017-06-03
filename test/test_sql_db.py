import unittest
from datetime import datetime

from app import create_app, app, db
from app.main import sql
from app.main.models import AndroidIDs, SubTasks
from app.main.sql import add_to_db


class TestSQLdb(unittest.TestCase):
    def setUp(self):
        create_app(False, True)

    @classmethod
    def millis_within_range(self, t1, t2, max_seperation):
        return (0.001 * abs(t1 - t2).microseconds) < max_seperation

    def test_add_to_db(self):
        with app.app_context():
            js_file = open('test/resources/test.js', 'rb')
            zip_file = open('test/resources/test.zip', 'rb')

            old_nTasks = SubTasks.query.count()
            submission_time = datetime.utcnow()
            add_to_db(js_file, zip_file)
            new_nTasks = SubTasks.query.count()

            self.assertEqual(new_nTasks, old_nTasks + 1)

            subtask = SubTasks.query.one()
            assert self.millis_within_range(subtask.time_submitted, submission_time, 20.0)

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
