# sample config -> copy paste to a new config.py which isn't under VCS (has been added to .gitignore already)
import os

class Development(object):
    DEBUG = True
    SECRET_KEY = 'secret!'
    # Change below otherwise it will obviously not work.
    JS_UPLOAD_FOLDER = '/path/to/dir/PhoneMapServer/data/js/'
    ZIP_UPLOAD_FOLDER = '/path/to/dir/PhoneMapServer/data/zip/'

    # SQLALCHEMY_DATABASE_URI = postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]
    SQLALCHEMY_DATABASE_URI = 'sqltype://username:password@location:port/databasename'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'secret!'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JS_UPLOAD_FOLDER = 'data/js/'
    ZIP_UPLOAD_FOLDER = 'data/zip/'


class ProductionConfig(Config):
    DEBUG = False


class DevelopmentConfig(Config):
    # SECRET_KEY = "should set this"
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]
    SQLALCHEMY_DATABASE_URI = 'sqltype://username:password@location:port/databasename'


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    JS_UPLOAD_FOLDER = "test/upload/data/js/"
    ZIP_UPLOAD_FOLDER = "test/upload/data/zip/"
    # setup to work with circleCI
    SQLALCHEMY_DATABASE_URI = 'postgresql://ubuntu/circle_test'
