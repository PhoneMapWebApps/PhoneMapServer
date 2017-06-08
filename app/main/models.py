from time import strftime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, ARRAY, Text
from werkzeug.security import generate_password_hash, check_password_hash

from app import db


class Tasks(db.Model):
    TIME_FORMAT = "%b %d %Y %H:%M:%S"
    __tablename__ = "tasks"
    task_id = Column(Integer, primary_key=True)
    owner_id = Column(Integer,
                      ForeignKey("users.user_id",
                                 onupdate="CASCADE",
                                 ondelete="CASCADE"),
                      nullable=False)
    task_name = Column(String(255), nullable=False)
    task_desc = Column(Text, nullable=False)  # is empty string null in SQL?
    time_submitted = Column(DateTime, nullable=False)
    time_started = Column(DateTime)
    time_completed = Column(DateTime)
    in_progress = Column(Boolean)
    is_complete = Column(Boolean)

    # task_id is autoincremented
    def __init__(self, owner_id, time_submitted, task_name="No Name Given", task_desc="No Desc Given"):
        self.owner_id = owner_id
        self.task_name = task_name
        self.task_desc = task_desc
        self.time_submitted = time_submitted
        self.time_started = None
        self.time_completed = None
        self.in_progress = False
        self.is_complete = False

    def to_json(self):
        submitted = strftime(self.TIME_FORMAT, self.time_submitted.timetuple())
        started = ""
        if self.time_started:
            started = strftime(self.TIME_FORMAT, self.time_started.timetuple())
        completed = ""
        if self.time_completed:
            completed = strftime(self.TIME_FORMAT, self.time_completed.timetuple())
        return {"task_id": self.task_id,
                "task_name": self.task_name,
                "time_submitted": submitted,
                "time_started": started,
                "time_completed": completed,
                "in_progress": self.in_progress,
                "is_complete": self.is_complete,
                "task_desc": self.task_desc}

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
    endorsed_tasks = Column(ARRAY(Integer))
    subtask_id = Column(Integer)

    def __init__(self, android_id, session_id):
        self.android_id = android_id
        self.session_id = session_id
        self.is_connected = True
        self.is_processing = False
        self.endorsed_tasks = []
        self.subtask_id = None

    def __repr__(self):
        return '<Android_ID %r>' % self.android_id


class Users(db.Model):
    __tablename__ = "users"
    user_id = db.Column(Integer, primary_key=True)
    username = db.Column(String(255), unique=True)
    password = db.Column(String, nullable=False)

    def __init__(self, username, password):
        self.username = username
        self.set_password(password)

    def __repr__(self):
        return "%d/%s" % (self.user_id, self.username)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    @property
    def is_active(self):
        return True

    def get_id(self):
        return self.user_id

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def __eq__(self, other):
        if isinstance(other, db.Model):
            return self.get_id() == other.get_id()
        return NotImplemented

    def __ne__(self, other):
        equal = self.__eq__(other)
        if equal is NotImplemented:
            return NotImplemented
        return not equal
