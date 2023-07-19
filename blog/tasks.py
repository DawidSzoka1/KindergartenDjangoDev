from celery.schedules import crontab
from celery.task import periodic_task


@periodic_task(run_every=crontab(minute=0, hour=8))
def every_monday_morning():
    print("This is run every teks on 8am")
