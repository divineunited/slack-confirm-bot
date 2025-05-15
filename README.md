# slack-confirm-bot
A Slack bot that forces mentions to confirm they have read a message.

## Features
- Create announcements with read confirmations via slash command or mentions
- Track who has read announcements through reactions
- Send automatic reminders to users who haven't confirmed reading
- Notify when all users have read an announcement

## Developer Setup
Set up your local pyenv: 

```
make setup
```

Create a `.env` file and add:
```
SLACK_BOT_TOKEN=xoxb-your-token                                                                          
SLACK_APP_TOKEN=xapp-your-token                                                                          
                                                                                                         
DATABASE_URL=postgresql://localhost:5432/slack_read_confirm
```

Make sure your DB is running:
```
pg_isready -h localhost -p 5432
```

Run DB Migrations:
```
python -m slack_read_confirm.db_migrate
```

Run tests:

Manual tests:
```
python -m slack_read_confirm.db_test
```

Creating sample data for manual testing:
```
python -m slack_read_confirm.manual_test
```

Unit Tests:
```
python -m pytest slack_read_confirm/test_app.py -v
```

## Slack Integration Setup

### 1. Create a Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and click "Create New App"
2. Choose "From scratch" and provide a name (e.g., "Read Confirm Bot") and select your workspace
3. Click "Create App"

### 2. Configure Bot Permissions

1. In the left sidebar, click on "OAuth & Permissions"
2. Scroll down to "Scopes" and add the following Bot Token Scopes:
   - `chat:write` (Send messages as the app)
   - `reactions:read` (View emoji reactions)
   - `usergroups:read` (View user groups)
   - `app_mentions:read` (Receive mention events)
   - `commands` (Add slash commands)
3. Scroll up and click "Install to Workspace" to authorize the app

### 3. Enable Socket Mode

1. In the left sidebar, click on "Socket Mode"
2. Toggle "Enable Socket Mode" to On
3. Give your app-level token a name (e.g., "Read Confirm Socket")
4. Click "Generate" to create the token
5. Copy the `xapp-` token to your `.env` file as `SLACK_APP_TOKEN`

### 4. Configure Event Subscriptions

1. In the left sidebar, click on "Event Subscriptions"
2. Toggle "Enable Events" to On
3. Under "Subscribe to bot events", add:
   - `app_mention` (When the bot is mentioned)
   - `reaction_added` (When a reaction is added to a message)
4. Click "Save Changes"

### 5. Create Slash Command

1. In the left sidebar, click on "Slash Commands"
2. Click "Create New Command"
3. Fill in the details:
   - Command: `/read-confirm`
   - Short Description: "Create an announcement with read confirmations"
   - Usage Hint: "@user1 @user2 Your announcement text"
4. Click "Save"

### 6. Update Bot Token

1. In the left sidebar, click on "OAuth & Permissions"
2. Copy the "Bot User OAuth Token" (`xoxb-` token)
3. Paste it in your `.env` file as `SLACK_BOT_TOKEN`

## Running the Bot

Start the bot with:

```
python -m slack_read_confirm.app
```

## Testing End-to-End with Slack

### 1. Verify Bot is Online

After starting the bot, check your Slack workspace. The bot should appear as online.

### 2. Test Slash Command

In any channel where the bot is present, try:
```
/read-confirm @username This is a test announcement
```

The bot should:
1. Post the message "This is a test announcement"
2. Send you a confirmation that the announcement was created
3. Create entries in your database

### 3. Test Mention Command

In any channel where the bot is present, try:
```
@read-confirm-bot read-confirm This is another test announcement
```

The bot should:
1. Post the message "This is another test announcement"
2. Send a confirmation message
3. Create entries in your database

### 4. Test Read Confirmation

1. Add a ✅ reaction to one of the test announcements
2. Check your database to verify a read receipt was created:
   ```
   psql postgresql://localhost:5432/slack_read_confirm
   SELECT * FROM read_receipts;
   ```

### 5. Verify Database Records

After testing, check your database to see all created records:

```
psql postgresql://localhost:5432/slack_read_confirm

-- View all announcements
SELECT * FROM announcements;

-- View all targets
SELECT * FROM targets;

-- View all read receipts
SELECT * FROM read_receipts;

-- View read status for a specific announcement
SELECT a.text, t.user_id, 
  CASE WHEN r.id IS NULL THEN 'Not Read' ELSE 'Read' END as status
FROM announcements a
JOIN targets t ON a.id = t.announcement_id
LEFT JOIN read_receipts r ON t.id = r.target_id
WHERE a.id = 1;  -- Replace with your announcement ID
```

## Troubleshooting

### Bot Not Responding
- Check that both `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` are correctly set in your `.env` file
- Verify the bot is running without errors
- Ensure all required scopes are added to your Slack app

### Database Issues
- Run `python -m slack_read_confirm.db_test` to verify database connectivity
- Check PostgreSQL is running with `pg_isready -h localhost -p 5432`
- Ensure the database exists with `psql -l | grep slack_read_confirm`

### Event Handling Issues
- Make sure Socket Mode is enabled in your Slack app
- Verify you've subscribed to the required bot events
- Check the console output for any error messages
