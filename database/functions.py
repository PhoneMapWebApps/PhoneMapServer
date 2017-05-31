import os
from database.adapter import db
from database.models import Tasks, SubTasks
from werkzeug.utils import secure_filename
from datetime import datetime
from misc.files import EXTRACTED_PREFIX
from misc.helper import flashprint


def add_to_db(app, js_file, zip_file):
    js_filename = secure_filename(js_file.filename)
    zip_filename = secure_filename(zip_file.filename)

    task = Tasks(zip_filename, datetime.utcnow())

    db.session.add(task)

    # flush to set a task_id for task.
    db.session.flush()
    directory = app.config['ZIP_UPLOAD_FOLDER'] + EXTRACTED_PREFIX + zip_filename
    # NOTE: NO SUBDIRECTORIES (YET?)
    for filename in os.listdir(directory):
        subtask = SubTasks(task.task_id, js_filename, filename, datetime.utcnow())
        db.session.add(subtask)

    # make persistent
    db.session.commit()
    return task.task_id


def get_by_task_id(id_val):
    # NOTE: task query only required for the start_task func
    task = Tasks.query.filter_by(task_id=id_val, is_complete=False).first()
    if not task:
        flashprint("Selected task " + id_val + " is unavailable! Either it is already finished, or it doesnt exist.")
        return None, None, None

    subtask = SubTasks.query.filter_by(task_id=id_val, is_complete=False, in_progress=False).first()
    if not subtask:
        flashprint("Selected task " + id_val + " already has all tasks in progress.")
        return None, None, None

    start_task(task, subtask)

    return subtask.data_file, task.zip_file, subtask.js_file

# order reverse -> run latest submissions first
def get_latest():
    subtask = SubTasks.query.filter_by(is_complete=False, in_progress=False).first()
    if not subtask:
            flashprint("No more tasks!")
            return None, None, None

    # by foreign key magic, this has to exist so no point checking for None
    task = Tasks.query.filter_by(task_id=subtask.task_id).first()

    start_task(task, subtask)

    return subtask.data_file, task.zip_file, subtask.js_file

# oldest submissions first
def get_next():
    # get next task which isnt finished already -> it CAN be in progress!
    # just means one of its subtasks has/is run(ning)
    tasks = Tasks.query.filter_by(is_complete=False).all()
    if not tasks:
        # list is empty.
        # NOTE: maybe these errors should be handled some other way than flash
        flashprint("No more tasks!")
        return None, None, None
    # here though, dont double book subtasks, so make sure you dont queue an unfinished task
    for task in tasks:
        subtask = SubTasks.query.filter_by(task_id=task.task_id, is_complete=False, in_progress=False).first()
        if subtask:
            # if there are tasks left, continue as usual
            break

    # check if loop ended unsuccessfuly
    if not subtask:
        flashprint("No more subtasks to allocate!")
        return None, None, None

    start_task(task, subtask)

    return subtask.data_file, task.zip_file, subtask.js_file

def start_task(task, subtask):
    task.in_progress = True
    subtask.in_progress = True
    if task.time_started == None:
        task.time_started = datetime.utcnow()
    subtask.time_started = datetime.utcnow()
    db.session.commit()
