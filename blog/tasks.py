from __future__ import absolute_import, unicode_literals

from celery import Celery, shared_task
from celery.schedules import crontab

app = Celery()


@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week='mon-fri'),
        test.s('Happy Mondays!'),
    )


@app.task
def test(arg):
    print(arg)


@app.task
def add(x, y):
    z = x + y
    print(z)
