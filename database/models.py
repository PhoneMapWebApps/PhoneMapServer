from flask_sqlalchemy import SQLAlchemy
from database.adapter import db

class Tasks(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    zip_file = db.Column(db.String(255), nullable=False)
    time_submitted = db.Column(db.DateTime, nullable=False)
    time_started = db.Column(db.DateTime)
    time_completed = db.Column(db.DateTime)
    in_progress = db.Column(db.Boolean)
    is_complete = db.Column(db.Boolean)

    # task_id is autoincremented
    def __init__(self, zip_file, time_submitted):
        self.zip_file = zip_file
        self.time_submitted = time_submitted
        self.time_started = None
        self.time_completed = None
        self.in_progress = False
        self.is_complete = False

    def __repr__(self):
        return '<Task %r>' % self.task_id


# NOTE: could easily increment the subtask_id myself and have task_id as
# first col and as a primary_key. This would be done in the add_to_db function.
# However, this would cancel the uniqueness of the subtask_id.
# Currently, all subtasks have unique ID's
class SubTasks(db.Model):
    subtask_id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer,
                        db.ForeignKey("tasks.task_id",
                                      onupdate="CASCADE",
                                      ondelete="CASCADE"),
                        index=True)
    js_file = db.Column(db.String(255), nullable=False)
    data_file = db.Column(db.String(255), nullable=False)
    time_submitted = db.Column(db.DateTime, nullable=False)
    time_started = db.Column(db.DateTime)
    time_completed = db.Column(db.DateTime)
    in_progress = db.Column(db.Boolean)
    is_complete = db.Column(db.Boolean)


    # subtask_id is autoincremented
    def __init__(self, task_id, js_file, data_file, time_submitted):
        self.task_id = task_id
        self.js_file = js_file
        self.data_file = data_file
        self.time_submitted = time_submitted
        self.time_started = None
        self.time_completed = None
        self.in_progress = False
        self.is_complete = False

    def __repr__(self):
        return '<SubTask %r>' % self.subtask_id
