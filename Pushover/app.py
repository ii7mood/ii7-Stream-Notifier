import socket
import pickle
import requests
from datetime import datetime
from pushover_wrapper import *
from os import getcwd
from sys import path

parent_path = getcwd().replace('/Discord BOT', '')
path.append(parent_path)

from common import log_wp, config

log_wp.name = __file__


HOST = config['PUSHOVER']['host']
PORT = config['PUSHOVER']['port']

serverSocket = (HOST, int(PORT))
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(serverSocket)
server.listen(1)

log_wp.info(f"PUSHOVER listening on {HOST}:{PORT}")
conn, addr = server.accept()

while True:
    try:
        packets = []
        while True:
            packet = conn.recv(4096)
            if not packet or packet[-3:] == b"END" : 
                packets.append(packet[:-3])
                break
            packets.append(packet)
        info_dict = pickle.loads(b"".join(packets))

        if info_dict['live_status'] == "is_live":
            avatar = requests.get(info_dict['avatar_url']).content
            message = f"{info_dict['uploader']} has started a stream!\n{info_dict['fulltitle']}"
            send_notification(
                message=message,
                url=info_dict['original_url'],
                url_title="View Stream!",
                title="Stream Started!", 
                image_data=avatar,
                priority=1
            )
            log_wp.info(f"Stream started notification sent via Pushover for {info_dict['uploader']}\n")
        
        elif info_dict['live_status'] == 'is_upcoming':
            avatar = requests.get(info_dict['avatar_url']).content
            message = f"{info_dict['uploader']} has scheduled a stream to start in {int((info_dict['release_timestamp'] - datetime.timestamp(datetime.now())) / 3600)} hours!"
            send_notification(
                message=message,
                url=info_dict['original_url'],
                url_title='View Stream!',
                title="Scheduled Stream!",
                image_data=avatar,
                priority=0
            )
            log_wp.info(f"Stream scheduled notification sent via Pushover for {info_dict['uploader']}\n")
        
        conn.send(b"DONE")

    except socket.error as e:
        log_wp.warning(f"Socket error occurred: {e}")
        continue

    except EOFError:
        log_wp.warning("PUSHOVER did not receive any data as connection shutdown unexpectedly")
        conn.close()
        conn, addr = server.accept()

        continue

