from unittest import TestCase

from app.main.files import file_extension_okay, request_files_missing


# Doesnt need to be a BaseTestCase because not app related
class TestFiles(TestCase):
    def test_extensions(self):
        self.assertTrue(file_extension_okay('whatever.js', 'js'))
        self.assertFalse(file_extension_okay('whatever.png', 'js'))
        self.assertTrue(file_extension_okay('ayy/lmao.zip', 'zip'))
        self.assertFalse(file_extension_okay('ayy/lmao.tar.gz', 'zip'))

    def test_files_missing(self):
        self.assertFalse(request_files_missing({'foo': 'bar'}, 'foo'))
        self.assertTrue(request_files_missing({'foobar': 'bar'}, 'foo'))

    # def test_files_empty(self):
    #     # TODO: this
    #     pass
    #
    # def test_file_exists(self):
    #     # TODO: as prev
    #     pass
    #
    # def test_save_and_extract(self):
    #     pass
    #
    # def test_save_and_extract_js(self):
    #     pass
    #
    # def test_save_and_extract_zip(self):
    #     pass
    #
    # def test_extract(self):
    #     pass
    #
    # def test_remove_task_files(self):
    #     pass
