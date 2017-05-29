import os
import zipfile
from werkzeug.utils import secure_filename
from server import flashprint


def request_files_empty(request_result, filetype):
    if request_result.filename == '' or request_result.filename is None:
        flashprint('Empty in submission: ' + filetype)
        return True
    return False


def request_files_missing(request_files, filetype):
    if filetype not in request_files:
        flashprint('Missing from submission: ' + filetype)
        return True
    return False


def request_file_exists(request_files, file_tag):
    return not (
    request_files_missing(request_files, file_tag) or request_files_empty(request_files[file_tag], file_tag))


def file_extension_okay(filename, required_file_extension):
    file_extension = filename.rsplit('.', 1)[1].lower()
    if '.' in filename and file_extension == required_file_extension:
        return True
    flashprint('Expected file extension: ' + required_file_extension + ' but got: ' + file_extension)
    return False


def save_and_extract_files(app, js_file, zip_file):
    # TODO Gonna want to use custom file_names. Append user_id and put it in a folder for the user/task.
    js_filename = secure_filename(js_file.filename)
    zip_filename = secure_filename(zip_file.filename)
    flashprint('Uploading...')
    js_file.save(os.path.join(app.config['JS_UPLOAD_FOLDER'], js_filename))
    zip_file.save(os.path.join(app.config['ZIP_UPLOAD_FOLDER'], zip_filename))
    flashprint("successfully uploaded " + js_filename + " and " + zip_filename)
    extract(app, zip_filename)


def extract(app, filename):
    with zipfile.ZipFile(app.config['ZIP_UPLOAD_FOLDER'] + filename, "r") as zip_ref:
        zip_ref.extractall(app.config['ZIP_UPLOAD_FOLDER'] + "extracted_" + filename + "/")
