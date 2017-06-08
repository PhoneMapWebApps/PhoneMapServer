from app.main.files import file_extension_okay, request_files_missing
from test.test import BaseTestCase


class TestFiles(BaseTestCase):
    def test_extensions(self):
        self.assertTrue(file_extension_okay('whatever.js', 'js'))
        self.assertFalse(file_extension_okay('whatever.png', 'js'))
        self.assertTrue(file_extension_okay('ayy/lmao.zip', 'zip'))
        self.assertFalse(file_extension_okay('ayy/lmao.tar.gz', 'zip'))

    def test_filed_missing(self):
        self.assertFalse(request_files_missing({'foo': 'bar'}, 'foo'))
        self.assertTrue(request_files_missing({'foobar': 'bar'}, 'foo'))
