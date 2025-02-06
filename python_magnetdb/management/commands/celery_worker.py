from django.core.management.base import BaseCommand
import shutil
import subprocess
from watchfiles import run_process

def run_celery():
    celery_cmd = shutil.which('celery')
    cmd = [celery_cmd, '-A', 'python_magnetdb.worker', 'worker', '--loglevel=info']
    subprocess.run(cmd)

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        run_process('./python_magnetdb', target=run_celery)
