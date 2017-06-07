import os
import shutil
import zipfile

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
    return not (request_files_missing(request_files, file_tag)
                or request_files_empty(request_files[file_tag], file_tag))


def file_extension_okay(filename, required_file_extension):
    file_extension = filename.rsplit('.', 1)[1].lower()
    if '.' in filename and file_extension == required_file_extension:
        return True
    log('Expected file extension: ' + required_file_extension + ' but got: ' + file_extension)
    return False


def save_and_extract_files(task_id, js_file, zip_file, js_path, zip_path):
    log('Uploading...')

    save_and_extract_js(task_id, js_file, js_path)
    save_and_extract_zip(task_id, zip_file, zip_path)

    log("Successfully uploaded JS and ZIP files, as well as set task name and description")


def save_and_extract_js(task_id, js_file, js_path):
    js_filename = str(task_id) + ".js"
    # TODO: fix tests to use FileStorage and not a reader -> remove this IF statement
    if hasattr(js_file, 'save'):
        js_file.save(os.path.join(js_path, js_filename))
    else:
        shutil.copyfile(js_file.name, os.path.join(js_path, js_filename))


def save_and_extract_zip(task_id, zip_file, zip_path):
    zip_filename = str(task_id) + ".zip"
    # TODO: fix tests to use FileStorage and not a reader -> remove this IF statement
    if hasattr(zip_file, 'save'):
        zip_file.save(os.path.join(zip_path, zip_filename))
    else:
        shutil.copyfile(zip_file.name, os.path.join(zip_path, zip_filename))
    extract(zip_path, task_id)


def extract(zip_path, task_id):
    if os.path.isdir(zip_path + str(task_id)):
        shutil.rmtree(zip_path + str(task_id))
    with zipfile.ZipFile(zip_path + str(task_id) + ".zip", "r") as zip_ref:
        zip_ref.extractall(zip_path + str(task_id) + "/")


def remove_task_files(task_id, js_folder, zip_folder):
    os.remove(js_folder + str(task_id) + '.js')
    os.remove(zip_folder + str(task_id) + '.zip')
    shutil.rmtree(zip_folder + str(task_id))
