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

def main():
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


if __name__ == '__main__':

    # downloads to the TelegramImages directory by default, replace if desired otherwise
    #image_download_path = os.path.join(os.path.split(os.path.abspath(__file__))[0], '..', 'TelegramImages')

    config_file = ConfigParser()
    config_file.read(configuration_file_path)

    # put your telegram api stuff in here
    #telegram_client = TelegramClient(config.TG_NAME, config.TG_ID, config.TG_HASH)
    #telegram_client.start()
    
    signal.signal(signal.SIGTERM, lambda num, frame: fetch.clean_up_and_close())
    main()

    #telegram_client.run_until_disconnected()

