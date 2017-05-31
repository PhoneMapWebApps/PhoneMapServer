import unittest
import requests
import os.path
import shutil
import sys

sys.path.insert(0,'..')
from misc.files import *
from test.local_test_server import *


class TestFileUpload(unittest.TestCase):
    def test_valid_extensions(self):
        self.assertTrue(file_extension_okay('whatever.js', 'js'))
        self.assertFalse(file_extension_okay('whatever.png', 'js'))
        self.assertTrue(file_extension_okay('ayy/lmao.zip', 'zip'))
        self.assertFalse(file_extension_okay('ayy/lmao.tar.gz', 'zip'))

    def test_file_upload(self):
        test_server = start_local_test_server()

        # Requires server to be started
        js_file = open('test/resources/test.js', 'rb')
        zip_file = open('test/resources/test.zip', 'rb')
        response = requests.post('http://0.0.0.0:5000/', files=dict(JS_FILE=js_file, ZIP_FILE=zip_file))
        try:
            self.assertEqual(response.status_code, 200)
            self.assertTrue(os.path.isfile('test/upload/data/js/test.js'))
            self.assertTrue(os.path.isdir('test/upload/data/zip/extracted_test.zip'))
        finally:
            # Close files, delete byproducts
            js_file.close()
            zip_file.close()
            os.remove('test/upload/data/js/test.js')
            os.remove('test/upload/data/zip/test.zip')
            shutil.rmtree('test/upload/data/zip/extracted_test.zip')

        stop_local_test_server(test_server)

if __name__ == '__main__':
    test_server = start_local_test_server()

    unittest.main()

    stop_local_test_server(test_server)
