import unittest
import requests
import os.path
from server import file_extension_okay
import shutil

class TestFileUpload(unittest.TestCase):
    def allows_valid_extensions(self):
        self.assertTrue(file_extension_okay('whatever.js', 'js'))
        self.assertFalse(file_extension_okay('whatever.png', 'js'))
        self.assertTrue(file_extension_okay('ayy/lmao.zip', 'zip'))
        self.assertFalse(file_extension_okay('ayy/lmao.tar.gz', 'zip'))

    def can_upload_file(self):
        # Requires server to be started
        js_file = open('resources/test.js', 'rb')
        zip_file = open('resources/test.zip', 'rb')
        response = requests.post('http://0.0.0.0:5000/', files=dict(JS_FILE=js_file, ZIP_FILE=zip_file))
        try:
            self.assertEqual(response.status_code, 200)
            self.assertTrue(os.path.isfile('../data/js/test.js'))
            self.assertTrue(os.path.isdir('../data/zip/extracted_test.zip'))
        finally:
            # Close files, delete byproducts
            js_file.close()
            zip_file.close()
            os.remove('../data/js/test.js')
            os.remove('../data/zip/test.zip')
            shutil.rmtree('../data/zip/extracted_test.zip')




if __name__ == '__main__':
    unittest.main()