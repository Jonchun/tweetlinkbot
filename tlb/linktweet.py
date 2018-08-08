
import logging
from io import BytesIO
from pathlib import Path

from PIL import Image
from pytesseract import image_to_string
import requests

from tlb.tweetparser.parser import TweetParser

logger = logging.getLogger('tlb.reply')

def link_tweet(submission):
    # We only care about images. Also ignored saved submissions.
    try:
        if submission.saved:
            logger.debug(f'This submission has already been looked at: {submission}')
            return
        if submission.post_hint != 'image':
            return
    except AttributeError:
        return

    try:
        r = requests.get(submission.url, stream=True)
        img = Image.open(BytesIO(r.content))
        img = img.convert('L')
        img_text = image_to_string(img)
        logger.debug(f'Parsed image from: {submission.url}')
        logger.debug(f'Parsed text: {img_text}')
    except Exception as e:
        logger.exception(f'Problem getting submission image: "{submission.url}"')
        return

    possible_tweets = TweetParser(img_text).find_tweets()
    confirmed_tweets = [tweet for tweet in possible_tweets if tweet.search_twitter()]

    if not confirmed_tweets:
        logger.info(f'Found no confirmed tweets at {submission.url}.')
        return

    links = []
    for tweet in confirmed_tweets:
        links.append(f'* [Link to Tweet]({tweet.full_url})')
    p = Path(__file__).parent / 'templates/reply'

    reply = p.read_text()

    plural = 's' if len(links) > 1 else ''
    reply = reply.replace('{plural}', plural)
    reply = reply.replace('{links}', '\n'.join(links))

    submission.reply(reply)
    # Save submission if we respond. That way, even if there is a bot crash/discrepancy, we don't double-post.
    submission.save()
    logger.info(f'Replied to {submission} with {len(confirmed_tweets)} links.')
    logger.debug('\n'.join(links))
