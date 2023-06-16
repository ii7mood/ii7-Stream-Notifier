import socket
from time import sleep
import pickle
from enum import Enum
from Streamers import *
from common import log_wp, config

log_wp.name = __file__


class ServerType(Enum):
    DISCORD = 'DISCORD'
    PUSHOVER = 'PUSHOVER'

def establish_connection(server_type):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server.connect((config[server_type.value]['host'], int(config[server_type.value]['port'])))
        log_wp.info(f"Connection to {server_type.value} socket established.")
        return server

    except ConnectionRefusedError:
        log_wp.warning(f"Failed to establish a connection to {server_type.value} socket. Connection Refused.")
        return None, None

def initialize_servers():
    servers = {}

    for server_type in ServerType:
        server = establish_connection(server_type)
        if server:
            servers[server_type] = server

    return servers


def send_data(data : dict, servers : dict) -> None:
    """
    Checks if the server is accepting data before attempting to write to it.
    Then waits for a reply confirming that the client is done processing the data.
    Then awaits a reply from the server to confirm that it is done processing the data.
    """

    for server in servers.items():
        server_type = server[0]
        connection = server[1]

        try:
            connection.sendall(pickle.dumps(data) + b"END")

            reply = connection.recv(1024)

            if reply == b"DONE":
                log_wp.info("Server confirmed that the data has been received and processed.")

            else:
                log_wp.warning("Unexpected response from server, not sure what happened here. Attempting to re-establish a connection.")
                connection.close()
                server = establish_connection(server_type)

                if server:
                    servers[server_type] = server

                else:
                    log_wp.warning("Failed to re-establish the connection. Did the sever close?")

        except ConnectionAbortedError:
            log_wp.warning(f"Failed to send data to {server_type}. Connection Aborted.")

        except socket.error:
            log_wp.warning(f"Failed to send data to {server_type}. Socket Error.")


def process_streamers_data(streamers_data : list, servers : dict) -> None:
    for info_dict in streamers_data:
        change_in_activity = info_dict['live_status'] != info_dict['recorded_live_status']

        if change_in_activity:
            log_wp.info(f'Change in activity with {info_dict["name"]} | ' 
                        f'Before: {info_dict["recorded_live_status"]} | '
                        f'After: {info_dict["live_status"]} | ')

            sleep(1) # Sometimes Detector.py sends data before listener can process it.

            if info_dict['live_status'] != "not_live": # Only send notification is the stream is a scheduled one or a live one.
                send_data(info_dict, servers)
            update_streamer(info_dict['uploader_url'], info_dict['live_status'])

def main_loop():
    iteration = 0
    while True:
        streamers_data = get_all_streamers_data()
        iteration += 1

        process_streamers_data(streamers_data, servers)

        log_wp.info("Sleeping for 5 minutes. \n")
        sleep(300)

# Server Initialization
servers = initialize_servers()

# Main Loop
main_loop()
