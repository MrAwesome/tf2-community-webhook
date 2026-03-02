# TF2 Community Server Webhook

Periodically fetches TF2 server data from the Steam API (filtered by `gleesus` gametype) and updates a single Discord message via webhook with a formatted server list.

## Setup

1. **Steam API key** should already exist at `~/.steam_api_key`.

2. **Create a Discord webhook** in your server's channel settings (Edit Channel > Integrations > Webhooks), then save the URL:

   ```
   echo 'https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN' > .webhook_url
   ```

3. **First run** — creates the Discord message and saves its ID to `.message_id`:

   ```
   python3 update.py
   ```

   All subsequent runs will edit that same message in place.

4. **Install the systemd timer** (runs every 5 minutes):

   ```
   bash install.sh
   ```

## Manual usage

```
python3 update.py          # create or update the message
systemctl --user status tf2-server-list.timer   # check timer
systemctl --user stop tf2-server-list.timer     # stop
journalctl --user -u tf2-server-list.service    # view logs
```

## Resetting the message

Delete `.message_id` and run `python3 update.py` again to post a fresh message.
