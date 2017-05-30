from flask_sqlalchemy import SQLAlchemy
from database.adapter import db

class Tasks(db.Model):
    task_id = db.Column(db.Integer, primary_key=True)
    js_file = db.Column(db.String(255), nullable=False)
    zip_file = db.Column(db.String(255), nullable=False)
    time_submitted = db.Column(db.DateTime, nullable=False)
    time_completed = db.Column(db.DateTime)
    is_complete = db.Column(db.Boolean)

    def __init__(self, js_file, zip_file, time_submitted, time_completed, is_complete):
        self.js_file = js_file
        self.zip_file = zip_file
        self.time_submitted = time_submitted
        self.time_completed = time_completed
        self.is_complete = is_complete

    def __repr__(self):
        return '<Task %r>' % self.task_id


class SubTasks(db.Model):
    task_id = db.Column(db.Integer, primary_key=True) # index this
    subtask_id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    time_submitted = db.Column(db.DateTime, nullable=False)
    time_completed = db.Column(db.DateTime)
    is_complete = db.Column(db.Boolean)

    def __init__(self, task_id, subtask_id, filename, time_submitted, time_completed, is_complete):
        self.task_id = task_id
        self.subtask_id = subtask_id
        self.filename = filename
        self.time_submitted = time_submitted
        self.time_completed = time_completed
        self.is_complete = is_complete

    def __repr__(self):
        return '<SubTask %r>' % self.subtask_id
