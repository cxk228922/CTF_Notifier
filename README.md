# CTF Time Discord Notifier

A lightweight Python script that periodically fetches upcoming CTF events from CTFtime.org and sends notifications to a Discord channel via webhook.

## Features

- Checks for new CTF events in the next **5 days** (configurable).  
- Formats event details (start/end time, duration, weight, etc.) into a Discord embed.  
- Prevents duplicate notifications by keeping track of already sent events.  
- Handles Discord rate limits (HTTP 429) by retrying after the suggested delay.  
- Simple logging to console for status and errors.

## Prerequisites

- Python 3.7 or higher  
- The following Python packages:
  - `requests`
  - `pytz`

You can install them via:

```bash
pip install requests pytz
```

## Configuration

- **WEBHOOK_URL** – Your Discord webhook URL.
- **CHECK_INTERVAL** – Time (in seconds) between checks (default: 3600).
- **DAYS_TO_LOOK_AHEAD** – How many days ahead to query events (default: 5).

## Usage

1. Clone this repository or copy `script.py` into your project.
2. Ensure `script.py` is executable:
   ```bash
   chmod +x script.py
   ```
3. Run the notifier:
   ```bash
   ./script.py
   ```
   or
   ```bash
   python3 script.py
   ```

## Project Structure

```
├── script.py          # Main notifier script
├── sent_events.json   # Generated; keeps track of sent event IDs
└── README.md          # This file
```

## License

This project is released under the MIT License.