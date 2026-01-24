from apscheduler.schedulers.background import BackgroundScheduler
from django.utils import timezone
import datetime
import random
from .models import Episode
from .services.syoboi_calendar import auto_update_episodes


def update_episodes():
    auto_update_episodes()


def update_weekly_episodes():
    start_date = timezone.now().date()
    end_date = start_date + datetime.timedelta(days=7)
    auto_update_episodes(start_date=timezone.now().date(), end_date=end_date)


def start():
    scheduler = BackgroundScheduler()
    hour = random.randint(0, 4)
    minute = random.randint(1, 59)
    scheduler.add_job(update_episodes, "cron", hour=hour,
                      minute=minute, id="update_episodes")
    scheduler.add_job(update_weekly_episodes, "cron", day_of_week="mon",
                      hour=3, minute=minute, id="update_weekly_episodes")
    scheduler.start()
