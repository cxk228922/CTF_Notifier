#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone

import requests
import pytz

WEBHOOK_URL = "" # Fill in your Discord Webhook URL
CHECK_INTERVAL = 3600  # Check interval (sec)
DAYS_TO_LOOK_AHEAD = 5  # Check for the next few days
CTF_TIME_API = "https://ctftime.org/api/v1/events/"

# CTFtime User-agent
HEADERS = {"User-Agent": "CTF-Discord-Notifier/1.0"}

# logging settings
logging.basicConfig(
    level=logging.INFO,  # Set logging level to INFO
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # Define log message format
    handlers=[logging.StreamHandler()]  # Output logs to console
)
# Create a logger instance for this application
logger = logging.getLogger('ctf_notifier')

# To save sent events
DATA_FILE = "sent_events.json"

# Load sent events
def load_sent_events():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error("Data file format error, creating new file")
            save_sent_events([])
    return []


# Save sent events
def save_sent_events(events):
    with open(DATA_FILE, 'w') as f:
        json.dump(events, f)


# Get upcoming CTFs
def get_upcoming_ctfs():
    now = datetime.now(timezone.utc)
    # Set the start and end times for the query
    start = int(now.timestamp())
    end = int((now + timedelta(days=DAYS_TO_LOOK_AHEAD)).timestamp())

    params = {
        'limit': 100,
        'start': start,
        'finish': end
    }

    try:
        response = requests.get(CTF_TIME_API, headers=HEADERS, params=params)
        response.raise_for_status() 
        events = response.json()
        return events
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to get CTF events: {e}")
        return []

# Format Discord Embed
def format_discord_embed(event):
    taipei_tz = pytz.timezone('Asia/Taipei')

    # Process start and end times, convert to Taipei time
    start_dt = datetime.strptime(event['start'], "%Y-%m-%dT%H:%M:%S%z")
    finish_dt = datetime.strptime(event['finish'], "%Y-%m-%dT%H:%M:%S%z")

    # Convert to Taipei time
    start_dt_taipei = start_dt.astimezone(taipei_tz)
    finish_dt_taipei = finish_dt.astimezone(taipei_tz)

    # Format display
    start_time = start_dt_taipei.strftime("%Y-%m-%d %H:%M") + " (GMT+8 Taipei Time)"
    finish_time = finish_dt_taipei.strftime("%Y-%m-%d %H:%M") + " (GMT+8 Taipei Time)"

    # Calculate the duration of the competition
    duration = finish_dt - start_dt
    days = duration.days
    hours = duration.seconds // 3600
    if days > 0:
        duration_str = f"{days} days {hours} hours"
    else:
        duration_str = f"{hours} hours"

    # Get the weight of the competition
    weight = event.get('weight')

    embed = {
        "title": event['title'],
        "url": event['url'],
        "color": 5814783, 
        "description": event.get('description', 'No description') if event.get('description') else 'No description',
        "fields": [
            {
                "name": "Start Time",
                "value": start_time,
                "inline": True
            },
            {
                "name": "End Time",
                "value": finish_time,
                "inline": True
            },
            {
                "name": "Duration",
                "value": duration_str,
                "inline": True
            },
            {
                "name": "Weight",
                "value": f"{weight:.2f}" if weight is not None else "Unknown",
                "inline": True
            },
            {
                "name": "Official Website",
                "value": f"[Click to visit]({event.get('ctf_url', event['url'])})" if event.get(
                    'ctf_url') else f"[CTFtime page]({event['url']})",
                "inline": True
            },
            {
                "name": "Format",
                "value": event.get('format', 'Unknown'),
                "inline": True
            }
        ],
        "footer": {
            "text": "CTF Time Auto Notification | Data source: CTFtime.org"
        },
        "timestamp": datetime.now().isoformat()
    }

    # If there is a logo, add it to the embed
    if event.get('logo'):
        embed["thumbnail"] = {"url": event['logo']}

    return embed


def send_to_discord(events):
    sent_events = load_sent_events()
    new_events_sent = False

    for event in events:
        event_id = str(event['id'])

        # Check if it has already been sent
        if event_id in sent_events:
            continue
        
        if(WEBHOOK_URL == ""):
            logger.error("No Discord Webhook URL provided")
            return
        
        embed = format_discord_embed(event)
        payload = {
            "content": f"**New CTF Event Notification** \n{event['title']} will start at {embed['fields'][0]['value']}",
            "embeds": [embed]
        }

        try:
            response = requests.post(WEBHOOK_URL, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully sent event notification: {event['title']}")
            sent_events.append(event_id)
            new_events_sent = True
            # Avoid Discord rate limit
            time.sleep(1)
        except requests.exceptions.HTTPError as http_err:
            if http_err.response is not None and http_err.response.status_code == 429:
                retry_after = int(http_err.response.headers.get('Retry-After', 1))
                logger.warning(f"Rate limited, retrying after {retry_after} seconds")
                time.sleep(retry_after)
                continue
            else:
                logger.error(f"Failed to send to Discord: {http_err}")
        except Exception as e:
            logger.error(f"Failed to send to Discord: {e}")

    if new_events_sent:
        save_sent_events(sent_events)
        logger.info("Updated sent events list")


def main():
    logger.info("Starting CTF Time Discord Notifier...")

    while True:
        logger.info("Checking for new CTFs...")
        events = get_upcoming_ctfs()
        if events:
            send_to_discord(events)
        else:
            logger.info("No new CTFs found")

        logger.info(f"Waiting {CHECK_INTERVAL} seconds before checking again...")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Program stopped manually")
    except Exception as e:
        logger.error(f"Program encountered an error: {e}")