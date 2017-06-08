import os
from datetime import datetime

from flask import current_app as app

from app import db
from app.main.files import save_and_extract_files, save_and_extract_js, save_and_extract_zip, \
    remove_task_files
from app.main.logger import log
from app.main.models import Tasks, SubTasks, AndroidIDs, Users


def get_task_list():
    # ensure some ID is obtained from phone
    # get_phone(id, sess_id)
    values = Tasks.query.filter_by(is_complete=False).all()
    return [val.to_json() for val in values]


def get_all_tasks():
    values = Tasks.query.all()
    return [val.to_json() for val in values]


def get_user_tasks(user_id):
    values = Tasks.query.filter_by(owner_id=user_id).all()
    return [val.to_json() for val in values]


def add_to_db(user_id, js_file, zip_file, task_name, task_desc):
    task = Tasks(user_id, datetime.utcnow(), task_name, task_desc)

    db.session.add(task)

    # flush to set a task_id for task.
    db.session.flush()

    log('Saving and extracting...')
    save_and_extract_files(task.task_id, js_file, zip_file,
                           app.config['JS_FOLDER'],
                           app.config['ZIP_FOLDER'])

    create_subtasks(task.task_id)

    # make persistent
    db.session.commit()
    return task.task_id


def remove_from_db(task_id):
    task = Tasks.query.get(task_id)
    db.session.delete(task)
    remove_task_files(task_id, app.config['JS_FOLDER'], app.config['ZIP_FOLDER'])
    db.session.commit()


def update_code_in_db(task_id, js_file):
    save_and_extract_js(task_id, js_file, app.config['JS_FOLDER'])
    subtasks = SubTasks.query.filter_by(task_id=task_id).all()

    for subtask in subtasks:
        subtask.is_complete = False
        subtask.in_progress = False
        subtask.time_started = None
        subtask.time_completed = None

    task = Tasks.query.get(task_id)
    task.is_complete = False
    task.in_progress = False
    task.time_started = None
    task.time_completed = None

    # make persistent
    db.session.commit()


def update_data_in_db(task_id, zip_file):
    save_and_extract_zip(task_id, zip_file, app.config['ZIP_FOLDER'])
    subtasks = SubTasks.query.filter_by(task_id=task_id).all()
    print(subtasks)
    for subtask in subtasks:
        db.session.delete(subtask)
    create_subtasks(task_id)

    task = Tasks.query.get(task_id)
    task.is_complete = False
    task.in_progress = False
    task.time_started = None
    task.time_completed = None

    # make persistent
    db.session.commit()


# NOTE DOES NOT SET PERSISTENCE -> does not commit
def create_subtasks(task_id):
    directory = app.config['ZIP_FOLDER'] + str(task_id)
    # TODO: NO SUBDIRECTORIES (YET?)
    for filename in os.listdir(directory):
        subtask = SubTasks(task_id, filename, datetime.utcnow())
        db.session.add(subtask)


def get_phone(android_id, session_id):
    phone = AndroidIDs.query.get(android_id)
    if not phone:
        log("Phone has never been seen before, adding phone to DB " + android_id + " " + session_id)
        phone = AndroidIDs(android_id, session_id)
        db.session.add(phone)
        db.session.commit()
    return phone


def get_subtask_by_task_id(android_id, session_id, task_id):
    phone = get_phone(android_id, session_id)

    # NOTE: task query only required for the start_task func
    task = Tasks.query.get(task_id)
    if not task or task.is_complete:
        log("Selected task " + str(task_id) + " is unavailable! Either it is already finished, or \
            it doesnt exist.")
        return None, None, None

    subtask = SubTasks.query.filter_by(task_id=task_id, is_complete=False, in_progress=False).first()
    if not subtask:
        log("Selected task " + str(task_id) + " already has all tasks in progress.")
        return None, None, None

    # set correct values of session id and subtask_id in phone DB
    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, subtask.task_id, task.task_name


# order reverse -> run latest submissions first
def get_latest_subtask(android_id, session_id):
    phone = get_phone(android_id, session_id)

    subtask = SubTasks.query.order_by(SubTasks.subtask_id.desc()).\
        filter_by(is_complete=False, in_progress=False).first()

    if not subtask:
        log("No more tasks!")
        return None, None, None

    task = Tasks.query.get(subtask.task_id)

    # set correct values of session id and subtask_id in phone DB
    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, subtask.task_id, task.task_name


# Returns a tuple of (data file, task id) for the next subtask to be
# done by the phone specified by android_id.
def get_next_subtask(android_id, session_id):
    phone = get_phone(android_id, session_id)

    # Proposed change below is relevant to these 4 lines.
    incomplete_tasks = Tasks.query.filter_by(is_complete=False).all()
    if not incomplete_tasks:
        log("No more tasks!")
        return None, None, None

    # TODO: Must add an "endorsed_task(s)" field (or equivalent) to AndroidIDs table.
    endorsed_task_id = incomplete_tasks[0].task_id
    endorsed_task_name = incomplete_tasks[0].task_name

    subtask = fetch_incomplete_subtask(endorsed_task_id)

    if not subtask:
        # TODO: Send a "task(s) complete" message, which causes "All tasks done!"
        # to be displayed on phone UI.
        log("No more subtasks to allocate!")
        return None, None, None

    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, endorsed_task_id, endorsed_task_name


def fetch_incomplete_subtask(task_id):
    return SubTasks.query. \
        filter_by(task_id=task_id, is_complete=False, in_progress=False). \
        order_by(SubTasks.subtask_id).first()


def start_task(android_id):
    phone = AndroidIDs.query.get(android_id)
    if not phone:
        log("Phone not found - " + android_id)
        return

    subtask = SubTasks.query.filter_by(subtask_id=phone.subtask_id).first()
    if not subtask:
        log("No subtask found at: " + str(phone.subtask_id))
        return False
    task = Tasks.query.get(subtask.task_id)

    if subtask.is_complete:
        # return false so as to emit a "stop executing" signal
        return False

    phone.is_processing = True
    task.in_progress = True
    subtask.in_progress = True
    if not task.time_started:
        task.time_started = datetime.utcnow()
    subtask.time_started = datetime.utcnow()

    db.session.commit()
    return True


def stop_execution(android_id):
    phone = AndroidIDs.query.get(android_id)
    if phone and phone.is_processing:
        subtask = SubTasks.query.get(phone.subtask_id)
        # task = Tasks.query.filter_by(task_id=subtask.task_id).first()

        phone.is_processing = False
        subtask.in_progress = False
        subtask.time_started = None
        # TODO: update task process + start time if no other processes running it (loop?)
        db.session.commit()


def execution_complete(android_id):
    phone = AndroidIDs.query.get(android_id)
    if phone and phone.is_processing:
        subtask = SubTasks.query.get(phone.subtask_id)
        if not subtask.is_complete:
            task = Tasks.query.get(subtask.task_id)

            phone.is_processing = False
            subtask.in_progress = False
            subtask.is_complete = True
            subtask.time_completed = datetime.utcnow()

            subtasks = SubTasks.query.filter_by(task_id=subtask.task_id).all()
            for sub in subtasks:
                if not sub.is_complete:
                    # dont set task as complete, return now instead
                    db.session.commit()
                    return

            task.in_progress = False
            task.is_complete = True
            task.time_completed = datetime.utcnow()

            db.session.commit()


def disconnected(session_id):
    phone = AndroidIDs.query.filter_by(session_id=session_id).first()
    if phone:
        phone.is_connected = False
        phone.session_id = None  # NOTE: SQL implementation dependent. OK with PostGreSQL

        db.session.commit()


def authenticate_user(username, password):
    user = Users.query.filter_by(username=username).first()
    if user and user.check_password(password):
        db.session.commit()
        return user
    return None


def does_user_exist(username):
    user = Users.query.filter_by(username=username).first()
    if user:
        return True
    return False


def add_user(username, password):
    user = Users(username, password)
    db.session.add(user)
    db.session.commit()
    return user
