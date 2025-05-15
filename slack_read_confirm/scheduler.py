"""APScheduler jobs"""

import os

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from slack_bolt import App

from .models import Announcement, ReadReceipt, SessionLocal, Target

# Initialize scheduler
scheduler = BackgroundScheduler()

# Lazy-loaded Slack app
_app = None

def get_app():
    """Get or initialize the Slack app"""
    global _app
    if _app is None:
        token = os.environ.get("SLACK_BOT_TOKEN")
        if token:
            _app = App(token=token)
        else:
            # For testing purposes
            from unittest.mock import MagicMock
            _app = MagicMock()
    return _app

def schedule_user_reminder(announcement_id: int, target_id: int, user_id: str):
    job_id = f"reminder_{announcement_id}_{target_id}"
    trigger = CronTrigger(hour=9, minute=0)
    scheduler.add_job(send_reminder, trigger, args=[announcement_id, target_id, user_id], id=job_id, replace_existing=True)

def send_reminder(announcement_id: int, target_id: int, user_id: str):
    db = SessionLocal()
    existing = db.query(ReadReceipt).filter_by(target_id=target_id).first()
    if not existing:
        # Get the announcement details to provide context in the reminder
        target = db.query(Target).filter_by(id=target_id).first()
        announcement = db.query(Announcement).filter_by(id=announcement_id).first()
        
        if announcement:
            channel_link = f"<#{announcement.channel_id}>"
            text = (f"Reminder: Please confirm you've read the announcement in {channel_link}.\n"
                   f"Message: '{announcement.text}'\n"
                   f"Please add a ✅ reaction to the original message to confirm you've read it.")
            get_app().client.chat_postMessage(channel=user_id, text=text)
    db.close()
