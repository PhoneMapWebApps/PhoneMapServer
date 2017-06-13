from datetime import datetime
from time import strftime

from sqlalchemy.exc import IntegrityError

from app import app, db
from app.main.models import Tasks, SubTasks, AndroidIDs, Users
from test.test import BaseTestCase

ROOT_ID = 1


class TestTasks(BaseTestCase):

    def test_single_task(self):
        with app.app_context():
            task = Tasks(ROOT_ID, datetime.utcnow())
            db.session.add(task)
            db.session.commit()

            tasks = Tasks.query.all()
            self.assertTrue(task in tasks)
            self.assertEqual(len(tasks), 1)

    def test_double_task(self):
        with app.app_context():
            task = Tasks(ROOT_ID, datetime.utcnow())
            task2 = Tasks(ROOT_ID, datetime.utcnow())
            db.session.add(task)
            db.session.add(task2)
            db.session.commit()

            tasks = Tasks.query.all()
            self.assertTrue(task in tasks and task2 in tasks)
            self.assertEqual(len(tasks), 2)

    def test_to_json(self):
        with app.app_context():
            time = datetime.utcnow()
            task = Tasks(ROOT_ID, time, "Task", "Desc")
            db.session.add(task)
            db.session.commit()

            def_json = {"task_id": 1,
                "task_name": "Task",
                "time_submitted": strftime(task.TIME_FORMAT, time.timetuple()),
                "time_started": "",
                "time_completed": "",
                "in_progress": False,
                "is_complete": False,
                "task_desc": "Desc",
                "owner_fullname": "Admin",
                "owner_org": "No Org"}

            self.assertEqual(task.to_json(), def_json)

    def tearDown(self):
        with app.app_context():
            db.drop_all()


class TestSubTasks(BaseTestCase):
    def test_foreign_key(self):
        with app.app_context():
            with self.assertRaises(IntegrityError):
                # 0 is never valid task_id, given SQL starts to increment at 1
                subtask = SubTasks(0, "somefile.js", datetime.utcnow())
                db.session.add(subtask)
                db.session.commit()

    def test_single_subtask(self):
        with app.app_context():
            task = Tasks(ROOT_ID, datetime.utcnow())
            db.session.add(task)
            db.session.flush()
            subtask = SubTasks(task.task_id, "somefile.js", datetime.utcnow())
            db.session.add(subtask)
            db.session.commit()

            subtasks = SubTasks.query.all()
            self.assertEqual(len(subtasks), 1)
            self.assertTrue(subtask in subtasks)

    def test_double_subtask(self):
        with app.app_context():
            task = Tasks(ROOT_ID, datetime.utcnow())
            db.session.add(task)
            db.session.flush()
            subtask = SubTasks(task.task_id, "randomfile1.js", datetime.utcnow())
            subtask2 = SubTasks(task.task_id, "randomfile2.js", datetime.utcnow())
            db.session.add(subtask)
            db.session.add(subtask2)
            db.session.commit()

            subtasks = SubTasks.query.all()
            self.assertEqual(len(subtasks), 2)
            self.assertTrue(subtask in subtasks and subtask2 in subtasks)

    def tearDown(self):
        with app.app_context():
            db.drop_all()


class TestAndroidIDs(BaseTestCase):
    def test_single_id(self):
        with app.app_context():
            id1 = AndroidIDs("Dr", "Who")
            db.session.add(id1)
            db.session.commit()

            ids = AndroidIDs.query.all()
            self.assertEqual(len(ids), 1)
            self.assertTrue(id1 in ids)

    def test_double_id(self):
        with app.app_context():
            id1 = AndroidIDs("James", "Bond")
            id2 = AndroidIDs("Rick", "Morty")
            db.session.add(id1)
            db.session.add(id2)
            db.session.commit()

            ids = AndroidIDs.query.all()
            self.assertEqual(len(ids), 2)
            self.assertTrue(id1 in ids and id2 in ids)

    def tearDown(self):
        with app.app_context():
            db.drop_all()


class TestUsers(BaseTestCase):
    def test_single_id(self):
        with app.app_context():
            user1 = Users("My", "password", "SomeGuy")
            db.session.add(user1)
            db.session.commit()

            users = Users.query.all()
            self.assertTrue(user1 in users)
            self.assertEqual(len(users), 2)  # +1 because of root user

    def test_double_id(self):
        with app.app_context():
            user1 = Users("123", "456", "Tester01")
            user2 = Users("789", "101112", "Tester02")
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()

            users = Users.query.all()
            self.assertTrue(user1 in users and user2 in users)
            self.assertEqual(len(users), 3)  # +1 because of root user

    def test_active(self):
        with app.app_context():
            user = Users("My", "password", "Big Secret")
            db.session.add(user)
            db.session.commit()

            self.assertTrue(user.is_active)

    def test_authenticated(self):
        with app.app_context():
            user = Users("My", "password", "Small Secret")
            db.session.add(user)
            db.session.commit()

            self.assertTrue(user.is_authenticated)

    def test_anonymous(self):
        with app.app_context():
            user = Users("My", "password", "Meh Secret")
            db.session.add(user)
            db.session.commit()

            self.assertFalse(user.is_anonymous)

    def test_get_id(self):
        with app.app_context():
            user = Users("My", "password", "Bleh Secret")
            db.session.add(user)
            db.session.commit()

            self.assertEqual(user.get_id(), user.user_id)

    def test_check_password(self):
        with app.app_context():
            user = Users("My", "password", "Alpha secret")
            db.session.add(user)
            db.session.commit()

            user.check_password("password")

    def tearDown(self):
        with app.app_context():
            db.drop_all()
