from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String

from app import db


class Tasks(db.Model):
    __tablename__ = "tasks"
    task_id = Column(Integer, primary_key=True)
    time_submitted = Column(DateTime, nullable=False)
    time_started = Column(DateTime)
    time_completed = Column(DateTime)
    in_progress = Column(Boolean)
    is_complete = Column(Boolean)

    # task_id is autoincremented
    def __init__(self, time_submitted):
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
    __tablename__ = "sub_tasks"
    subtask_id = Column(Integer, primary_key=True)
    task_id = Column(Integer,
                     ForeignKey("tasks.task_id",
                                onupdate="CASCADE",
                                ondelete="CASCADE"),
                     index=True)
    data_file = Column(String(255), nullable=False)
    time_submitted = Column(DateTime, nullable=False)
    time_started = Column(DateTime)
    time_completed = Column(DateTime)
    in_progress = Column(Boolean)
    is_complete = Column(Boolean)

    # subtask_id is autoincremented
    def __init__(self, task_id, data_file, time_submitted):
        self.task_id = task_id
        self.data_file = data_file
        self.time_submitted = time_submitted
        self.time_started = None
        self.time_completed = None
        self.in_progress = False
        self.is_complete = False

    def __repr__(self):
        return '<SubTask %r>' % self.subtask_id


class AndroidIDs(db.Model):
    __tablename__ = "android_ids"
    android_id = Column(String(64), primary_key=True)
    session_id = Column(String(32), unique=True)
    is_connected = Column(Boolean, nullable=False)
    is_processing = Column(Boolean, nullable=False)
    subtask_id = Column(Integer)

    # NOTE always use session.merge to avoid key fuck ups
    def __init__(self, android_id, session_id):
        self.android_id = android_id
        self.session_id = session_id
        self.is_connected = True
        self.is_processing = False
        self.subtask_id = None

    def __repr__(self):
        return '<Android_ID %r>' % self.android_id