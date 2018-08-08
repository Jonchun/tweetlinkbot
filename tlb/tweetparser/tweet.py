#!/usr/bin/env python3
# coding: utf-8

# Most of this stolen from https://github.com/taspinar/twitterscraper/blob/0.7.0/twitterscraper/tweet.py

from datetime import datetime
import logging

from bs4 import BeautifulSoup

class Tweet:
    def __init__(self, user, fullname, id, url, timestamp, text, replies, retweets, likes, html, expanded_url):
        self.user = user.strip('\@')
        self.fullname = fullname
        self.id = id
        self.url = url
        self.timestamp = timestamp
        self.text = text
        self.replies = replies
        self.retweets = retweets
        self.likes = likes
        self.html = html
        self.expanded_url = expanded_url

    @classmethod
    def from_html(cls, html):
        soup = BeautifulSoup(html, 'lxml')
        tweets = soup.find_all('li', 'js-stream-item')
        if tweets:
            for tweet in tweets:
                try:
                    yield cls.from_soup(tweet)
                except AttributeError as e:
                    print(e)
                    pass  # Incomplete info? Discard!
                except TypeError as e:
                    print(e)
                    pass  # Incomplete info? Discard!

    @classmethod
    def from_soup(cls, tweet):
        expanded_url = ''
        try:
            expanded_url=tweet.find('a', 'twitter-timeline-link')['data-expanded-url']
        except TypeError:
            # found none
            pass
        except KeyError:
            # doesn't have data-expanded-url
            pass

        return cls(
            user=tweet.find('span', 'username').text or '',
            fullname=tweet.find('strong', 'fullname').text or '', 
            id=tweet['data-item-id'] or '',
            url = tweet.find('div', 'tweet')['data-permalink-path'] or '',
            timestamp=datetime.utcfromtimestamp(
                int(tweet.find('span', '_timestamp')['data-time'])),
            text=tweet.find('p', 'tweet-text').text or '',
            replies = tweet.find(
                'span', 'ProfileTweet-action--reply u-hiddenVisually').find(
                    'span', 'ProfileTweet-actionCount')['data-tweet-stat-count'] or '0',
            retweets = tweet.find(
                'span', 'ProfileTweet-action--retweet u-hiddenVisually').find(
                    'span', 'ProfileTweet-actionCount')['data-tweet-stat-count'] or '0',
            likes = tweet.find(
                'span', 'ProfileTweet-action--favorite u-hiddenVisually').find(
                    'span', 'ProfileTweet-actionCount')['data-tweet-stat-count'] or '0',
            html=str(tweet.find('p', 'tweet-text')) or '',
            expanded_url=expanded_url
        )
