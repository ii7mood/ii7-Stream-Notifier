import configparser
import requests

"""
In this script there is a chance we need to re-generate the access_token in which case we will need to re-read the config file
That is why I haven't used common.py
"""

config = configparser.ConfigParser() 
config_path = "config/config.ini"

def oAuthreinit() -> None:
    config.read(config_path)
    OAuth = config['TWITCH']
    newAuthBearer = requests.post(f"https://id.twitch.tv/oauth2/token?client_id={OAuth['client_id']}&client_secret={OAuth['client_secret']}&grant_type=client_credentials").json();

    try:
        OAuth['access_token'] = newAuthBearer['access_token']
    except KeyError:
        if newAuthBearer['status'] == 400:
            print("Twitch oauth details incorrectly entered.")
            exit(1)

    
    with open(config_path, 'w') as configfile:
        config.write(configfile)



def getProfile(name):
    config.read(config_path)
    OAuth = config['TWITCH']

    headers = {
        'Client-ID': OAuth['client_id'],
        'Authorization': 'Bearer ' + OAuth['access_token']}


    profile_json = requests.get(f'https://api.twitch.tv/helix/users?login={name}', headers=headers)

    if profile_json.status_code == 401: # Twitch tokens expire after some time, in which case we can re-generate one.
        oAuthreinit()
        getProfile(name)

    profile = profile_json.json();
    return profile


def getStream(name):
    config.read(config_path)
    OAuth = config['TWITCH']

    headers = {
        'Client-ID': OAuth['client_id'],
        'Authorization': 'Bearer ' + OAuth['access_token']}

    stream_json = requests.get(f'https://api.twitch.tv/helix/streams?user_login={name}', headers=headers)

    if stream_json.status_code == 401: # Twitch tokens expire after some time, in which case we can re-generate one.
        oAuthreinit()
        getStream(name)

    stream = stream_json.json();
    return stream 