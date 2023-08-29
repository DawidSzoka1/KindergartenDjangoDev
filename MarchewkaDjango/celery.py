from __future__ import absolute_import, unicode_literals
from celery.schedules import crontab
import os

from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MarchewkaDjango.settings')

app = Celery('MarchewkaDjango')
app.conf.enable_utc = False
app.conf.update(timezone='Europe/Warsaw')
# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

app.conf.beat_schedule = {

    'add-every-day-morning': {
        'task': 'calendar_app.tasks.add',
        'schedule': crontab(hour=00, minute=00, day_of_week='mon,tue,wed,thu,fri'),
    },
}


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
