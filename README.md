# slack-confirm-bot
A slack bot that forces mentions to confirm they have read a message.


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

