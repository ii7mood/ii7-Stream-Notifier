import pickle
import socket
import asyncio
import functools
import typing
import discord
from datetime import datetime
from os import getcwd
from sys import path
from copy import deepcopy

parent_path = getcwd().replace('/Discord BOT', '')
path.append(parent_path)

from common import log_wp, config

log_wp.name = __file__


TOKEN = config['DISCORD']['token']
HOST = config['DISCORD']['host']
PORT = config['DISCORD']['port']
CHANNEL_ID = config['DISCORD']['channel_id']

serverSocket = (HOST, int(PORT))
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(serverSocket)
server.listen(1)

intents = discord.Intents.all()
client = discord.Client(intents=intents)


def simplify_string(string : str) -> str:
    """
    So, I follow a lot of creators who like to use symbols in their titles. This ends up making the title too long and unnecessary.
    So with this function I will only keep ascii characters thereby removing these symbols. Now if after removing all unicode characters the string becomes empty then
    I will not go on with the change and just instead return the old string (this is for languages such as JP or AR) otherwise if after removing the unicode characters
    ASCII characters still exist then we will just go on with that. ****** NOTE THIS IS ONLY FOR SCHEDULED STREAMS, ON YT.
    """

    string_copy = deepcopy(string)
    string_copy = string_copy.encode('ascii', 'ignore').decode()

    if string_copy == "": # If after removing all unicode characters the string is empty then just return the string unmodified.
        return string
    
    else:
        return string_copy.replace('/', ' ') # Otherwise return the string with the unicode characters removed, and for some reason when decoding '/' takes the place of spaces so let's fix that


def embed_notification(info_dict : dict) -> discord.Embed:
    """
    In live notifications, for twitch we should get the embedded image to be the avatar, while in YT we should get the thumbnail, and simplify name.
    In scheduled notifications, youtube should have the both the name and title simplified but everything else is the same between Twitch and YT.
    I had to re-write this entire app.py multiple times I do not fucking care that it is spaghetti code I just wanna be done with it.
    """

    if info_dict['live_status'] == "is_live":

        if info_dict['platform'] == "youtube":

            image_url = info_dict['thumbnail']
            name = simplify_string(info_dict['uploader'])
        else:

            image_url = info_dict['avatar_url']
            name = info_dict['webpage_url_basename'] # for some reason uploader is not always available for twitch streams I'll look into it when I feel like it

        viewer_count = info_dict['concurrent_view_count']
        stream_url = info_dict['original_url']
        title = info_dict['fulltitle']


        embed_notif = discord.Embed(title=f'{name} is live!', color=0x00ff00)
        embed_notif.set_image(url=image_url)
        embed_notif.add_field(name=f"**__{title}__** for {viewer_count} viewers!", value=f"[Visit this stream!]({stream_url})")
        embed_notif.timestamp = datetime.utcnow()
    

    else: # If scheduled notification
        
        name = simplify_string(info_dict['uploader'])
        title = simplify_string(info_dict['fulltitle'])
        stream_url = info_dict['original_url']
        image_url = info_dict['avatar_url']
        hours_left = round(((info_dict['release_timestamp'] - datetime.timestamp(datetime.now())) / 3600), 1)

        embed_notif = discord.Embed(title=f'{name} has scheduled a stream!', color=0xff0000)
        embed_notif.set_image(url=image_url)
        embed_notif.add_field(name=f"**__{title}__** scheduled to start in {hours_left} hours!", value=f"[Visit this stream!]({stream_url})")
        embed_notif.timestamp = datetime.utcnow()

    return embed_notif


'''
With Discord, we'll constantly be re-connecting and disconnecting from the Socket.
Basically, we are trying to listen to two sockets at once: Discord's and the Detector.py client.
That is kind of difficult to do, especially as a "programmer," so instead, we'll use this to_thread function
I found on Stack Overflow. It basically offloads blocking functions to a separate thread. This utilizes asyncio.to_thread, which
is only available in Python >= 3.9.
'''



def to_thread(func: typing.Callable) -> typing.Coroutine:
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper


@to_thread
def start_listening(conn : socket.socket.accept = None):
    """
    Alright so the way this will work is that on the first iteration a new connection will be accepted into a variable called conn.
    The program will receive it's data, process it while passing this conn object around. Then on the second iteration after the first
    Notifcation has been sent we call start_listening again except this time giving this conn as an argument. This will make sure to continue using
    The same connection, not making a new one. Why don't I just place the server.accept() outside the  function? accept() is a blocking method
    of the socket.socket.connect object so by running it outside we prevent all the other functions from being executed.
    """
    log_wp.info(f"DISCORD currently listening on {HOST}:{PORT}")
    if conn == None:
        conn, addr = server.accept()
    try:
        packets = []
        while True:
            packet = conn.recv(4096)
            if not packet or packet[-3:] == b"END":
                packets.append(packet[:-3])
                break
            packets.append(packet)
        data = pickle.loads(b"".join(packets))

    except socket.error as e:
        log_wp.warning(e)
        return None, None # Should create a new connection as None is returned in place of current broken connection

    except EOFError:
        log_wp.warning("DISCORD did not receive any data as the connection shut down unexpectedly")
        return None, None

    return data, conn



@client.event
async def on_ready():
    channel = await client.fetch_channel(CHANNEL_ID)
    conn = None
    while True:
        info_dict, conn = await start_listening(conn)

        if info_dict == None and conn == None: # An error occured with the connection itself
            continue

        elif info_dict == None: # An error occured with the data received. Does not prevent the program from panic exiting
            conn.sendall(b"DONE")
            continue

        embed_notifi = embed_notification(info_dict)
        await channel.send(embed=embed_notifi)
        log_wp.info(f"Stream notification sent via Discord for {info_dict['uploader']}\n")


        # Wait for acknowledgement from the server
        conn.sendall(b"DONE")

client.run(TOKEN)
