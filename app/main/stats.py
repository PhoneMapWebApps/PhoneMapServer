from datetime import datetime

from collections import defaultdict
from time import strftime

from flask import json
from sqlalchemy.orm.attributes import flag_modified

from app import db
from app.main.models import TaskStats

ALL_TASKS = -1


class StatsManager:
    TIME_FORMAT = "%b %d %Y %H:%M:%S"
    STAT_HISTORY = 50

    def __init__(self):
        self.dict_numworkers = {}
        self.dict_worker_stats = defaultdict(list)
        self.dict_numworkers[ALL_TASKS] = 0

    def incworkers(self, task_id):
        time = datetime.utcnow()
        time_dict = strftime(self.TIME_FORMAT, time.timetuple())

        curtask = TaskStats.query.get(task_id)
        if not curtask:
            curtask = TaskStats(task_id)
            db.session.add(curtask)
            db.session.commit()
            self.dict_numworkers[task_id] = 0

        self.dict_numworkers[task_id] += 1
        self.dict_numworkers[ALL_TASKS] += 1  # total
        curtask.worker_stats[time_dict] = self.dict_numworkers[task_id]
        self.dict_worker_stats[task_id].append((time_dict, self.dict_numworkers[task_id]))
        flag_modified(curtask, "worker_stats")
        db.session.commit()

    def decworkers(self, task_id):
        time = datetime.utcnow()
        time_dict = strftime(self.TIME_FORMAT, time.timetuple())

        curtask = TaskStats.query.get(task_id)
        self.dict_numworkers[task_id] -= 1
        self.dict_numworkers[ALL_TASKS] -= 1  # total
        curtask.worker_stats[time_dict] = self.dict_numworkers[task_id]
        self.dict_worker_stats[task_id].append((time_dict, self.dict_numworkers[task_id]))
        flag_modified(curtask, "worker_stats")
        db.session.commit()

    def get_workertimes_json(self):
        # if server was reloaded or crashed, lookup these from DB
        if len(self.dict_numworkers) <= 1:
            stats_all = TaskStats.query.all()
            for task_stat in stats_all:
                dict = task_stat.worker_stats
                for key, value in dict.items():
                    self.dict_worker_stats[task_stat.task_id].append((key, value))
                self.dict_numworkers[task_stat.task_id] = dict[max(dict.keys())]

        return json.dumps(self.dict_worker_stats)
