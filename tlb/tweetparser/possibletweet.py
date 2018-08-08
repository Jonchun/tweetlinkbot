#!/usr/bin/env python3
# coding: utf-8


from datetime import timedelta
import difflib
import logging
import re

from tlb.tweetparser.fetcher import query_tweets, twitter_meta_text

logger = logging.getLogger('tlb.possibletweet')

class PossibleTweet:
    def __init__(self, handle, time, mentions, content):
        self.handle = handle.strip('\@')
        self.incomplete_handle = True if handle.endswith('.') else False
        self.timestamp = time
        self.mentions = mentions
        self.content = content

        self.url = None

    @property
    def full_url(self):
        return f'https://twitter.com{self.url}'

    def search_twitter(self):
        handle = f'from:{self.handle}' if not self.incomplete_handle else ''

        # search using each line of the tweet to see if we find a matching real tweet.
        for line in self.content.split('\n'):
            logger.debug(f'{handle} {line}')
            for tweet in query_tweets(f'{handle} {line}'):
                # If author is not correct, definitely not the right tweet
                if self.handle.rstrip('.') not in tweet.user:
                    logger.debug(f'User {tweet.user} is not {self.handle}')
                    continue

                # If time difference is more than 1 day, probably not the right tweet.
                time_diff = tweet.timestamp - self.timestamp
                if time_diff > timedelta(days=1):
                    logger.debug(f'Timestamp is too different. Tweet:{tweet.timestamp}, Img:{self.timestamp}')
                    continue

                # If there is a URL in the real tweet, we need to find the expanded_url because the OCR engine will have parsed it.
                meta_text = ''
                if tweet.expanded_url:
                    meta_text = twitter_meta_text(tweet.expanded_url)

                # Remove links from tweet. Download and append meta text if there is an expanded url in the tweet
                cleaned_tweet = re.sub(r'(?:https?://)?\w+(?:\.\w{1,4})+(?:/\w*)?', '', tweet.text).strip()
                # Add in the meta text
                cleaned_tweet += meta_text
                # collapse all whitespace and replace with a single space for better compariso
                cleaned_tweet = re.sub(r'\s+', ' ', cleaned_tweet)
                cleaned_content = re.sub(r'\s+', ' ', self.content)

                ratio = difflib.SequenceMatcher(None, cleaned_tweet, cleaned_content).ratio()
                # Check ratio of our local text to real text. If it is <70%, probably not the right tweet
                if ratio < 0.7:
                    if ratio > 0.4:
                        logger.debug(f'Attempting to recalculate ratio...')
                        new_length = min(len(cleaned_tweet), len(cleaned_content))
                        new_ratio = difflib.SequenceMatcher(None, cleaned_tweet[:new_length], cleaned_content[:new_length]).ratio()
                        logger.debug(f'Recalculated ratio. {new_ratio}')
                        # If recalculated ratio is really strong, that means we can attribute the discrepancy to metadata or other info from external links. It is probably the right tweet.
                        if new_ratio > .9:
                            logger.debug(f'Found the right URL: {tweet.url}')
                            self.url = tweet.url
                            break
                    logger.debug(f'Body similarity too low. Ratio {ratio}')
                    continue

                # If we got to here, we have the right tweet.

                logger.debug(f'Found the right URL: {tweet.url}')
                self.url = tweet.url
                break
            else:
                logger.debug(f'Real tweet not found. Check with next line.')
                continue  # only executed if inner loops does not break
            break # break the outer loop as well if the inner loop breaks

        if self.url:
            return True
        else:
            return False