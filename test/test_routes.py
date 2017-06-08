import os

import shutil

from flask import url_for
from flask_login import current_user

from app import app, db
from app.main.models import User
from test.test import BaseTestCase


class TestUpload(BaseTestCase):

    def login(self):
        user = User("Test", "pw")
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
                        resp = self.client.post(
                            '/tasks',
                            data=dict(
                                JS_FILE=js_file,
                                ZIP_FILE=zip_file,
                                TASK_NAME="Some Test Task",
                                TASK_DESC="Interesting description"
                            ),
                            content_type='multipart/form-data'
                        )

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(os.path.isfile(app.config['JS_FOLDER'] + '1.js'))
        self.assertTrue(os.path.isfile(app.config['ZIP_FOLDER'] + '1.zip'))
        self.assertTrue(os.path.isdir(app.config['ZIP_FOLDER'] + '1'))

    @staticmethod
    def tearDown():
        os.remove(app.config['JS_FOLDER'] + '1.js')
        os.remove(app.config['ZIP_FOLDER'] + '1.zip')
        shutil.rmtree(app.config['ZIP_FOLDER'] + '1')
        with app.app_context():
            db.drop_all()


class TestLogin(BaseTestCase):
    def test_start(self):
        with app.app_context():
            resp = self.client.get("/")
            self.assert200(resp)

    def test_login_no_auth(self):
        resp = self.client.get("/tasks")
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(url_for('main.login') in resp.location)

    def test_login_auth(self):
        with app.app_context():
            user = User("Test", "pw")
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

    def tearDown(self):
        with app.app_context():
            db.drop_all()
