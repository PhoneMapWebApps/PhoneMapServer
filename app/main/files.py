import os
import zipfile

from flask import current_app as app

from app.main.logger import log


def request_files_empty(request_result, filetype):
    if request_result.filename == '' or request_result.filename is None:
        log('Empty in submission: ' + filetype)
        return True
    return False


def request_files_missing(request_files, filetype):
    if filetype not in request_files:
        log('Missing from submission: ' + filetype)
        return True
    return False


def request_file_exists(request_files, file_tag):
    return not (
        request_files_missing(request_files, file_tag) or request_files_empty(request_files[file_tag], file_tag))


def file_extension_okay(filename, required_file_extension, shouldflashprint=True):
    file_extension = filename.rsplit('.', 1)[1].lower()
    if '.' in filename and file_extension == required_file_extension:
        return True
    if shouldflashprint:
        log('Expected file extension: ' + required_file_extension + ' but got: ' + file_extension)
    return False


def save_and_extract_files(js_file, zip_file, task_id):
    js_filename = str(task_id) + ".js"
    zip_filename = str(task_id) + ".zip"
    log('Uploading...')
    js_file.save(os.path.join(app.config['JS_UPLOAD_FOLDER'], js_filename))
    zip_file.save(os.path.join(app.config['ZIP_UPLOAD_FOLDER'], zip_filename))
    log("Successfully uploaded JS and ZIP files")
    extract(task_id)


def extract(task_id):
    with zipfile.ZipFile(app.config['ZIP_UPLOAD_FOLDER'] + str(task_id) + ".zip", "r") as zip_ref:
        zip_ref.extractall(app.config['ZIP_UPLOAD_FOLDER'] + str(task_id) + "/")
