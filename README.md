This repository stores the source code to the discord music bot.

## Usage
Install the necessary system dependencies:
```
sudo apt-get install python3-venv python3-pip
```

Then create a python virtual environment using the command (eg. Python 3.12) 
```
python3.12 -m venv <your_env_name>
```

Next, activate the virtual environment you created using 
```
source <your_env_name>/bin/activate
```

Then install the necessary dependencies with 
```
pip install -r requirements.txt
```

Create a .env file using the command `touch .env` and insert your discord_token as follows:

```
DISCORD_TOKEN = <INSERT_YOUR_DISCORD_TOKEN>
```

Now you can start the bot locally with the command
```
python3.12 main.py
```
