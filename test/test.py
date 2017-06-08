from flask_testing import TestCase

from app import app, create_app


class BaseTestCase(TestCase):
    def create_app(self):
        create_app(False, True)
        return app
