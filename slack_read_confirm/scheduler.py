"""APScheduler jobs"""

import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from models import ReadReceipt, SessionLocal, Target
from slack_bolt import App

app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
scheduler = BackgroundScheduler()

def schedule_user_reminder(announcement_id: int, target_id: int, user_id: str):
    job_id = f"reminder_{announcement_id}_{target_id}"
    trigger = CronTrigger(hour=9, minute=0)
    scheduler.add_job(send_reminder, trigger, args=[announcement_id, target_id, user_id], id=job_id, replace_existing=True)

def send_reminder(announcement_id: int, target_id: int, user_id: str):
    db = SessionLocal()
    existing = db.query(ReadReceipt).filter_by(target_id=target_id).first()
    if not existing:
        text = f"Reminder: please confirm you’ve read announcement `{announcement_id}`."
        app.client.chat_postMessage(channel=user_id, text=text)
    db.close()