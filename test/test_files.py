import unittest

from app.main.files import file_extension_okay, request_file_exists, request_files_missing


class TestFiles(unittest.TestCase):
    def test_extensions(self):
        assert file_extension_okay('whatever.js', 'js')
        assert not file_extension_okay('whatever.png', 'js')
        assert file_extension_okay('ayy/lmao.zip', 'zip')
        assert not file_extension_okay('ayy/lmao.tar.gz', 'zip')

    def test_filed_missing(self):
        assert not request_files_missing({'foo': 'bar'}, 'foo')
        assert request_files_missing({'foobar': 'bar'}, 'foo')
