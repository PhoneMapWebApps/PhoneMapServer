# sample config -> copy paste to a new config.py which isn't under VCS (has been added to .gitignore already)
class Development(object):
    DEBUG = True
    SECRET_KEY = 'secret!'
    # Change below otherwise it will obviously not work.
    JS_UPLOAD_FOLDER = '/path/to/dir/PhoneMapServer/data/js/'
    ZIP_UPLOAD_FOLDER = '/path/to/dir/PhoneMapServer/data/zip/'

    # SQLALCHEMY_DATABASE_URI = postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]
    SQLALCHEMY_DATABASE_URI = 'sqltype://username:password@location:port/databasename'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
