import os
from datetime import datetime

from werkzeug.utils import secure_filename

from database.adapter import db
from database.models import Tasks, SubTasks, Android_IDs
from misc.files import EXTRACTED_PREFIX
from misc.logger import log


# TODO: CHANGE UNIQUE KEYS FROM FIRST() TO ONE()? check reasons?

def add_to_db(app, js_file, zip_file):
    js_filename = secure_filename(js_file.filename)
    zip_filename = secure_filename(zip_file.filename)

    task = Tasks(js_filename, zip_filename, datetime.utcnow())

    db.session.add(task)

    # flush to set a task_id for task.
    db.session.flush()
    directory = app.config['ZIP_UPLOAD_FOLDER'] + EXTRACTED_PREFIX + zip_filename
    # NOTE: NO SUBDIRECTORIES (YET?)
    for filename in os.listdir(directory):
        subtask = SubTasks(task.task_id, filename, datetime.utcnow())
        db.session.add(subtask)

    # make persistent
    db.session.commit()
    return task.task_id

def get_phone(android_id, session_id):
    phone = Android_IDs.query.filter_by(android_id=android_id).first()
    if not phone:
        print("phone has never been seen before, adding phone to DB.")
        phone = Android_IDs(android_id, session_id)
        db.session.add(phone)
        db.session.commit()
    return phone


def get_by_task_id(android_id, session_id, id_val):
    phone = get_phone(android_id, session_id)

    # NOTE: task query only required for the start_task func
    task = Tasks.query.filter_by(task_id=id_val, is_complete=False).first()
    if not task:
        log("Selected task " + id_val + " is unavailable! Either it is already finished, or it doesnt exist.")
        return None, None, None

    subtask = SubTasks.query.filter_by(task_id=id_val, is_complete=False, in_progress=False).first()
    if not subtask:
        log("Selected task " + id_val + " already has all tasks in progress.")
        return None, None, None

    # set correct values of session id and subtask_id in phone DB
    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, task.zip_file, task.js_file

# order reverse -> run latest submissions first
def get_latest(android_id, session_id):
    phone = get_phone(android_id, session_id)

    subtask = SubTasks.query.filter_by(is_complete=False, in_progress=False).first()
    if not subtask:
            log("No more tasks!")
            return None, None, None

    # by foreign key magic, this has to exist so no point checking for None
    task = Tasks.query.filter_by(task_id=subtask.task_id).first()

    # set correct values of session id and subtask_id in phone DB
    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, task.zip_file, task.js_file

# oldest submissions first
def get_next(android_id, session_id):
    phone = get_phone(android_id, session_id)
    # get next task which isnt finished already -> it CAN be in progress!
    # just means one of its subtasks has/is run(ning)
    tasks = Tasks.query.filter_by(is_complete=False).all()
    if not tasks:
        # list is empty.
        # NOTE: maybe these errors should be handled some other way than flash
        log("No more tasks!")
        return None, None, None
    # here though, dont double book subtasks, so make sure you dont queue an unfinished task
    for task in tasks:
        subtask = SubTasks.query.filter_by(task_id=task.task_id, is_complete=False, in_progress=False).first()
        if subtask:
            # if there are tasks left, continue as usual
            break

    # check if loop ended unsuccessfuly
    if not subtask:
        log("No more subtasks to allocate!")
        return None, None, None

    # set correct values of session id and subtask_id in phone DB
    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, task.zip_file, task.js_file


def start_task(android_id):
    phone = Android_IDs.query.filter_by(android_id=android_id).first()
    if not phone:
        log("Phone not found.")
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
    phone = Android_IDs.query.filter_by(android_id=android_id).first()
    if phone and phone.is_processing:
        subtask = SubTasks.query.filter_by(subtask_id=phone.subtask_id).first()
        task = Tasks.query.filter_by(task_id=subtask.task_id).first()

        phone.is_processing = False
        subtask.in_progress = False
        subtask.time_started = None
        # TODO: update task process + start time if no other processes running it (loop?)
        db.session.commit()

def execution_complete(android_id):
    phone = Android_IDs.query.filter_by(android_id=android_id).first()
    if phone and phone.is_processing:
        subtask = SubTasks.query.filter_by(subtask_id=phone.subtask_id).first()
        if not subtask.is_complete:
            task = Tasks.query.filter_by(task_id=subtask.task_id).first()

            phone.is_processing = False
            subtask.in_progress = False
            subtask.is_complete = True
            subtask.time_completed = datetime.utcnow()

            subtasks = SubTasks.query.filter_by(subtask_id=phone.subtask_id).all()
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
    phone = Android_IDs.query.filter_by(session_id=session_id).first()
    if phone:
        phone.is_connected = False
        phone.session_id = None # NOTE: SQL implementation dependent. OK with PostGreSQL

        db.session.commit()
