#This file is responsible for load balancing and task scheduling, and runs on settings.RUNNER_QUEUE_HOST

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

import logging
import socket
import subprocess
import threading

from runner.models import Task

logger = logging.getLogger(__name__)

class Manager:

    def __init__(self):
        self.current_index = 0
        self.current_lock = threading.Lock()
        self.hosts = []
        for host in settings.RUNNER_HOSTS:
            self.hosts.append((host, threading.Lock()))

    def next_host(self):
        with self.current_lock:
            index = self.current_index
            self.current_index += 1
            if self.current_index >= len(self.hosts):
                self.current_index = 0
        return self.hosts[index]

class Command(BaseCommand):

    def update_leaderboard(self, task):
        for assignment_task in task.assignmenttask_set.all():
            if not task.result:
                continue
            # TODO, this not a great way to get the result...
            from api.v0.views import get_task_result
            result = get_task_result(task)
            if not 'kind' in result:
                continue
            if not result['kind'] == 'benchmark':
                continue
            if not 'speedup' in result:
                continue
            from courses.models import AssignmentLeaderboardEntry
            user = assignment_task.user
            assignment = assignment_task.assignment
            speedup = result['speedup']
            try:
                entry = AssignmentLeaderboardEntry.objects.get(
                    user=user,
                    assignment=assignment,
                )
                if speedup > entry.speedup:
                    entry.speedup = speedup
                    entry.save()
            except AssignmentLeaderboardEntry.DoesNotExist:
                AssignmentLeaderboardEntry.objects.create(
                    user=user,
                    assignment=assignment,
                    speedup=speedup,
                )

    def run_task(self, task):
        self.stdout.write(f'{task} received')
        close_old_connections()

        host, lock = self.manager.next_host()
        with lock:
            self.stdout.write(f'{task} sent to {host}')
            if host == 'localhost':
                py = settings.BASE_DIR / 'venv' / 'bin' / 'python'
                cmd = [py, '-u', 'manage.py', 'runtask', str(task.id)]
            else:
                cmd = [
                    'ssh', f'compeng.gg@{host}',
                    '/opt/compeng.gg/backend/venv/bin/python', '-u',
                    '/opt/compeng.gg/backend/manage.py', 'runtask', str(task.id)
                ]
            p = subprocess.run(cmd, cwd=settings.BASE_DIR)

        # Need to reload the task, since the subprocess updates it
        task = Task.objects.get(id=task.id)
        if p.returncode == 0:
            task.status = Task.Status.SUCCESS
            self.stdout.write(f'{task} success')
        else:
            task.status = Task.Status.FAILURE
            self.stdout.write(f'{task} failure')
        task.save()

        self.update_leaderboard(task)

        close_old_connections()

    def run(self, conn):
        with conn:
            data = conn.recv(1024)
            task_id = int(data)

        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            raise CommandError(f'Task {task_id} does not exist')
        self.run_task(task)

    def _socket_listen(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', settings.RUNNER_QUEUE_PORT))
        s.listen()
        return s

    def handle(self, *args, **options):
        self.manager = Manager()

        for task in Task.objects.filter(status=Task.Status.QUEUED):
            t = threading.Thread(target=Command.run_task, args=(self, task))
            t.start()

        try:
            s = self._socket_listen()
            self.stdout.write(self.style.SUCCESS(
                f'Listening on *:{settings.RUNNER_QUEUE_PORT}'
            ))
        except OSError as err:
            raise CommandError(f'Socket failed: {err}')

        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=Command.run, args=(self, conn))
            t.start()

        s.close()
