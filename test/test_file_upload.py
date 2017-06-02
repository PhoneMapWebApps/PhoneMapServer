import os.path
import requests
import shutil
import sys
import threading
import time
import unittest

from app.main.files import file_extension_okay
from test.local_test_server import *

sys.path.insert(0, '..')

WAIT_FOR_SERVER = 3.0


class TestFileUpload(unittest.TestCase):
    test_server = None

    def test_valid_extensions(self):
        self.assertTrue(file_extension_okay('whatever.js', 'js', False))
        self.assertFalse(file_extension_okay('whatever.png', 'js', False))
        self.assertTrue(file_extension_okay('ayy/lmao.zip', 'zip', False))
        self.assertFalse(file_extension_okay('ayy/lmao.tar.gz', 'zip', False))

    def test_file_upload(self):
        js_file = open('test/resources/test.js', 'rb')
        zip_file = open('test/resources/test.zip', 'rb')
        response = requests.post('http://0.0.0.0:5000/tasks', files=dict(JS_FILE=js_file, ZIP_FILE=zip_file))
        # new database so task will be 1
        try:
            self.assertEqual(response.status_code, 200)
            self.assertTrue(os.path.isfile('test/upload/data/js/1.js'))
            self.assertTrue(os.path.isfile('test/upload/data/zip/1.zip'))
            self.assertTrue(os.path.isdir('test/upload/data/zip/1'))
        finally:
            js_file.close()
            zip_file.close()
            os.remove('test/upload/data/js/1.js')
            os.remove('test/upload/data/zip/1.zip')
            shutil.rmtree('test/upload/data/zip/1')

    @classmethod
    def setUpClass(cls):
        test_server = threading.Thread(target=start_local_test_server)
        test_server.setDaemon(True)
        test_server.start()
        time.sleep(WAIT_FOR_SERVER)
        cls.test_server = test_server

    @classmethod
    def tearDownClass(cls):
        cls.test_server.join(-1)
        restore_previous_config()
        os.system('pkill -f flask')


if __name__ == '__main__':
    unittest.main()
