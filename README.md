This repository stores the source code to the discord music bot.

## 📂 Folder Structure

```
discord_musicBot/
├── cogs/                   # Modular components for commands and events
│   ├── general.py          # Commands for general activity
│   ├── lyrics.py           # Commands to fetch lyrics of a song 
│   └── music_player.py     # Commands to play music
├── logs/                   # Log files for bot activity
├── .env                    # API keys
├── docker-compose.yml      # Docker configuration
├── Dockerfile              # Dockerfile for building the bot image
├── logger.py               # Logger setup
├── macros.py               # Helper functions and macros
├── main.py                 # Main entry point for the bot
├── README.md               # Project overview and instructions
└── requirements.txt        # Dependencies for the project
```

---

## 🚀 Quickstart
(Optional) Create a python virtual environment using the command and activate it (eg. Python 3.12) 
```
python3.12 -m venv <your_env_name>
source <your_env_name>/bin/activate
```

1. Install the necessary system dependencies:
```bash
pip install -r requirements.txt
```

2. Add credentials to `.env`:
```env
DISCORD_TOKEN = <INSERT_YOUR_DISCORD_TOKEN>
```

3. Now you can start the bot locally with:
```bash
python main.py
```

---
## Alternative 
If you have docker installed, you can simply build the bot image and the bot will automatically run
```bash
docker-compose up -d 
```