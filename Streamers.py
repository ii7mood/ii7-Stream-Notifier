import yt_dlp
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import TwitchC, sqlite3
from time import sleep

from common import log_wp, config

log_wp.name = __file__


db = sqlite3.connect('files/Streamers.db') # establish a connection to Streamers.db holding various data about each streamer
cursor = db.cursor()

default_twitch_icon = "https://imgur.com/gZYnkUt.png"
default_youtube_icon = "https://imgur.com/UZPLIyf.png"





def _fetch_twitch_information(streamer_url : str, stream_info = False) -> str:
    '''
    Attempts to extract Twitch avatar by either scraping or using Twitch API if credentials are provided.
    IF Twitch API is used we can also get concurrent viewer count for active streams.
    This is optional, and only happens if stream_info is set to True which _fetch_avatar_url does not set.
    Should NOT be used by itself, instead should be called by _fetch_avatar_url
    '''
    if config["TWITCH"]['scrape'] == "1":
        if stream_info == True: # If this function was called while scraping is true then twitch API shall not be used and instead concurrent viewer will be None. We will need to change message later.
            return None

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
        }

        try:
            response = requests.get(streamer_url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Method 1: Look for the <meta> tag with property="og:image"
                meta_avatar = soup.find('meta', property='og:image')
                if meta_avatar:
                    return meta_avatar['content']
                
                # Method 2: Look for the <img> tag with the class "tw-image-avatar"
                img_avatar = soup.find('img', class_='tw-image-avatar')
                if img_avatar:
                    return img_avatar['src']
                
                # Method 3: Look for the <figure> tag with the class "channel-header__avatar"
                figure_avatar = soup.find('figure', class_='channel-header__avatar')
                if figure_avatar:
                    img = figure_avatar.find('img')
                    if img:
                        return img['src']
                    else:
                        log_wp("soup.find returned None, Twitch.TV probably changed website structure. Using default Twitch icon.")
                        return default_twitch_icon

        except requests.RequestException as e:
            log_wp.warning(f"Failed to get avatar by scraping Twitch.tv, using default twitch icon. {e}")
            return default_twitch_icon

    else:
        try:
            streamer_name = streamer_url.replace('https://www.twitch.tv/', '')

            
            if stream_info:
                stream = TwitchC.getStream(streamer_name)
                return [stream['data'][0]['viewer_count'], stream['data'][0]['game_name']]

            
            else:
                profile = TwitchC.getProfile(streamer_name)
                return profile['data'][0]['profile_image_url']
    
        except Exception as e:
            log_wp.warning(f"Failed to get avatar/stream_info using Twitch API, using default twitch icon/unknown. {e}")
            
            if stream_info:
                return "an unknown number of"
            else:
                return default_twitch_icon





def _fetch_avatar_url(streamer_url : str, yt_dlp_args : dict):
    '''
    As the name suggests, this attempts to extract avatar url from the streamer's url. Uses _get_twitch_avatar().
    This should be called by get_streaming_data to pass yt_dlp_args. If you want to use it, you can just copy the yt_dlp_args variable from get_streaming_data
    '''
    if "youtube" in streamer_url:
        try:
            with yt_dlp.YoutubeDL(yt_dlp_args) as ytd:
                info_dict = ytd.extract_info(streamer_url.replace('/live', '')) # ytd returns thumbnails containing avatar when confronted with home page of a channel.
            return [x for x in info_dict['thumbnails'] if x['id'] == "avatar_uncropped"][0]['url']
        except Exception as e:
            log_wp.warning(f"*Something* happened. What is it? I have no idea but avatar_url will use default youtube icon. {e}")
            return default_youtube_icon
        
    elif "twitch" in streamer_url:
        return _fetch_twitch_information(streamer_url)





def _fetch_raw_streamers_data() -> list:
     """
     Get a list of all streamers urls and their recorded_activity within the database
     """
     cursor.execute("SELECT * FROM streamers")
     return cursor.fetchall()






def fetch_streamer(raw_streamer_data: list) -> dict:
    """
    This is the main function extracting all necessary information regarding a singular streamer.
    The raw_streamer_data is a list with two elements : URL and recorded_activity (within DB, example : 'is_live' or 'not_live' or 'is_upcoming')
    """
    # Get URL and live stream status from input list
    url = raw_streamer_data[0]
    recorded_activity = raw_streamer_data[1]

    log_wp.info(f"Currently working with {url}")

    # In youtube adding /live at the end of a channel's URL redirects us to a live-stream (if exists)
    if "youtube" in url:
        url = url + '/live'
        platform = "youtube"
    
    else:
        platform = "twitch"
    
    # Set up options for yt-dlp extractor
    yt_dlp_args = {
        'ignoreerrors': True, # Continue extracting info even if no playable stream is found
        'quiet': True, # Suppress non-error output
        'skip_download': True, # Don't download any media
        'playlist_items': '0', # Only look at first item in playlist (for efficiency)
        'ignore_no_formats_error' : True,
        'no_warnings' : True
    }

    # Use yt-dlp to extract video information from URL
    with yt_dlp.YoutubeDL(yt_dlp_args) as ytd:
        try:
            info_dict = ytd.extract_info(url)
        
        except yt_dlp.DownloadError as e:
            if 'Unable to recognize tab page' in e:
                fetch_streamer(raw_streamer_data) # Error on YouTube side, attempts to extract info again.
            else:
                info_dict = None

        if info_dict != None:
            log_wp.info(f"Stream found. Status: {info_dict['live_status']}")

            if info_dict['live_status'] != recorded_activity: # This will attempt to extract the avatar ONLY on the first detection where the notification will be sent.
                info_dict['avatar_url'] = _fetch_avatar_url(url, yt_dlp_args)  # Rather than extract the avatar every detection where notifications won't be sent and this is just useless.
                # This is important because _fetch_avatar_url takes a long time depending on whether it is scraping or not and whether Twitch servers are feeling good or not.
            
            if info_dict['live_status'] == "is_upcoming":
                if info_dict['release_timestamp'] == None: # When a Live stream gets close to being live YT no longer gives us a specific time to work with so release_timestamp will be a NoneType.
                    info_dict['release_timestamp'] = 'in_moments' # I know this is not a timestamp but it'll work i guess. Also this is a scheduled notification meaning we won't be notified twice if this has been scheduled for a while.
                    log_wp.info('no release_timestamp given despite an upcoming stream. Set to starting in a few moments.')

                elif (((info_dict['release_timestamp'] - datetime.timestamp(datetime.now())) / 3600) > 24): # Avoid scheduled streams that will start in over 24 hours
                    info_dict['live_status'] = 'not_live'
                    log_wp.info("Scheduled stream will start in over 24 hours so we will set it to not_live and ignore it.") # This does mean that avatar will be generated everytime though.
            
            if (platform == "twitch") and (info_dict['live_status'] == 'is_live'): # With YouTube viewer count is extracted automatically while Twitch not. So we will extract it manually using Twitch API. (if enabled)
                twitch_ext = _fetch_twitch_information(url, stream_info=True)
                info_dict['concurrent_view_count'] = twitch_ext[0]
                info_dict['category_name'] = twitch_ext[1]
        
        else: # Stream does not exist so just populate this with bare minimum data to save to DB.
            info_dict = {}
            info_dict['live_status'] = 'not_live'
            info_dict['uploader_url'] = url.replace('/live', '')
        
    # Add live status and previously recorded live stream status to video information
    info_dict['recorded_live_status'] = recorded_activity
    info_dict['platform'] = platform
    info_dict['name'] = raw_streamer_data[2]
    info_dict['uploader_url'] = url.replace('/live', '')

    return info_dict




def get_all_streamers_data() -> list:
    """
    Get a list of dictionaries of all streamers in the database
    """
    raw_streamers_data_list = _fetch_raw_streamers_data()
    data = []
    for streamer in raw_streamers_data_list:
        data.append(fetch_streamer(streamer))
        sleep(1) # Without it we get a connection refused somewhere along the fetch_streamer function so let's not do that.
    
    return data





def update_streamer(url : str, current_activity : str) -> None:
    """
    Update the recorded_activity field of a streamer when a change in activity is detected
    """
    cursor.execute(
        "UPDATE streamers SET RECORDED_ACTIVITY = :current_activity WHERE URL = :url",
        {'url': url.replace('/live', ''), 'current_activity': current_activity}
    )
    db.commit()
    log_wp.info("Streamer information updated within database")


x = fetch_streamer(['https://www.youtube.com/@rinpenrose', 'not_live', 'moist'])
print(x)