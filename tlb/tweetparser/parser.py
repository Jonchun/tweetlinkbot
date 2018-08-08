#!/usr/bin/env python3
# coding: utf-8

import datetime as dt
import logging
import re

from dateutil.parser import parse as dateparse

from tlb.tweetparser.possibletweet import PossibleTweet

class TweetParser:
    def __init__(self, message):
        self.message = message

    def find_handles(self):
        matches = re.finditer(r'@\w+(?:\.\.\.)?\s', self.message, re.MULTILINE)
        matches = [(match, 'handle') for match in matches]
        return matches

    def find_times(self):
        # Search for twitter-formatted timestamps. There are 2 types I am looking for
        times = []

        matches = re.finditer(r'\d{1,2}/\d{1,2}/\d{1,2},?\s\d{1,2}:\d{2}\s[AP]M', self.message, re.MULTILINE)
        matches = [(match, 'time') for match in matches]
        times.extend(matches)

        matches = re.finditer(r'\d{1,2}:\d{2}\s[AP]M\s-\s\w{3}\s\d{1,2},?\s\d{4}', self.message, re.MULTILINE)
        matches = [(match, 'time') for match in matches]
        times.extend(matches)

        matches = re.finditer(r'\d{1,2}:\d{2}\s[AP]M\s-\s\d{1,2}\s\w{3}\s\d{2,4}', self.message, re.MULTILINE)
        matches = [(match, 'time') for match in matches]
        times.extend(matches)

        return times

    def is_tweet_possible(self):
        if 'tweet' in self.message:
            self._handles = self.find_handles()
            self._times = self.find_times()
            return True

        if self._handles or self._times:
            return True

        return False

    def find_tweets(self):
        _handles = self.find_handles()
        _times = self.find_times()

        # Check if tweet is even possible. If not, return empty.
        if ('tweet' not in self.message) and (not _handles or not _times):
            return []

        # Combine the results. matches is a list of tuples (re.Match, str)
        matches = _handles + _times

        # Sort the results by their index position in the message. 
        matches.sort(key=lambda m: m[0].span()[0])


        # Loop through all the matches and break it down into PossibleTweets
        possible_tweets = []

        current_handle = None
        mentions = []
        tweet_start = 0
        tweet_end = -1

        for match in matches:
            # Tweet must start with a handle
            if match[1] == 'time' and not current_handle:
                continue

            # Start of a new tweet.
            if match[1] == 'handle' and not current_handle:
                current_handle = match[0].group().strip()
                tweet_start = match[0].span()[1]
                continue
            # If we get another handle before tweet closes, that means the tweet is mentioning someone.
            if match[1] == 'handle':
                mentions.append(match[0].group().strip())
                continue
            # If not, close the tweet because it must be a time.
            elif match[1] == 'time':
                tweet_time = match[0].group().strip()
                tweet_timestamp = self.parse_time(tweet_time)
                tweet_end = match[0].span()[0]

                # get tweet content and remove any links
                content = self.message[tweet_start:tweet_end].strip()
                content = re.sub(r'(?:https?://)?\w+(?:\.\w{1,4})+(?:/\w*)?', '', content).strip()
                content = re.sub(r'\n+', '\n', content)

                # OCR detects I's as pipes for some reason...
                content = content.replace('|', 'I')
                possible_tweets.append(PossibleTweet(current_handle, tweet_timestamp, mentions, content))

                # reset handle and mentions
                current_handle = None
                mentions = []
                continue
            raise Exception('Error parsing for possible tweets')

        return possible_tweets

    def parse_time(self, time):
        # remove - and , | also change toupper for consistency
        time = re.sub(r'[-,]','', time).upper()
        # collapse spaces
        time = re.sub(r'\s+',' ', time)

        match = re.search(r'(\d{1,2}):(\d{2})\s([AP]M)', time)
        if not match:
            raise Exception('Unable to parse time')
        hours = int(match.group(1))
        minutes = int(match.group(2))
        period = match.group(3)
        if period == 'PM' and hours != 12:
            hours += 12

        time = time.replace(match.group(0), '').strip()
        date = dateparse(time)

        # Add the hour back in manually
        date = date + dt.timedelta(hours=hours, minutes=minutes)

        return date