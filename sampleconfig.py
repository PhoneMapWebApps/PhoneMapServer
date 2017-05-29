# sample config -> copy paste to a new config.py which isn't under VCS (has been added to .gitignore already)
class Development(object):
    DEBUG = True
    SECRET_KEY = 'secret!'
    # Change below otherwise it will obviously not work.
    JS_UPLOAD_FOLDER = '/path/to/dir/PhoneMapServer/data/js/'
    ZIP_UPLOAD_FOLDER = '/path/to/dir/PhoneMapServer/data/zip/'

    PSQL_USER = 'I_am_a_user'
    PSQL_PASSWORD = 'this_is_a_password'
    PSQL_DB = 'this_is_a_DB'
    PSQL_SERVER = 'db.this.is.where.com'
    PSQL_PORT = 6666
