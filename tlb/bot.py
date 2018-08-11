#!/usr/bin/env python3
# coding: utf-8

import logging
import pickle
import re
import time

import praw
from prawcore.exceptions import PrawcoreException

from tlb.linktweet import link_tweet
from tlb.taskqueue import TaskQueue

logger = logging.getLogger('tlb.bot')

class Bot:
    """ The Bot class handles most of the general logic and operations of the TweetLinkBot.
    """
    def __init__(self,  workers=5, subreddit='all', **kwargs):
        """
        Construct a new Bot        

        Args:
            workers (int): How many workers to use when running bot.
            subreddits (list of str): List of subreddits to run the bot in.
        """
        self.queue = TaskQueue(num_workers=workers)
        self.subreddit = subreddit

        try:
            # reddit client
            self.rc = praw.Reddit(
                        username=kwargs.get('username'),
                        password=kwargs.get('password'),
                        client_id=kwargs.get('client_id'),
                        client_secret=kwargs.get('client_secret'),
                        user_agent='TweetLinkBot'
                    )
        except Exception as e:
            raise Exception('Unable to connect to Reddit')

        self.reddit_name = self.rc.user.me().name

        self.register_plugins()
        self.load_db()

    def register_plugins(self):
        pass

    def load_db(self):
        db = set()
        try:
            with open('records.pickle', 'rb') as f:
                db = pickle.load(f)
                logger.info('Loaded previous db from file')
        except Exception as e:
            logger.error('Unable to load previous records file. Starting from scratch.')
        self.db = db

    def save_db(self):
        with open('records.pickle', 'wb') as f:
            pickle.dump(self.db, f, protocol=pickle.HIGHEST_PROTOCOL)

        logger.info('Saved current db to file')

    def run(self):
        # We are going to loop through each subreddit where the bot is enabled and grab the hot 100.
        logger.info(f'Now active with {self.queue.num_workers} workers. Logged in as {self.reddit_name}')

        try:
            for submission in self.rc.subreddit(self.subreddit).stream.submissions():
                self.queue.add_task(self.check_submission, submission)
        except praw.exceptions.APIException:
            logger.exception('Something wrong with the API... Waiting 1 minute  and retrying...')
            time.sleep(60)
        except praw.exceptions.PRAWException:
            logger.exception('Something wrong with PRAW. Attempting to restart in 5 seconds...')
            time.sleep(5)
        except PrawcoreException:
            logger.exception('Something went wrong while dealing with Prawcore. Attempting to restart in 5 seconds...')
            time.sleep(5)
        self.run()

    def check_submission(self, submission):
        # Don't parse if we already checked
        if str(submission) in self.db:
            logger.debug('Skipping {} [Submission]. Already in DB'.format(submission))
            return False

        # Do stuff here
        self.queue.add_task(link_tweet, submission)

        self.db.add(str(submission))
        logger.debug('Added {} [Submission] to db'.format(submission))
