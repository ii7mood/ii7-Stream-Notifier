# ii7-Stream-Notifier
## A YouTube / Twitch stream notifier. Works with Discord & Pushover! (Python >= 3.9)

A personal project I quickly cooked up as I - before this - used a deprecated version of Discord.py that was held together by two pieces of duct tape.
Now I know I am not an amazing programmer so if there any changes or ways to improve the code please do let me know. (I guess create an issue?)
Personally, I think that Discord has recently made a series of bad decisions (Username update anyone?) and soon enough they might attempt to monetise their API usage; similar to Reddit. So I plan on somehow migrating to a webapp.

Pushover is available on iOS & Android, it has a 30-day free trial and after that it has a $5 one-time purchase. This way I am not relying on any specific platform. For now though, this only works on Discord and Pushover.
I will remove Pushover support once the webapp has been implemented as notifications can be sent via the webapp (since iOS 16.4 on Apple devices)

Limitations:
- Poorly written (probably)
- Probably has tons of bugs.
- Relies mostly on Discord (CLI does exist but it isn't that great)
  
![Untitled](https://github.com/ii7mood/ii7-Stream-Notifier/assets/86324776/5a6f978c-9ad8-477d-be65-ac43fab73e18)


# Setting up

## Necessary Modules
You will need Python installed (>= 3.9), and added to path. You will also need pip properly configured (test by simply running pip in your terminal). (if you can run ```python --version``` (with an output of > 3.9) and ```pip``` without errors then you're good to continue.)
1) (optional) Set-up a virtual environment by running ```python -m venv venv``` while you are in the root folder ii7-Stream-Notifier. Depending on your installation you might need to substitute python for python3 or python3.9 (depends on the version installed). Then ```source venv/bin/activate``` to interact with the virtual environment.
2) Run the command ```pip install -r requirements.txt```


## Config.ini

### [PUSHOVER]
1) You will need to create an account at https://pushover.net/ , you will see a user key. <br>
2) Now you will need to create an application by clicking on the "Create an Application/API Token" link, and fill out the form. You will be re-directed back to the homepage but now you can click on your newly created app and find your token. <br>
3) Paste both the user keys and the token into the config file in ii7-Stream-Notifier/config/config.ini under [PUSHOVER]. (DO NOT SHARE THESE KEYS WITH ANYONE) <br>


### [DISCORD]
1) Head over to https://discord.com/developers and log-in / create an account. Then click on Applications on the left hand sidebar and create an Application. <br>
2) Name it whatever you want, then click on Bot and Reset Token. Now your bot token will be visible. MAKE SURE TO KEEP THIS PRIVATE AS THAT CAN LEAD TO THE BOT EXECUTING COMMANDS FROM A THIRD PARTY. <br>
3) Copy and Paste this token into the config file in ii7-Stream-Notifier/config/config.ini under [DISCORD]. Then copy the Channel ID of the text channel for the bot to send notifications to. (Enable developer mode then right-click the channel -> copy ID) <br>
4) Lastly, click on OAuth2 on the left sidebar and click on URL Generator. Select Bot, and give it the "Send Messages", "Use Slash Commands", and the "Embed links" permissions at minimum. Copy that link and paste it into google. Select your server and invite your bot to it. <br>


### [TWITCH]
**NOTE**: You do not need to use the Twitch API so this does not need to be filled **so long as scrape = 1** however this does mean that the bot cannot display the number of concurrent viewers or use the streamer's avatar instead it will display Twitch's logo. otherwise do follow these steps for the full set of features.

1) Go to https://dev.twitch.tv/ and log-in with your Twitch account.
2) Click on "Your Console" next to your profile in the top-right corner and then click "Register Your Application".
3) Choose whatever name you would like, as for the re-direct link you can just write down http://localhost if you do not plan on making use of it, and for category select "Application integeration".
4) Click the Manage button next to your app, and then click New Secret. Now copy & paste both your Client ID and Client Secret into config.ini in ii7-Stream-Notifier/config/config.ini
5) **MAKE SURE TO SET scrape to 0**

**NOTE**: Keep the host and port their default values, unless Detector.py is hosted somewhere other than the local machine then you'll need to input the host (IP) and port that the listener would listen to, per listener. Otherwise, do not change it.<br>


### ** [USAGE] **
You can use the CLI to interact with the program by running ```python modify.py``` in the terminal, in the same directory as the bot. Be aware that the CLI only has the bare minimum commands unlike the BOTs commands.
As for Discord you can simply type '/' and view all the commands and what each one does.
```/reset activity``` resets all streamers' status to not_live meaning that within the next 5 minutes you will be notified of all streams again.
```/reset database``` removes all streamers from the database meaning you will need to re-follow everyone again.



