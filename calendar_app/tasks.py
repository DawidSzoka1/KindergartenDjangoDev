from __future__ import absolute_import, unicode_literals
from children.models import PresenceModel, Kid
from django.utils import timezone
from celery import Celery, shared_task
from celery.schedules import crontab
from MarchewkaDjango.celery import app


@shared_task(blind=True)
def add():
    kids = Kid.objects.filter(is_active=True)
    for kid in kids:
        test = PresenceModel.objects.filter(kid=kid).filter(day=timezone.now()).first()
        if test:
            pass
        else:
            PresenceModel.objects.create(kid=kid, day=timezone.now(), presenceType=1)
    return "Done"
