from database.adapter import db
from database.models import Tasks, SubTasks
from werkzeug.utils import secure_filename
from datetime import datetime


def add_to_db(js_file, zip_file):

    js_filename = secure_filename(js_file.filename)
    zip_filename = secure_filename(zip_file.filename)

    task = Tasks(js_filename, zip_filename, datetime.utcnow(), None, False)
    db.session.add(task)
    db.session.commit()
    return task.task_id

def get_from_db_by_id(id_val):
    return Tasks.query.filter_by(task_id=id_val).first()

def get_latest():
    return Tasks.query.order_by(Tasks.task_id.desc()).first()
