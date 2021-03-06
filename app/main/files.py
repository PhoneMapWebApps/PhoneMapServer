import os
import shutil
import zipfile

from flask import flash


def flashmsg(msg):
    try:
        flash(msg)
    except RuntimeError:
        pass


def request_files_empty(request_result, filetype):
    if request_result.filename == '' or request_result.filename is None:
        flashmsg('Empty in submission: ' + filetype)
        return True
    return False


def request_files_missing(request_files, filetype):
    if filetype not in request_files:
        flashmsg('Missing from submission: ' + filetype)
        return True
    return False


def request_file_exists(request_files, file_tag):
    return not (request_files_missing(request_files, file_tag)
                or request_files_empty(request_files[file_tag], file_tag))


def file_extension_okay(filename, required_file_extension):
    file_extension = filename.rsplit('.', 1)[1].lower()
    if '.' in filename and file_extension == required_file_extension:
        return True
    flashmsg('Expected file extension: ' + required_file_extension + ' but got: ' + file_extension)
    return False


def save_and_extract_files(task_id, js_file, zip_file, js_path, zip_path):
    flashmsg('Uploading...')

    save_and_extract_js(task_id, js_file, js_path)
    save_and_extract_zip(task_id, zip_file, zip_path)

    flashmsg("Successfully uploaded picture, JS, and ZIP files, as well as set task name and description")


def save_and_extract_js(task_id, js_file, js_path):
    js_filename = str(task_id) + ".js"
    # TODO: fix tests to use FileStorage and not a reader -> remove this IF statement
    if hasattr(js_file, 'save'):
        js_file.save(os.path.join(js_path, js_filename))
    else:
        shutil.copyfile(js_file.name, os.path.join(js_path, js_filename))


def save_pic(name, pic, pic_path):
    extension = "." + pic.filename.rsplit('.', 1)[1].lower()
    pic_filename = str(name) + extension
    if hasattr(pic, 'save'):
        pic.save(os.path.join(pic_path, pic_filename))
    else:
        shutil.copyfile(pic.name, os.path.join(pic_path, pic_filename))
    return extension


def save_and_extract_zip(task_id, zip_file, zip_path):
    zip_filename = str(task_id) + ".zip"
    # TODO: fix tests to use FileStorage and not a reader -> remove this IF statement
    if hasattr(zip_file, 'save'):
        zip_file.save(os.path.join(zip_path, zip_filename))
    else:
        shutil.copyfile(zip_file.name, os.path.join(zip_path, zip_filename))
    extract(zip_path, task_id)


def extract(zip_path, task_id):
    folder_path = os.path.join(zip_path, str(task_id))  # no trailing /
    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
    with zipfile.ZipFile(folder_path + ".zip", "r") as zip_ref:
        zip_ref.extractall(os.path.join(folder_path, ""))


def remove_task_files(task_id, pic_name, js_folder, zip_folder, res_folder, pics_folder):
    os.remove(os.path.join(js_folder, str(task_id) + '.js'))
    os.remove(os.path.join(zip_folder, str(task_id) + '.zip'))
    try:
        os.remove(os.path.join(res_folder, str(task_id) + '.zip'))
    except FileNotFoundError:
        pass
    else:
        shutil.rmtree(os.path.join(res_folder, str(task_id)))

    if pic_name != "default.jpg" and os.path.isfile(os.path.join(pics_folder, pic_name)):
        os.remove(os.path.join(pics_folder, pic_name))

    shutil.rmtree(os.path.join(zip_folder, str(task_id)))


def create_res(res_path, task_id, compl_subtasks):
    folder_path = os.path.join(res_path, str(task_id))
    if os.path.isdir(folder_path):
        shutil.rmtree(folder_path)

    os.makedirs(folder_path)

    for idx, val in enumerate(compl_subtasks):
        file_path = os.path.join(folder_path, str(idx) + ".txt")
        with open(file_path, "w") as res_file:
            res_file.write(val.result)

    shutil.make_archive(folder_path, 'zip', folder_path)
