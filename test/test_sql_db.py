import unittest
from datetime import datetime

from app import create_app, app, db
from app.main import sql
from app.main.models import AndroidIDs, SubTasks
from app.main.sql import add_to_db


class TestSQLdb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(False, True)

    @classmethod
    def millis_within_range(cls, t1, t2, max_separation):
        return (0.001 * abs(t1 - t2).microseconds) < max_separation

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
            self.assertTrue(self.millis_within_range(subtask.time_submitted, submission_time, 20.0))

    def test_get_phone_in_db(self):
        with app.app_context():
            id1 = AndroidIDs("Sherlock", "Holmes")
            db.session.add(id1)
            db.session.commit()

            phone = sql.get_phone("Sherlock", "Holmes")

            self.assertEqual(phone.android_id, "Sherlock")
            self.assertEqual(phone.session_id, "Holmes")
            self.assertTrue(phone.is_connected)
            self.assertFalse(phone.is_processing)

    def test_get_phone_not_in_db(self):
        with app.app_context():
            phone = sql.get_phone("Dr John", "Watson")

            self.assertEqual(phone.android_id, "Dr John")
            self.assertEqual(phone.session_id, "Watson")
            self.assertTrue(phone.is_connected)
            self.assertFalse(phone.is_processing)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
