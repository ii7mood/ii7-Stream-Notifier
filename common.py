import configparser
import logging

config = configparser.ConfigParser()
config.read('config/config.ini')

# Create a logger with a placeholder name
log_wp = logging.getLogger('common')
fhdlr = logging.FileHandler("files/logs.log")
log_wp.addHandler(fhdlr)
fhdlr.setFormatter(logging.Formatter('# %(asctime)s | %(name)s | %(levelname)s - %(message)s'))
log_wp.setLevel(logging.INFO)

