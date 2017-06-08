import unittest
from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app import create_app, app, db
from app.main.models import Tasks, SubTasks, AndroidIDs


class TestTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(False, True)

    def test_single_task(self):
        with app.app_context():
            task = Tasks(0, datetime.utcnow())
            db.session.add(task)
            db.session.commit()

            tasks = Tasks.query.all()
            self.assertTrue(task in tasks)
            print("Number of tasks should be 1, is " + str(len(tasks)))

    def test_double_task(self):
        with app.app_context():
            task = Tasks(0, datetime.utcnow())
            task2 = Tasks(0, datetime.utcnow())
            db.session.add(task)
            db.session.add(task2)
            db.session.commit()

            tasks = Tasks.query.all()
            self.assertTrue(task in tasks and task2 in tasks)
            print("Number of tasks should be 2, is " + str(len(tasks)))

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()


class TestSubTasks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(False, True)

    def test_foreign_key(self):
        with app.app_context():
            with self.assertRaises(IntegrityError):
                # 0 is never valid task_id, given SQL starts to increment at 1
                subtask = SubTasks(0, "somefile.js", datetime.utcnow())
                db.session.add(subtask)
                db.session.commit()

    def test_single_subtask(self):
        with app.app_context():
            task = Tasks(0, datetime.utcnow())
            db.session.add(task)
            db.session.flush()
            subtask = SubTasks(task.task_id, "somefile.js", datetime.utcnow())
            db.session.add(subtask)
            db.session.commit()

            subtasks = SubTasks.query.all()
            self.assertTrue(subtask in subtasks)
            print("Number of subtasks should be 1, is " + str(len(subtasks)))

    def test_double_subtask(self):
        with app.app_context():
            task = Tasks(0, datetime.utcnow())
            db.session.add(task)
            db.session.flush()
            subtask = SubTasks(task.task_id, "randomfile1.js", datetime.utcnow())
            subtask2 = SubTasks(task.task_id, "randomfile2.js", datetime.utcnow())
            db.session.add(subtask)
            db.session.add(subtask2)
            db.session.commit()

            subtasks = SubTasks.query.all()
            self.assertTrue(subtask in subtasks and subtask2 in subtasks)
            print("Number of subtasks should be 2, is " + str(len(subtasks)))

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()


class TestAndroidIDs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(False, True)

    def test_single_id(self):
        with app.app_context():
            id1 = AndroidIDs("Dr", "Who")
            db.session.add(id1)
            db.session.commit()

            ids = AndroidIDs.query.all()
            self.assertTrue(id1 in ids)
            print("Number of tasks should be 1, is " + str(len(ids)))

    def test_double_id(self):
        with app.app_context():
            id1 = AndroidIDs("James", "Bond")
            id2 = AndroidIDs("Rick", "Morty")
            db.session.add(id1)
            db.session.add(id2)
            db.session.commit()

            ids = AndroidIDs.query.all()
            self.assertTrue(id1 in ids and id2 in ids)
            print("Number of tasks should be 2, is " + str(len(ids)))

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
