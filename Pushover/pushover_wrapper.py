import requests
from os import getcwd
from sys import path


parent_path = getcwd().replace('/Discord BOT', '')
path.append(parent_path)

from common import log_wp, config

log_wp.name = __file__

token = config['PUSHOVER']['token']
user = config['PUSHOVER']['user']
contentType = {'Content-type' : 'multipart/form-data'}

def send_notification(message, url = None, url_title = None, image_data = None, priority=0, title=None):
    body = {
        'token' : token,
        'user' : user,
        'message' : message,
        'html' : 1,
        'priority' : priority
        }  
    
    if url != None:
        body['url'] = url

    if url_title != None:
        body['url_title'] = url_title  

    if title != None:
        body['title'] = title

    if image_data != None:
        response = requests.post("https://api.pushover.net/1/messages.json", data=body, files={'attachment' : ("image.png", image_data, "image/png")})
    
    else:
        response = requests.post("https://api.pushover.net/1/messages.json", data=body)

    if response.status_code == 200:
        print("Success!")
    else:
        send_notification(response.read())
