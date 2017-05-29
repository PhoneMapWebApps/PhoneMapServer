# sample config -> copy paste to a new config.py which isn't under VCS (has been added to .gitignore already)
class Development(object):
    DEBUG = True
    SECRET_KEY = 'secret!'
    # Change below otherwise it will obviously not work.
    JS_UPLOAD_FOLDER = '/path/to/dir/PhoneMapServer/data/js/'
    ZIP_UPLOAD_FOLDER = '/path/to/dir/PhoneMapServer/data/zip/'
    PostGreSQLUser = 'I_am_a_user'
    PostGreSQLPassword = 'this_is_a_password'
    PostGreSQLDB = 'this_is_a_DB'
    PostGreSQLServer = 'db.this.is.where.com'
    PostGreSQLPort = 6666
