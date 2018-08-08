#!/usr/bin/env python3
# coding: utf-8

import logging
import os
import sys

from dotenv import load_dotenv, find_dotenv
import praw

from tlb.bot import Bot

logger = logging.getLogger('tlb')

def configure_logging():
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('[%(levelname)s] %(name)s-%(asctime).19s | %(message)s')
    # create file handler which logs even debug messages
    fh = logging.FileHandler('tlb.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # create console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def main():
    bot = None
    try:
        configure_logging()
        # Load environment variables from .env file
        load_dotenv(find_dotenv())
        logger.info('Starting TweetLinkBot...')
        bot = Bot(
                workers=10,
                subreddit='all',
                username=os.getenv("BOT_USERNAME"),
                password=os.getenv("BOT_PASSWORD"),
                client_id=os.getenv("CLIENT_ID"),
                client_secret=os.getenv("CLIENT_SECRET")
            )
        bot.run()
    except KeyboardInterrupt:
        if bot:
            bot.save_db()
        # Catch Keyboard Interrupt. This area can be used to cleanly exit if wanted.
        raise Exception('ERROR: Interrupted by user')
    except Exception as e:
        if bot:
            bot.save_db()
        import traceback
        traceback.print_exc()
        raise e