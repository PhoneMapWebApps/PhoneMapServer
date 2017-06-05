import unittest
from datetime import datetime

from app import create_app, app, db
from app.main import sql
from app.main.models import AndroidIDs, SubTasks


class TestSQLdb(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(False, True)

    @classmethod
    def millis_within_range(cls, t1, t2, max_separation):
        return (0.001 * abs(t1 - t2).microseconds) < max_separation

    def test_add_to_db(self):
        with app.app_context():
            old_nTasks = SubTasks.query.count()
            with open('test/resources/test.js', 'rb') as js_file:
                with open('test/resources/test.zip', 'rb') as zip_file:
                    submission_time = datetime.utcnow()
                    val = sql.add_to_db(js_file, zip_file)

            self.assertIsNotNone(val)
            new_nTasks = SubTasks.query.count()
            self.assertEqual(new_nTasks, old_nTasks + 3) # 3 subtasks added from test.zip

            subtask = SubTasks.query.first()
            self.assertTrue(self.millis_within_range(subtask.time_submitted, submission_time, 20.0))

    def test_get_phone_in_db(self):
        with app.app_context():
            db.session.add(AndroidIDs("Sherlock", "Holmes"))
            db.session.commit()

            phone = sql.get_phone("Sherlock", "Holmes")

            self.assertEqual(phone.android_id, "Sherlock")
            self.assertEqual(phone.session_id, "Holmes")
            self.assertTrue(phone.is_connected)
            self.assertFalse(phone.is_processing)

    def test_phone_created_if_not_in_db(self):
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


class TestGetCodeFail(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(False, True)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()

    def test_get_next_fail(self):
        with app.app_context():
            data_file, task_id = sql.get_next_subtask("TestPhone", "TestSessionID")

        self.assertIsNone(data_file)
        self.assertIsNone(task_id)

    def test_get_by_task_id_fail(self):
        with app.app_context():
            # task 0 is never present
            data_file, task_id = sql.get_subtask_by_task_id("TestPhone", "TestSessionID", 1)

        self.assertIsNone(data_file)
        self.assertIsNone(task_id)

    def test_get_latest_fail(self):
        with app.app_context():
            data_file, task_id = sql.get_latest_subtask("TestPhone", "TestSessionID")

        self.assertIsNone(data_file)
        self.assertIsNone(task_id)


class TestGetCode(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(False, True)
        with app.app_context():
            with open('test/resources/test.js', 'rb') as js_file:
                with open('test/resources/test.zip', 'rb') as zip_file:
                    # add twice for 2 tasks (1, 2)
                    # test.zip has 3 files = 3 subtasks -> 6 subtasks total (numbered 1-6)
                    sql.add_to_db(js_file, zip_file)
                    sql.add_to_db(js_file, zip_file)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()

    def test_get_next(self):
        with app.app_context():
            data_file, task_id = sql.get_next_subtask("TestPhone", "TestSessionID")

        self.assertIsNotNone(data_file)
        self.assertIsNotNone(task_id)
        self.assertEqual(task_id, 1)

    def test_get_by_task_id(self):
        with app.app_context():
            data_file, task_id = sql.get_subtask_by_task_id("TestPhone", "TestSessionID", 1)
            data_file_2, task_id_2 = sql.get_subtask_by_task_id("TestPhone", "TestSessionID", 2)

        self.assertIsNotNone(data_file)
        self.assertIsNotNone(data_file_2)
        self.assertIsNotNone(task_id)
        self.assertIsNotNone(task_id_2)
        self.assertEqual(task_id, 1)
        self.assertEqual(task_id_2, 2)

    def test_get_latest(self):
        with app.app_context():
            data_file, task_id = sql.get_latest_subtask("TestPhone", "TestSessionID")
            data_file_2, task_id_2 = sql.get_subtask_by_task_id("TestPhone", "TestSessionID", 1)

        self.assertIsNotNone(data_file)
        self.assertIsNotNone(data_file_2)
        self.assertIsNotNone(task_id)
        self.assertIsNotNone(task_id_2)
        self.assertLess(task_id_2, task_id)
