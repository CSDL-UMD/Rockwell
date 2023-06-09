# Function to get the card info from a website for a tweet.
# Requires full tweet links in order to work as anticipated.

import logging
import requests
from bs4 import BeautifulSoup
from configparser import ConfigParser

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/114.0"


def config(filename='database.ini', section='postgresql'):
    """
    Read configuration file
    """
    # create a parser
    parser = ConfigParser()
    # read config file
    parser.read(filename)

    # get section, default to postgresql
    db = {}
    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception('Section {0} not found in the {1} file'.format(section, filename))

    return db


def truncate(s, maxlen, ellipsis="..."):
    """
    Truncate string to maxlen with optional ellipsis.
    """
    if len(s) > (maxlen - len(ellipsis)):
        s = s[:maxlen] + ellipsis
    return s


def meta2dict(body):
    """ 
    Convert meta tags with a "content" attribute to a dictionary mapping
    the name of the property (typically the value of either a "name" or
    "property" attribute) to the value of the "content" attribute.

    Example:

        <meta name="twitter:card" content="summary_large_image" />
        <meta name="twitter:site" content="@UMD" />

    Will return the dictionary

    {
        "twitter:card": "summary_large_image",
        "twitter:site: "@UMD"
    }

    Only tags with a "content" attribute will be included.
    """
    tags = body.find_all(name="meta")
    d = {}
    for tag in tags:
        # skip meta tags without two separate attributes (property/name and content)
        if len(tag.attrs) < 2:
            continue
        # since we are going to pop, keep body unchanged by working on a copy
        attrs = tag.attrs.copy()
        # get value of "content" attribute; skip tags without it
        try:
            value = attrs.pop("content")
        except KeyError:
            continue
        # the name of the property can be under the "name" or "property" attribute
        _, key = attrs.popitem()
        d[key] = value
    return d


def getCardData(url, maxretries=3, timeout=0.5): 
    """
    Returns a dictionary with the following information needed to display a card
    of an external web page:

        image - URL to card image
        title - card title string
        description - card description

    Both the title and description are shortened to a maximum length specified
    in the configuration file. 

    Parameters
    ==========

    url : str
        The URL whose card we are fetching

    maxretries : int
        Maximum number of retries in case of timeout

    timeout : float
        The initial timeout with exponential backoff in case of timeout
    """
    resp = None
    try:
        with requests.Session() as session:
            for i in range(maxretries):
                try:
                    resp = session.get(url, 
                                       timeout=timeout, 
                                       headers={"User-Agent": USER_AGENT})
                except requests.Timeout:
                    logging.error(f"Time out after {timeout}s: {url}")
                    timeout *= 2
    except (requests.RequestException, requests.ConnectionError) as e:
        logging.error(f"{e.__class__.__name__}: {e}: {url}")
        return {}
    if resp is None:
        logging.error(f"Max retries reached: {url}")
        return {}
    if not resp.ok:
        logging.error(f"{resp.status_code} {resp.reason}: {url}")
        
    params = config('../configuration/config.ini','twitterapp')
    try: 
        soup = BeautifulSoup(resp.text, "html.parser")
        meta = meta2dict(soup)
        image = \
            meta.get("twitter:image") or \
            meta.get("twitter:image:src") or \
            meta.get("og:image")
        title = meta.get("twitter:title") or meta.get("og:title")
        description = meta.get("twitter:description") or meta.get("og:description")
        if any([image is None, title is None, description is None]):
            logging.error(f"No card data: {url}")
            return {}
        return {
            "image": image,
            "title": truncate(title, int(params['title_max'])),
            "description": truncate(description, int(params['description_max']))
        }
    except Exception as e:
        logging.error(f"{e.__class__.__name__}: {e}: {url}")
        return {}
