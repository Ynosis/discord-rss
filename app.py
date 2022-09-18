import fetch
import os
import time
from discord import Webhook, RequestsWebhookAdapter, File
from telethon import TelegramClient, events, sync
from telethon.errors.rpcerrorlist import UsernameInvalidError
from telethon.tl.functions.channels import JoinChannelRequest
import json
from enum import Enum

import signal
import sys
import atexit

from configparser import ConfigParser, NoOptionError
import config

from Formatting import format_single_article

# expects the configuration file in the same directory as this script by default, replace if desired otherwise
configuration_file_path = os.path.join(
    os.path.split(os.path.abspath(__file__))[0], "Config.txt"
)

# put the discord hook urls to the channels you want to receive feeds in here
private_sector_feed = Webhook.from_url(config.EDEN_CLUB_CTI_PRIVATE_SECTOR, adapter=RequestsWebhookAdapter())
government_feed = Webhook.from_url(config.EDEN_CLUB_CTI_PUBLIC_SECTOR, adapter=RequestsWebhookAdapter())
ransomware_feed = Webhook.from_url(config.EDEN_CLUB_CTI_RANSOMWARE, adapter=RequestsWebhookAdapter())
# put the discord hook url to the channel you want to receive feeds in here
telegram_feed = Webhook.from_url(config.EDEN_CLUB_TG_FEED, adapter=RequestsWebhookAdapter())
reuters_feed = Webhook.from_url(config.EDEN_CLUB_MARKINT_FEED, adapter=RequestsWebhookAdapter())

FeedTypes = Enum("FeedTypes", "RSS JSON")

source_details = {
    "Private RSS Feed": {
        "source": config.cti_private_rss_feed_list,
        "hook": private_sector_feed,
        "type": FeedTypes.RSS,
    },
    "Gov RSS Feed": {
        "source": config.cti_gov_rss_feed_list,
        "hook": government_feed,
        "type": FeedTypes.RSS,
    },
    "Ransomware News": {
        "source": "https://raw.githubusercontent.com/joshhighet/ransomwatch/main/posts.json",
        "hook": ransomware_feed,
        "type": FeedTypes.JSON,
    },
    "Reuters MARKINT": {
        "source": config.reuters_rss_feed_list,
        "hook": reuters_feed,
        "type": FeedTypes.RSS
    }
}

def create_telegram_output(group, message):
    telegram_feed.send(f'{group} {time.ctime()} {message}')
    

if __name__ == '__main__':

    # downloads to the TelegramImages directory by default, replace if desired otherwise
    image_download_path = os.path.join(os.path.split(os.path.abspath(__file__))[0], '..', 'TelegramImages')

    config_file = ConfigParser()
    config_file.read(configuration_file_path)

    # put your telegram api stuff in here
    telegram_client = TelegramClient(config.TG_NAME, config.TG_ID, config.TG_HASH)
    telegram_client.start()
    
#    """  # Instatiate object per feed item
#     for feed in range(len(config.telegram_feed_list)):
#         vars()[feed] = telegram_client.get_entity(config.telegram_feed_list[feed])

#         try: # TODO consider only sending join requests if not already joined
#             telegram_client(JoinChannelRequest(vars()['feed']))
#         except (UsernameInvalidError, TypeError, ValueError): # telegram user or channel was not found
#             continue
#  """

    signal.signal(signal.SIGTERM, lambda num, frame: clean_up_and_close())
    while True:
        for detail_name, details in source_details.items():
            fetch.write_status_messages_to_discord(f"Checking {detail_name}")

            if details["type"] == FeedTypes.JSON:
                fetch.process_source(fetch.get_ransomware_news, details["source"], details["hook"])
            elif details["type"] == FeedTypes.RSS:
                fetch.handle_rss_feed_list(details["source"], details["hook"])

        fetch.write_status_messages_to_discord("All done")
        with open(configuration_file_path, "w") as f:
            config_file.write(f)

        time.sleep(1800)
    telegram_client.run_until_disconnected()



@telegram_client.on(events.NewMessage(incoming=True))
async def event_handler(event):
    if event.photo:
        image_data = await event.download_media(image_download_path)
        upload_file = File(open(image_data, 'rb'))
        telegram_feed.send(file=upload_file)
        
    for channel in telegram_feed_list:
        # TODO consider error handling here and write to a secondary discord status channel on errors
        if globals()[channel].id == event.message.peer_id.channel_id:
            create_telegram_output(globals()[channel].title, event.message.message)
            break
