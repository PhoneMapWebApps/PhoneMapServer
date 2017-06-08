import os
import shutil
import unittest

from nose.tools import nottest

from app import create_app, app, db


@nottest
def upload_data():
    with open('test/resources/test.js', 'rb') as js_file:
        with open('test/resources/test.zip', 'rb') as zip_file:
            with app.test_client() as client:
                return client.post(
                    '/tasks',
                    data=dict(
                        JS_FILE=js_file,
                        ZIP_FILE=zip_file,
                        TASK_NAME="Some Test Task",
                        TASK_DESC="Interesting description"
                    ),
                    content_type='multipart/form-data'
                )


@nottest
def delete_data():
    os.remove(app.config['JS_FOLDER'] + '1.js')
    os.remove(app.config['ZIP_FOLDER'] + '1.zip')
    shutil.rmtree(app.config['ZIP_FOLDER'] + '1')


# TODO: test Login

# class TestUpload(unittest.TestCase):
#     @classmethod
#     def setUpClass(cls):
#         create_app(debug=False, testing=True)
#
#     def test_upload(self):
#         resp = upload_data()
#
#         self.assertEqual(resp.status_code, 302)
#         self.assertTrue(os.path.isfile(app.config['JS_FOLDER'] + '1.js'))
#         self.assertTrue(os.path.isfile(app.config['ZIP_FOLDER'] + '1.zip'))
#         self.assertTrue(os.path.isdir(app.config['ZIP_FOLDER'] + '1'))
#
#     # def test_successful_start(self):
#     #     with app.app_context():
#     #         with app.test_client() as client:
#     #             resp = client.get('/')
#     #             self.assertEqual(resp.status_code, 200)
#
#     def tearDown(self):
#         delete_data()
#
#     @classmethod
#     def tearDownClass(cls):
#         with app.app_context():
#             db.drop_all()


class TestServer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(debug=False, testing=True)

    def test_successful_start(self):
        with app.app_context():
            with app.test_client() as client:
                resp = client.get('/')
                self.assertEqual(resp.status_code, 200)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
