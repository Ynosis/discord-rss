import utils.fetch as fetch
import os
import time
from discord import Webhook, RequestsWebhookAdapter, File
from enum import Enum

import signal
import sys
import atexit

from dotenv import load_dotenv
from configparser import ConfigParser, NoOptionError
import utils.feeds as feeds

from utils.format import format_single_article

# expects the configuration file in the same directory as this script by default, replace if desired otherwise
configuration_file_path = os.path.join(
    os.path.split(os.path.abspath(__file__))[0], "Config.txt"
)



# put the discord hook urls to the channels you want to receive feeds in here
private_sector_feed = Webhook.from_url(os.getenv('CTI_WEBHOOK'), adapter=RequestsWebhookAdapter())
gov_cti_feed = Webhook.from_url(os.getenv('CTI_WEBHOOK'), adapter=RequestsWebhookAdapter())
gov_finance_feed = Webhook.from_url(os.getenv('GOV_FINTEL_WEBHOOK'), adapter=RequestsWebhookAdapter())
ransomware_feed = Webhook.from_url(os.getenv('RANSOMWARE_WEBHOOK'), adapter=RequestsWebhookAdapter())
# put the discord hook url to the channel you want to receive feeds in here
reuters_feed = Webhook.from_url(os.getenv('REUTERS_WEBHOOK'), adapter=RequestsWebhookAdapter())

FeedTypes = Enum("FeedTypes", "RSS JSON")

source_details = {
    "Private RSS Feed": {
        "source": feeds.ThreatIntel,
        "hook": private_sector_feed,
        "type": FeedTypes.RSS,
    },
    "Gov RSS Feed": {
        "source": feeds.GovThreatIntel,
        "hook": gov_cti_feed,
        "type": FeedTypes.RSS,
    },
    "Ransomware News": {
        "source": "https://raw.githubusercontent.com/joshhighet/ransomwatch/main/posts.json",
        "hook": ransomware_feed,
        "type": FeedTypes.JSON,
    },
    "Reuters MARKINT": {
        "source": feeds.Reuters,
        "hook": reuters_feed,
        "type": FeedTypes.RSS
    },
    "Government Finance RSS": {
        "source": feeds.TreasuryGovRss,
        "hook": gov_finance_feed,
        "type": FeedTypes.RSS

    }
}

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

    load_dotenv()
    config_file = ConfigParser()
    config_file.read(configuration_file_path)
    signal.signal(signal.SIGTERM, lambda num, frame: fetch.clean_up_and_close())
    main()


