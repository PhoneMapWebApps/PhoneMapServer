# sample config -> copy paste to a new config.py which isn't under VCS (has been added to .gitignore already)
class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'secret!'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JS_FOLDER = 'data/js/'
    ZIP_FOLDER = 'data/zip/'


class Production(Config):
    DEBUG = False


class Development(Config):
    # SECRET_KEY = "should set this"
    DEBUG = True
    # SQLALCHEMY_DATABASE_URI = postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]
    SQLALCHEMY_DATABASE_URI = 'sqltype://username:password@location:port/databasename'


class Testing(Config):
    TESTING = True
    DEBUG = False
    JS_FOLDER = "test/upload/data/js/"
    ZIP_FOLDER = "test/upload/data/zip/"
    # setup to work with circleCI
    SQLALCHEMY_DATABASE_URI = 'postgresql://ubuntu@localhost:5432/circle_test'
