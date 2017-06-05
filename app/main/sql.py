# TODO: CHANGE UNIQUE KEYS FROM FIRST() TO ONE()? check reasons?
import os
from datetime import datetime

from flask import current_app as app

from app import db
from app.main.files import save_and_extract_files
from app.main.logger import log
from app.main.models import Tasks, SubTasks, AndroidIDs


def get_task_list(android_id, session_id):
    # ensure some ID is obtained from phone
    get_phone(android_id, session_id)

    values = Tasks.query.filter_by(is_complete=False).all()

    return [val.to_json() for val in values]


def add_to_db(js_file, zip_file):
    task = Tasks(datetime.utcnow())

    db.session.add(task)

    # flush to set a task_id for task.
    db.session.flush()

    log('Saving and extracting...')
    save_and_extract_files(app.config['JS_FOLDER'],
                           app.config['ZIP_FOLDER'],
                           js_file, zip_file, task.task_id)

    directory = app.config['ZIP_FOLDER'] + str(task.task_id)
    # NOTE: NO SUBDIRECTORIES (YET?)
    for filename in os.listdir(directory):
        subtask = SubTasks(task.task_id, filename, datetime.utcnow())
        db.session.add(subtask)

    # make persistent
    db.session.commit()
    return task.task_id


def get_phone(android_id, session_id):
    phone = AndroidIDs.query.filter_by(android_id=android_id).first()
    if not phone:
        log("Phone has never been seen before, adding phone to DB " + android_id + " " + session_id)
        phone = AndroidIDs(android_id, session_id)
        db.session.add(phone)
        db.session.commit()
    return phone


def get_subtask_by_task_id(android_id, session_id, id_val):
    phone = get_phone(android_id, session_id)

    # NOTE: task query only required for the start_task func
    task = Tasks.query.filter_by(task_id=id_val, is_complete=False).first()
    if not task:
        log("Selected task " + str(id_val) + " is unavailable! Either it is already finished, or \
            it doesnt exist.")
        return None, None

    subtask = SubTasks.query.filter_by(task_id=id_val, is_complete=False, in_progress=False).first()
    if not subtask:
        log("Selected task " + str(id_val) + " already has all tasks in progress.")
        return None, None

    # set correct values of session id and subtask_id in phone DB
    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, subtask.task_id


# order reverse -> run latest submissions first
def get_latest_subtask(android_id, session_id):
    phone = get_phone(android_id, session_id)

    subtask = SubTasks.query.order_by(SubTasks.subtask_id.desc()).\
        filter_by(is_complete=False, in_progress=False).first()

    if not subtask:
        log("No more tasks!")
        return None, None

    # set correct values of session id and subtask_id in phone DB
    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, subtask.task_id


# Returns a tuple of (data file, task id) for the next subtask to be
# done by the phone specified by android_id.
def get_next_subtask(android_id, session_id):
    phone = get_phone(android_id, session_id)

    # Proposed change below is relevant to these 4 lines.
    incomplete_tasks = Tasks.query.filter_by(is_complete=False).all()
    if not incomplete_tasks:
        log("No more tasks!")
        return None, None

    # TODO: Must add an "endorsed_task(s)" field (or equivalent) to AndroidIDs table.
    endorsed_task_id = incomplete_tasks[0].task_id

    subtask = fetch_incomplete_subtask(endorsed_task_id)

    if not subtask:
        # TODO: Send a "task(s) complete" message, which causes "All tasks done!" to be displayed on phone UI.
        log("No more subtasks to allocate!")
        return None, None

    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, endorsed_task_id


def fetch_incomplete_subtask(task_id):
    return SubTasks.query. \
        filter_by(task_id=task_id, is_complete=False, in_progress=False). \
        order_by(SubTasks.subtask_id).first()


def start_task(android_id):
    phone = AndroidIDs.query.filter_by(android_id=android_id).first()
    if not phone:
        log("Phone not found - " + android_id)
        return

    subtask = SubTasks.query.filter_by(subtask_id=phone.subtask_id).first()
    if not subtask:
        log("No subtask found at: " + str(phone.subtask_id))
        return False
    task = Tasks.query.filter_by(task_id=subtask.task_id).first()

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
    phone = AndroidIDs.query.filter_by(android_id=android_id).first()
    if phone and phone.is_processing:
        subtask = SubTasks.query.filter_by(subtask_id=phone.subtask_id).first()
        # task = Tasks.query.filter_by(task_id=subtask.task_id).first()

        phone.is_processing = False
        subtask.in_progress = False
        subtask.time_started = None
        # TODO: update task process + start time if no other processes running it (loop?)
        db.session.commit()


def execution_complete(android_id):
    phone = AndroidIDs.query.filter_by(android_id=android_id).first()
    if phone and phone.is_processing:
        subtask = SubTasks.query.filter_by(subtask_id=phone.subtask_id).first()
        if not subtask.is_complete:
            task = Tasks.query.filter_by(task_id=subtask.task_id).first()

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
