#!/usr/bin/env python3
# coding: utf-8

import json
import logging
import random

from bs4 import BeautifulSoup
import requests

from tlb.tweetparser.tweet import Tweet

logger = logging.getLogger('tlb.fetcher')

#INIT_URL = 'https://twitter.com/search?f=tweets&vertical=default&q={q}'
SEARCH_URL = "https://twitter.com/i/search/timeline?f=tweets&vertical=default&include_available_features=1&include_entities=1&reset_error_state=false&src=typd&max_position={offset}&q={q}"

HEADERS_LIST = [
    'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2226.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.75.14 (KHTML, like Gecko) Version/7.0.3 Safari/7046A194A',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:40.0) Gecko/20100101 Firefox/40.1',
    'Mozilla/5.0 (Windows NT 6.1; WOW64; Trident/7.0; AS; rv:11.0) like Gecko',
    'Mozilla/5.0 (compatible, MSIE 11, Windows NT 6.3; Trident/7.0; rv:11.0) like Gecko',
]


# Query borrowed from https://github.com/taspinar/twitterscraper/blob/0.7.0/twitterscraper/query.py
def query_tweets(query):
    query = query.replace(' ', '%20').replace("#", "%23").replace(":", "%3A")
    tweets = []
    url = SEARCH_URL.format(q=query, offset=0)

    html = ''
    try:
        response = requests.get(url, headers={'User-Agent': random.choice(HEADERS_LIST)})
        try:
            json_text = response.text
            json_resp = json.loads(json_text)
            html = json_resp['items_html'] or ''
        except ValueError as e:
            logger.exception(f'Failed to parse JSON "{e}" while requesting "{url}". \n{json_text}')
    except requests.exceptions.HTTPError as e:
        logger.exception(f'HTTPError {e} while requesting "{url}"')
    except requests.exceptions.ConnectionError as e:
        logger.exception(f'ConnectionError {e} while requesting "{url}"')
    except requests.exceptions.Timeout as e:
        logger.exception(f'Timeout {e} while requesting "{url}"')
    except json.decoder.JSONDecodeError as e:
        logger.exception(f'Failed to parse JSON "{e}" while requesting "{url}"')

    tweets = list(Tweet.from_html(html))

    return tweets

def twitter_meta_text(url):
    try:
        response = requests.get(url, headers={'User-Agent': random.choice(HEADERS_LIST)})
    except requests.exceptions.HTTPError as e:
        logger.exception(f'HTTPError {e} while requesting "{url}"')
    except requests.exceptions.ConnectionError as e:
        logger.exception(f'ConnectionError {e} while requesting "{url}"')
    except requests.exceptions.Timeout as e:
        logger.exception(f'Timeout {e} while requesting "{url}"')

    try:
        soup = BeautifulSoup(response.content, 'lxml')
        title = soup.find("meta",  property="twitter:title")
        description = soup.find("meta",  property="twitter:description")

        if not title or not description:
            title = soup.find("meta",  property="og:title")
            description = soup.find("meta",  property="og:description")

        if not title or not description:
            return ''
        else:
            return title.get('content', '') + description.get('content', '')
    except Exception:
        logger.exception('Unable to parse twitter meta text')
        return ''

