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
        time = datetime.now()
        time_str = strftime(self.TIME_FORMAT, time.timetuple())

        self.dict_phoneids = defaultdict(list)
        self.dict_numworkers = {}
        self.dict_worker_stats = defaultdict(list)
        self.dict_numworkers[ALL_TASKS] = 0
        self.dict_worker_stats[ALL_TASKS].append((time_str, self.dict_numworkers[ALL_TASKS]))

    # DOES NOT COMMIT - is done later
    def init_stats(self, task_id):
        time = datetime.now()
        time_str = strftime(self.TIME_FORMAT, time.timetuple())

        all_tasks = TaskStats.query.get(ALL_TASKS)
        if not all_tasks:
            all_tasks = TaskStats(ALL_TASKS)
            db.session.add(all_tasks)

        self.dict_numworkers[task_id] = 0
        curtask = TaskStats(task_id)

        curtask.worker_stats[time_str] = self.dict_numworkers[task_id]
        all_tasks.worker_stats[time_str] = self.dict_numworkers[ALL_TASKS]

        self.dict_worker_stats[task_id].append((time_str, self.dict_numworkers[task_id]))

        db.session.add(curtask)
        flag_modified(curtask, "worker_stats")
        flag_modified(all_tasks, "worker_stats")

    def incworkers(self, task_id, android_id):
        if android_id in self.dict_phoneids[task_id]:
            return False

        time = datetime.now()
        time_str = strftime(self.TIME_FORMAT, time.timetuple())

        curtask = TaskStats.query.get(task_id)
        all_tasks = TaskStats.query.get(ALL_TASKS)

        self.dict_numworkers[task_id] += 1
        self.dict_phoneids[task_id].append(android_id)
        self.dict_numworkers[ALL_TASKS] += 1  # total

        curtask.worker_stats[time_str] = self.dict_numworkers[task_id]
        all_tasks.worker_stats[time_str] = self.dict_numworkers[ALL_TASKS]

        self.dict_worker_stats[task_id].append((time_str, self.dict_numworkers[task_id]))
        self.dict_worker_stats[ALL_TASKS].append((time_str, self.dict_numworkers[ALL_TASKS]))

        flag_modified(curtask, "worker_stats")
        flag_modified(all_tasks, "worker_stats")
        db.session.commit()
        return True

    def decworkers(self, task_id, android_id):
        if task_id in self.dict_numworkers:
            if self.dict_numworkers[task_id] <= 0:
                return

        time = datetime.now()
        time_str = strftime(self.TIME_FORMAT, time.timetuple())

        curtask = TaskStats.query.get(task_id)
        all_tasks = TaskStats.query.get(ALL_TASKS)

        self.dict_phoneids[task_id].remove(android_id)

        self.dict_numworkers[task_id] -= 1
        self.dict_numworkers[ALL_TASKS] -= 1  # total

        curtask.worker_stats[time_str] = self.dict_numworkers[task_id]
        all_tasks.worker_stats[time_str] = self.dict_numworkers[ALL_TASKS]

        self.dict_worker_stats[task_id].append((time_str, self.dict_numworkers[task_id]))
        self.dict_worker_stats[ALL_TASKS].append((time_str, self.dict_numworkers[ALL_TASKS]))

        flag_modified(curtask, "worker_stats")
        flag_modified(all_tasks, "worker_stats")
        db.session.commit()

    def finish(self, task_id):
        time = datetime.now()
        time_str = strftime(self.TIME_FORMAT, time.timetuple())

        curtask = TaskStats.query.get(task_id)

        self.dict_numworkers[task_id] = 0
        curtask.worker_stats[time_str] = self.dict_numworkers[task_id]
        self.dict_worker_stats[task_id].append((time_str, self.dict_numworkers[task_id]))

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
