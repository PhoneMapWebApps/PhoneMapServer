import unittest
from datetime import datetime

from app import create_app, app, db
from app.main.models import Tasks


class TestTasks(unittest.TestCase):
    def setUp(self):
        create_app(True, True)

    def test_single_task(self):
        with app.app_context():
            task = Tasks(datetime.utcnow())
            db.session.add(task)
            db.session.commit()

            tasks = Tasks.query.all()
            assert task in tasks
            print("Number of tasks should be 1, is " + str(len(tasks)))

    def test_double_task(self):
        with app.app_context():
            task = Tasks(datetime.utcnow())
            task2 = Tasks(datetime.utcnow())
            db.session.add(task)
            db.session.add(task2)
            db.session.commit()

            tasks = Tasks.query.all()
            assert task in tasks and task2 in tasks
            print("Number of tasks should be 2, is " + str(len(tasks)))

    def tearDown(self):
        with app.app_context():
            db.drop_all()
