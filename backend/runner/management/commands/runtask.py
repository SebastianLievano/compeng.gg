#This file represents the code that runs on the raspberry pi runners. 


from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from social_django.models import UserSocialAuth
from runner.models import Task
from github_app.utils import get_dir, get_file

import shlex
import subprocess

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("task_id", type=int)

    def handle(self, *args, **options):
        task_id = options["task_id"]
        try:
            task = Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            raise CommandError(f'Task {task_id} does not exist')

        task.status = Task.Status.IN_PROGRESS
        task.save()
        self.stdout.write(f'{task} in progress')

        try:
            social = UserSocialAuth.objects.get(
                provider='github', uid=task.push.payload['sender']['id']
            )
        except UserSocialAuth.DoesNotExist:
            raise CommandError(f'Task does not have a valid user')

        assignment_task = task.assignmenttask_set.get() # TODO: this is bad
        # If this is true, it should be a OneToOneField, if not it should
        # be more flexible. Ideally separate the files to mount.
        assignment = assignment_task.assignment
        push = task.push
        runner = task.runner

        volume_args = []
        for file_path in assignment.files:
            if not file_path.endswith('/'):
                file_full_path = get_file(push.payload['repository']['name'], file_path, push.payload['after'])
                volume_args += ['-v', f'{file_full_path}:/workspace/{file_path}']
            else:
                dir_full_path = get_dir(push.payload['repository']['name'], file_path, push.payload['after'])
                volume_args += ['-v', f'{dir_full_path}:/workspace/{file_path}']

        # TODO: make this better
        # 1. The extra options for a leaderboard shouldn't be hardcoded
        # 2. Whenever `docker run` starts, we should grab the container id.
        #    Killing the `docker run` command does not stop the command running
        #    in the container. It should `docker stop` only the container this
        #    task created.
        if runner.image == '2024-fall-ece454-runner:latest' and runner.command == '/workspace/lab2/benchmark.py':
            cmd = ['docker', 'run', '--rm',
              '--network', 'none',
              '-e', 'RUNNER_MACHINE=rpi4',
              '-e', 'ECE454_2024_FALL_LAB2_REFERENCE=96855895713',
            ] + volume_args + [runner.image]
            cmd += shlex.split(runner.command)
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            except subprocess.TimeoutExpired:
                containers = subprocess.run([
                    'docker', 'ps', '-a', '-q'
                ], stdout=subprocess.PIPE, text=True).stdout.splitlines()
                if len(containers) > 0:
                    subprocess.run(['docker', 'stop'] + containers,
                                   stdout=subprocess.DEVNULL)
                task.result = {'error': 'timeout'}
                task.save()
                exit(1)
        elif runner.image == '2024-fall-ece454-runner:latest' and runner.command == '/workspace/lab3/grade.py':
            cmd = ['docker', 'run', '--rm',
              '--network', 'none',
              '-e', 'RUNNER_MACHINE=rpi4',
            ] + volume_args + [runner.image]
            cmd += shlex.split(runner.command)
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            except subprocess.TimeoutExpired:
                containers = subprocess.run([
                    'docker', 'ps', '-a', '-q'
                ], stdout=subprocess.PIPE, text=True).stdout.splitlines()
                if len(containers) > 0:
                    subprocess.run(['docker', 'stop'] + containers,
                                   stdout=subprocess.DEVNULL)
                task.result = {'error': 'timeout'}
                task.save()
                exit(1)
        elif runner.image == '2024-fall-ece454-runner:latest' and runner.command == '/workspace/lab5-runner/benchmark.py':
            cmd = ['docker', 'run', '--rm',
              '-e', 'RUNNER_MACHINE=rpi4',
            ] + volume_args + [runner.image]
            cmd += shlex.split(runner.command)
            p = subprocess.run(cmd, capture_output=True, text=True)
        elif runner.image == '2024-fall-ece344-runner:latest' and runner.command == '/workspace/hello-ext2/grade.py --json':
            cmd = ['docker', 'run', '--rm',
              '--network', 'none',
              '--privileged',
            ] + volume_args + [runner.image]
            cmd += shlex.split(runner.command)
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            except subprocess.TimeoutExpired:
                containers = subprocess.run([
                    'docker', 'ps', '-a', '-q'
                ], stdout=subprocess.PIPE, text=True).stdout.splitlines()
                if len(containers) > 0:
                    subprocess.run(['docker', 'stop'] + containers,
                                   stdout=subprocess.DEVNULL)
                task.result = {'error': 'timeout'}
                task.save()
                exit(1)
        else:
            cmd = ['docker', 'run', '--rm', '--network', 'none']
            cmd += volume_args + [runner.image]
            cmd += shlex.split(runner.command)
            try:
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            except subprocess.TimeoutExpired:
                containers = subprocess.run([
                    'docker', 'ps', '-a', '-q'
                ], stdout=subprocess.PIPE, text=True).stdout.splitlines()
                if len(containers) > 0:
                    subprocess.run(['docker', 'stop'] + containers,
                                   stdout=subprocess.DEVNULL)
                task.result = {'error': 'timeout'}
                task.save()
                exit(1)
        task.result = p.stdout
        task.save()
        exit(p.returncode)
