import os

from flask import url_for
from flask_login import current_user

from app import app, db
from app.main.models import Users
from test.test import BaseTestCase, delete_data


class TestTasks(BaseTestCase):
    def login(self):
        user = Users("Test", "pw", "So many test users")
        db.session.add(user)
        db.session.commit()
        resp = self.client.post(url_for('main.login'),
                                data={'username': "Test", 'password': "pw"})

    def test_upload(self):
        with app.app_context():
            with self.client:
                self.login()
                print(current_user.username)
                with open('test/resources/test.js', 'rb') as js_file:
                    with open('test/resources/test.zip', 'rb') as zip_file:
                        with open('test/resources/martin.jpg', 'rb') as pic:
                            resp = self.client.post(
                                '/tasks',
                                data=dict(
                                    TASK_PIC=pic,
                                    JS_FILE=js_file,
                                    ZIP_FILE=zip_file,
                                    TASK_NAME="Some Test Task",
                                    TASK_DESC="Interesting description"
                                ),
                                content_type='multipart/form-data'
                            )

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(os.path.isfile(os.path.join(app.config['JS_FOLDER'], '1.js')))
        self.assertTrue(os.path.isfile(os.path.join(app.config['ZIP_FOLDER'], '1.zip')))
        self.assertTrue(os.path.isdir(os.path.join(app.config['ZIP_FOLDER'], '1')))
        delete_data(app.config["JS_FOLDER"])
        delete_data(app.config["ZIP_FOLDER"])
        delete_data(app.config["RES_FOLDER"])

    def test_tasks(self):
        with app.app_context():
            with self.client:
                self.login()
                resp = self.client.get("/")
        self.assert200(resp)

    @staticmethod
    def tearDown(**kwargs):
        with app.app_context():
            db.drop_all()


class TestIndex(BaseTestCase):
    @staticmethod
    def tearDown(**kwargs):
        with app.app_context():
            db.drop_all()

    def test_index(self):
        with app.app_context():
            with self.client:
                resp = self.client.get("/")

        self.assertEqual(resp.status_code, 200)  # should show /login directly


class TestLogin(BaseTestCase):
    def test_start(self):
        with app.app_context():
            resp = self.client.get("/")
            self.assertEqual(resp.status_code, 200)  # should show /login directly

    def test_login_no_auth(self):
        resp = self.client.get("/monitor")
        self.assertEqual(resp.status_code, 200)  # should show /login directly

    def test_login_auth(self):
        with app.app_context():
            user = Users("Test", "pw", "Testus maximus")
            db.session.add(user)
            db.session.commit()

            with self.client:
                resp = self.client.post(url_for('main.login'),
                                        data={'username': "Test", 'password': "pw"})
                print(resp.location)
                self.assertTrue(current_user.username == 'Test')
                self.assertFalse(current_user.is_anonymous)

    def test_bad_login(self):
        with app.app_context():
            with self.client:
                resp = self.client.post(url_for('main.login'),
                                        data={'username': "Bad", 'password': "User"})
                print(resp.location)
                self.assertTrue(current_user.is_anonymous)

    @staticmethod
    def tearDown(**kwargs):
        with app.app_context():
            db.drop_all()

# class TestCreate(BaseTestCase):
#     def tearDown(self):
#         with app.app_context():
#             db.drop_all()
#
#     def test_create(self):
#         pass
#
#     def test_already_exists_create(self):
#         pass
#
#
# class TestLogout(BaseTestCase):
#     def tearDown(self):
#         with app.app_context():
#             db.drop_all()
#
#     def test_logout(self):
#         pass
#
#
# class TestTaskList(BaseTestCase):
#     def tearDown(self):
#         with app.app_context():
#             db.drop_all()
#
#     def test_task_list(self):
#         pass
#
#
# class TestChangeFiles(BaseTestCase):
#     def tearDown(self):
#         with app.app_context():
#             db.drop_all()
#
#     def test_change_zip(self):
#         pass
#
#     def test_change_js(self):
#         pass
#
#     def test_change_bot(self):
#         pass
#
#     def test_change_other_user_task(self):
#         pass
#
#
# class TestRemoveTask(BaseTestCase):
#     def tearDown(self):
#         with app.app_context():
#             db.drop_all()
#
#     def test_remove_task(self):
#         pass
#
#     def test_remove_other_user_task(self):
#         pass
