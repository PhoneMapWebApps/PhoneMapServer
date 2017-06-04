import os
import shutil
import unittest

from app import create_app, app, db


class TestRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        create_app(debug=False, testing=True)

    def test_upload(self):
        with app.app_context():
            js_file = open('test/resources/test.js', 'rb')
            zip_file = open('test/resources/test.zip', 'rb')

            with app.test_client() as client:
                resp = client.post(
                    '/tasks',
                    data=dict(
                        JS_FILE=js_file,
                        ZIP_FILE=zip_file
                    ),
                    content_type='multipart/form-data'

                )
        assert resp.status_code == 302
        assert os.path.isfile('test/upload/data/js/1.js')
        assert os.path.isfile('test/upload/data/zip/1.zip')
        assert os.path.isdir('test/upload/data/zip/1')
        try:
            os.remove('test/upload/data/js/1.js')
            os.remove('test/upload/data/zip/1.zip')
            shutil.rmtree('test/upload/data/zip/1')
        except FileNotFoundError:
            print("No files found")
        finally:
            js_file.close()
            zip_file.close()

    def test_successful_start(self):
        with app.app_context():
            with app.test_client() as client:
                resp = client.get('/')
                print(resp.status_code)

    @classmethod
    def tearDownClass(cls):
        with app.app_context():
            db.drop_all()
