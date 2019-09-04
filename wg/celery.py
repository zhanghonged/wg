from celery import Celery, platforms
from celery.schedules import crontab
import os

project_name = os.path.split(os.path.abspath("."))[-1]
project_setting = "%s.settings" % project_name

os.environ.setdefault('DJANGO_SETTINGS_MODULE', project_setting)

app = Celery(project_name)
app.config_from_object('django.conf:settings')
app.autodiscover_tasks()

# 允许root用户运行celery
platforms.C_FORCE_ROOT = True

app.conf.update(
    CELERYBEAT_SCHEDULE = {
        'task-1': {
            'task':"api.tasks.checkUsedIp",
            'schedule':crontab(minute=1)
        }
    }
)