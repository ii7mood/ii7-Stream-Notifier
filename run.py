import subprocess
from time import sleep
import common

config = common.config
python = config['GENERAL']['python_exec']

# Define the scripts you want to execute
script_paths = ['Discord BOT/app.py', 'Discord BOT/BOT_commands.py', 'Pushover/app.py', 'Detector.py']

# Execute each script
for script_path in script_paths:
    subprocess.Popen([python, script_path], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sleep(3)

# Keep the program running until CTRL + C or something
while True:
    pass
