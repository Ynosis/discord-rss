import atexit
import os
import time
from configparser import ConfigParser, NoOptionError
import sys
import config
import Formatting
import requests

from discord import Webhook, RequestsWebhookAdapter
import feedparser
from enum import Enum

# expects the configuration file in the same directory as this script by default, replace if desired otherwise
configuration_file_path = os.path.join(
    os.path.split(os.path.abspath(__file__))[0], "Config.txt"
)

config_file = ConfigParser()
config_file.read(configuration_file_path)
# this one is logging of moniotring status only
status_messages = Webhook.from_url(config.EDEN_CLUB_BOT_STATUS, adapter=RequestsWebhookAdapter())
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

def get_ransomware_news(source):
    posts = requests.get(source).json()

    for post in posts:
        post["publish_date"] = post["discovered"]
        post["title"] = "Post: " + post["post_title"]
        post["source"] = post["group_name"]

    return posts


def get_news_from_rss(rss_item):
    feed_entries = feedparser.parse(rss_item[0]).entries

    # This is needed to ensure that the oldest articles are proccessed first. See https://github.com/vxunderground/ThreatIntelligenceDiscordBot/issues/9 for reference
    for rss_object in feed_entries:
        rss_object["source"] = rss_item[1]
        try:
            rss_object["publish_date"] = time.strftime(
                "%Y-%m-%dT%H:%M:%S", rss_object.published_parsed
            )
        except:
            rss_object["publish_date"] = time.strftime(
                "%Y-%m-%dT%H:%M:%S", rss_object.updated_parsed
            )

    return feed_entries


def proccess_articles(articles):
    messages, new_articles = [], []
    articles.sort(key=lambda article: article["publish_date"])

    for article in articles:
        try:
            config_entry = config_file.get("main", article["source"])
        except NoOptionError:  # automatically add newly discovered groups to config
            config_file.set("main", article["source"], " = ?")
            config_entry = config_file.get("main", article["source"])

        if config_entry.endswith("?"):
            config_file.set("main", article["source"], article["publish_date"])
        else:
            if config_entry >= article["publish_date"]:
                continue

        messages.append(Formatting.format_single_article(article))
        new_articles.append(article)

    return messages, new_articles


def send_messages(hook, messages, articles, batch_size=10):
    for i in range(0, len(messages), batch_size):
        try:
            hook.send(embeds=messages[i : i + batch_size])
        except:
            print("Empty embed for ", messages[i : i + batch_size])


        for article in articles[i : i + batch_size]:
            config_file.set(
                "main", article["source"], article["publish_date"]
            )

        time.sleep(3)


def process_source(post_gathering_func, source, hook):
    raw_articles = post_gathering_func(source)

    processed_articles, new_raw_articles = proccess_articles(raw_articles)
    send_messages(hook, processed_articles, new_raw_articles)


def handle_rss_feed_list(rss_feed_list, hook):
    for rss_feed in rss_feed_list:
        status_messages.send(f"> {rss_feed[1]}")
        process_source(get_news_from_rss, rss_feed, hook)


def write_status_messages_to_discord(message):
    status_messages.send(f"**{time.ctime()}**: *{message}*")
    time.sleep(3)


@atexit.register
def clean_up_and_close():
    with open(configuration_file_path, "w") as f:
        config_file.write(f)

    sys.exit(0)

