import os
from datetime import datetime

from flask import current_app as app

from app import db
from app.main import stats
from app.main.files import save_and_extract_files, save_and_extract_js, save_and_extract_zip, \
    remove_task_files, create_res, save_pic
from app.main.logger import log
from app.main.models import Tasks, SubTasks, AndroidIDs, Users, TaskStats
from app.main.sockets import update_task_list
from app.main.stats import ALL_TASKS


def get_task(task_id):
    return Tasks.query.get(task_id)


# possible tasks -> for phone use
def get_task_list():
    # ensure some ID is obtained from phone
    # get_phone(id, sess_id)
    values = Tasks.query.filter_by(is_complete=False).all()
    return [val.to_json() for val in values]


def get_user_tasks(user_id, task_id=ALL_TASKS):
    """ Tasks viewable for a web user (eg his own, or all if root)"""
    if int(user_id) == 1:  # 1 is root, gets all tasks
        values = Tasks.query.all()
    else:
        if task_id == ALL_TASKS:
            values = Tasks.query.filter_by(owner_id=user_id).all()
        else:
            values = Tasks.query.filter(owner_id=user_id).filter(task_id=task_id)
            return values.to_json()

    return [val.to_json() for val in values]


def add_to_db(user_id, js_file, zip_file, task_name, task_desc, task_pic=None):
    """ Creates a task and all its subtasks given the data"""
    task = Tasks(user_id, datetime.utcnow(), task_name, task_desc)

    db.session.add(task)

    # flush to set a task_id for task.
    db.session.flush()

    log('Saving and extracting...')
    if task_pic:
        extension = save_pic(task.task_id, task_pic, app.config['TASK_PICS'])
        task.pic_name = str(task.task_id) + extension
    save_and_extract_files(task.task_id, js_file, zip_file,
                           app.config['JS_FOLDER'],
                           app.config['ZIP_FOLDER'])

    create_subtasks(task.task_id)

    stats.init_stats(task.task_id)

    # make persistent
    db.session.commit()

    return task.task_id


# NOTE DOES NOT SET PERSISTENCE -> does not commit
def create_subtasks(task_id):
    """ Creates individual subtasks given a parent task_id """
    directory = os.path.join(app.config['ZIP_FOLDER'], str(task_id))
    # TODO: NO SUBDIRECTORIES (YET?)
    for filename in os.listdir(directory):
        subtask = SubTasks(task_id, filename, datetime.utcnow())
        db.session.add(subtask)


def remove_from_db(task_id):
    """ Removes a task and all relevant data from the server -> including any
    subtasks and files."""
    task = Tasks.query.get(task_id)
    db.session.delete(task)
    task_data = TaskStats.query.get(task_id)
    db.session.delete(task_data)
    remove_task_files(task_id, task.pic_name, app.config['JS_FOLDER'],
                      app.config['ZIP_FOLDER'], app.config['RES_FOLDER'], app.config['TASK_PICS'])

    db.session.commit()


def update_code_in_db(task_id, js_file):
    """ Changes the code a task refers to"""
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
    """ Changes the data a task refers to + deletes all subtasks
    + recreates them from the new data"""
    save_and_extract_zip(task_id, zip_file, app.config['ZIP_FOLDER'])
    subtasks = SubTasks.query.filter_by(task_id=task_id).all()

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


def get_phone(android_id, session_id):
    """ Check if phone already exists, if not add it to the DB with a session ID"""
    phone = AndroidIDs.query.get(android_id)
    if not phone:
        log("Phone has never been seen before, adding to DB " + android_id + " " + session_id)
        phone = AndroidIDs(android_id, session_id)
        db.session.add(phone)
        db.session.commit()
    return phone


def get_subtask_by_task_id(android_id, session_id, task_id):
    """ Gets a prefered subtask for android_id given the specified task_id"""
    phone = get_phone(android_id, session_id)

    if phone.subtask_id:
        curr_sub = SubTasks.query.get(phone.subtask_id)

        if curr_sub and not curr_sub.is_complete:
            curr_task = Tasks.query.get(curr_sub.task_id)
            return curr_sub.data_file, curr_sub.task_id, curr_task.task_name

    # NOTE: task query only required for the start_task func
    task = Tasks.query.get(task_id)
    if not task or task.is_complete:
        log("Selected task " + str(task_id) + " is unavailable! Either it is already finished, or \
            it doesnt exist.")
        return None, None, None

    subtask = SubTasks.query.\
        filter_by(task_id=task_id, is_complete=False, in_progress=False, has_failed=False).first()
    if not subtask:
        log("Selected task " + str(task_id) + " already has all tasks in progress.")
        return None, None, None

    # set correct values of session id and subtask_id in phone DB
    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, subtask.task_id, task.task_name


def get_next_subtask(android_id, session_id):
    """Returns a tuple of (data file, task id, task name) for the next subtask to be
        done by the phone specified by android_id."""
    phone = get_phone(android_id, session_id)

    if phone.subtask_id:
        curr_sub = SubTasks.query.get(phone.subtask_id)

        if curr_sub and not curr_sub.is_complete:
            curr_task = Tasks.query.get(curr_sub.task_id)
            return curr_sub.data_file, curr_sub.task_id, curr_task.task_name

    # Proposed change below is relevant to these 4 lines.
    task = Tasks.query.filter_by(is_complete=False).order_by(Tasks.task_id.asc()).first()
    if not task:
        log("No more tasks!")
        return None, None, None

    subtask = SubTasks.query.\
        filter_by(task_id=task.task_id, is_complete=False, in_progress=False, has_failed=False). \
        order_by(SubTasks.subtask_id).first()

    if not subtask:
        # TODO: Send a "task(s) complete" message, which causes "All tasks done!"
        # to be displayed on phone UI.
        log("No more subtasks to allocate!")
        return None, None, None

    phone.session_id = session_id
    phone.subtask_id = subtask.subtask_id
    db.session.commit()

    return subtask.data_file, task.task_id, task.task_name


def start_task(android_id):
    """ Marks the phone as started executing in the DB"""
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
    stats.incworkers(task.task_id)
    update_task_list(task.task_id)
    return True


def stop_execution(android_id):
    """ Marks the phone as not executing anymore"""
    phone = AndroidIDs.query.get(android_id)
    if phone and phone.is_processing:
        subtask = SubTasks.query.get(phone.subtask_id)
        task = Tasks.query.filter_by(task_id=subtask.task_id).first()

        phone.is_processing = False
        subtask.in_progress = False
        subtask.has_failed = True
        subtask.time_started = None
        task.some_failed = True
        # NOTE: uses filter() not filter_by(), so as to be able to use | operator.
        # NOTE2:Has a different syntax than filter_by(), double check if changed.
        # finds all subtasks and checks if any are running/completed to update the parent task
        subtasks = SubTasks.query.filter(SubTasks.task_id == subtask.task_id,
                                         (SubTasks.in_progress | SubTasks.is_complete)).all()
        # then need to set task to not running
        if not subtasks:
            task.in_progress = False
            task.time_started = None
        db.session.commit()
        stats.decworkers(task.task_id)
        update_task_list(task.task_id)


def execution_complete(android_id, result):
    """ Marks the calculation as complete, saving the results into the db"""
    phone = AndroidIDs.query.get(android_id)
    if phone and phone.is_processing:
        subtask = SubTasks.query.get(phone.subtask_id)
        if not subtask.is_complete:
            task_id = subtask.task_id
            task = Tasks.query.get(task_id)

            time = datetime.utcnow()

            phone.is_processing = False
            subtask.in_progress = False
            subtask.is_complete = True
            subtask.time_completed = time
            subtask.result = result

            subtasks = SubTasks.query.filter_by(task_id=task_id, is_complete=False).all()
            # if no incomplete subtasks, finished, so update status and generate results
            if not subtasks:
                task.in_progress = False
                task.is_complete = True
                task.time_completed = time
                compl_sub_tasks = SubTasks.query.filter_by(task_id=task_id).all()

                create_res(app.config["RES_FOLDER"], task_id, compl_sub_tasks)

            db.session.commit()
            stats.decworkers(task.task_id)
            update_task_list(task.task_id)


def disconnected(session_id):
    """ Marks a phone as disconnected in the android ID database"""
    phone = AndroidIDs.query.filter_by(session_id=session_id).first()
    if phone:
        phone.is_connected = False
        phone.session_id = None

        db.session.commit()


# USERS

def get_user(user_id):
    return Users.query.get(user_id)


def set_username(user_id, username):
    Users.query.get(user_id).username = username
    db.session.commit()


def set_fullname(user_id, fullname):
    Users.query.get(user_id).fullname = fullname
    db.session.commit()


def set_org(user_id, organisation):
    Users.query.get(user_id).organisation = organisation
    db.session.commit()


def set_password(user_id, new_password):
    Users.query.get(user_id).set_password(new_password)
    db.session.commit()


def set_pic(user_id, user_pic):
    user = get_user(user_id)
    if user_pic:
        extension = save_pic(user_id, user_pic, app.config["USER_PICS"])
        user.pic_name = str(user_id) + extension
    db.session.commit()


def authenticate_user(username, password):
    user = Users.query.filter_by(username=username).first()
    if user and user.check_password(password):
        return user
    return None


def does_user_exist(username):
    user = Users.query.filter_by(username=username).first()
    if user:
        return True
    return False


def add_user(username, password, fullname, organisation, user_pic):
    user = Users(username, password, fullname, organisation)
    db.session.add(user)
    db.session.flush()
    if user_pic:
        extension = save_pic(user.user_id, user_pic, app.config["USER_PICS"])
        user.pic_name = str(user.user_id) + extension
    db.session.commit()

    return user


def restart_failed_tasks(task_id):
    task = Tasks.query.get(task_id)
    subtasks = SubTasks.query.filter_by(task_id=task_id, has_failed=True).all()
    for subtask in subtasks:
        subtask.has_failed = False
    task.some_failed = False
    db.session.commit()
