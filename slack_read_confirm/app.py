import os
import re
from datetime import datetime

from dotenv import load_dotenv
from models import Announcement, Base, ReadReceipt, SessionLocal, Target, engine
from scheduler import schedule_user_reminder, scheduler
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# Load environment variables
load_dotenv()

# Initialize Slack Bolt app
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))
# Create DB tables
Base.metadata.create_all(bind=engine)

# Patterns for user and user-group mentions
MENTION_REGEX = re.compile(r"<@([UW][A-Z0-9]+)>")
GROUP_REGEX = re.compile(r"<!subteam\^([GS][A-Z0-9]+)\|[^>]+>")

@app.command("/read-confirm")
def handle_read_confirm_command(ack, body, client, logger):
    ack()
    owner_id = body["user_id"]
    channel_id = body["channel_id"]
    text = body.get("text", "").strip()

    # Extract user IDs and expand groups
    user_ids = MENTION_REGEX.findall(text)
    group_ids = GROUP_REGEX.findall(text)
    for gid in group_ids:
        try:
            resp = client.usergroups_users_list(usergroup=gid)
            if resp.get("ok"):
                user_ids.extend(resp.get("users", []))
        except Exception as e:
            logger.error(f"Usergroup fetch error {gid}: {e}")

    targets = list({uid for uid in user_ids if uid != owner_id})
    if not targets:
        client.chat_postEphemeral(channel=channel_id, user=owner_id, text="Mention at least one user or group.")
        return

    # Clean text
    clean_text = MENTION_REGEX.sub("", text)
    clean_text = GROUP_REGEX.sub("", clean_text).strip()
    if not clean_text:
        client.chat_postEphemeral(channel=channel_id, user=owner_id, text="Provide announcement text after mentions.")
        return

    # Post announcement
    post = client.chat_postMessage(channel=channel_id, text=clean_text)
    message_ts = post["ts"]

    # Save announcement
    db = SessionLocal()
    ann = Announcement(owner_id=owner_id, channel_id=channel_id,
                       message_ts=message_ts, text=clean_text)
    db.add(ann)
    db.commit()
    db.refresh(ann)

    # Create targets & schedule
    for uid in targets:
        tgt = Target(announcement_id=ann.id, user_id=uid)
        db.add(tgt)
        db.commit()
        db.refresh(tgt)
        schedule_user_reminder(ann.id, tgt.id, uid)

    db.close()
    client.chat_postEphemeral(channel=channel_id, user=owner_id, text=(f"Announcement created. Targets: {', '.join(f'<@{u}>' for u in targets)}"))

@app.event("reaction_added")
def handle_reaction_added(event, client, logger):
    reaction = event.get("reaction")
    if reaction in ["white_check_mark", "heavy_check_mark"]:
        user_id = event["user"]
        item = event["item"]
        channel_id = item["channel"]
        message_ts = item["ts"]

        db = SessionLocal()
        # Locate announcement & target
        ann = db.query(Announcement).filter_by(
            channel_id=channel_id,
            message_ts=message_ts
        ).first()
        if ann:
            tgt = db.query(Target).filter_by(
                announcement_id=ann.id,
                user_id=user_id
            ).first()
            if tgt:
                # Record receipt if not exists
                if not db.query(ReadReceipt).filter_by(target_id=tgt.id).first():
                    receipt = ReadReceipt(target_id=tgt.id, timestamp=datetime.utcnow())
                    db.add(receipt)
                    db.commit()
                # Cancel scheduled job
                job_id = f"reminder_{ann.id}_{tgt.id}"
                try:
                    scheduler.remove_job(job_id)
                except Exception as e:
                    logger.error(f"Job removal error {job_id}: {e}")
                # If everyone read, post celebration
                total = db.query(Target).filter_by(announcement_id=ann.id).count()
                read_cnt = db.query(ReadReceipt).join(Target).filter(Target.announcement_id==ann.id).count()
                if read_cnt == total:
                    client.chat_postMessage(
                        channel=channel_id,
                        text=":tada: Everyone has read this announcement!",
                        thread_ts=message_ts
                    )
        db.close()

# Mention handler
@app.event("app_mention")
def handle_app_mention(event, say, client, logger):
    user = event.get("user")
    text = event.get("text")
    channel_id = event.get("channel")
    
    # Check if the mention includes "read-confirm" command
    if "read-confirm" in text.lower():
        # Extract message text (everything after "read-confirm")
        parts = text.lower().split("read-confirm", 1)
        if len(parts) > 1:
            message_text = parts[1].strip()
            if message_text:
                # Post the announcement
                post = client.chat_postMessage(channel=channel_id, text=message_text)
                message_ts = post["ts"]
                
                # Save announcement with the mentioning user as owner
                db = SessionLocal()
                ann = Announcement(owner_id=user, channel_id=channel_id,
                                message_ts=message_ts, text=message_text)
                db.add(ann)
                db.commit()
                db.refresh(ann)
                db.close()
                
                say(f"<@{user}>, I've created your read-confirm announcement. Users can confirm by adding a ✅ reaction.")
                return
        
        # If we get here, the command wasn't properly formatted
        say(f"<@{user}>, to create a read-confirm announcement, mention me with 'read-confirm' followed by your message.")
    else:
        # Default response for other mentions
        say(f"Hey <@{user}>! Use me to create read-confirm announcements. Just mention me with 'read-confirm' followed by your message.")

# Start the scheduler
scheduler.start()

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    handler.start()
