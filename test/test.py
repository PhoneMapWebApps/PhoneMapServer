import os

import shutil
from flask_testing import TestCase
from nose.tools import nottest

from app import app, create_app


class BaseTestCase(TestCase):
    def create_app(self):
        create_app(False, True)
        return app


@nottest
def delete_data(folder):
    for root, dirs, files in os.walk(folder):
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']

        for f in files:
            os.unlink(os.path.join(root, f))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))
