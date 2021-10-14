"""Proof book fetch protocols."""

import os
import re
from urllib.parse import urlparse, urlunparse

import yaml
import requests
import tweepy


class FetchError(Exception):
    pass


def url_fetch(comps):
    cid = comps.netloc
    r = requests.get(urlunparse(comps))
    return r.text


def ipfs_fetch(comps):
    cid = comps.netloc
    r = requests.get(f"https://ipfs.io/ipfs/{cid}")
    # r = requests.get(f"http://{cid}.ipfs.localhost:8080/")
    return r.text


def file_fetch(comps):
    path = comps.netloc
    with open(path, "rt") as finp:
        return finp.read()


def twitter_fetch(comps):
    """Look for a tweet that contains a devigny signature for a particular
    user.

    twitter://handle

    """

    user_name = comps.netloc
    if user_name[0] == "@":
        user_name = user_name[1:]

    try:
        api_key = os.environ["TWITTER_API_KEY"]
        api_secret_key = os.environ["TWITTER_API_SECRET_KEY"]
    except KeyError:
        raise FetchError(
            "TWITTER_API_KEY and TWITTER_API_SECRET_KEY environment variables not set"
        )

    auth = tweepy.AppAuthHandler(api_key, api_secret_key)
    api = tweepy.API(auth)
    r = api.search_tweets(q="from:weschow devigny:")

    if not r:
        raise FetchError(
            f"could not find devigny signature attached to Twitter account @{user_name}"
        )

    return r[0].text


def fetch(uri):
    comps = urlparse(uri)
    if comps.scheme in ["http", "https"]:
        return url_fetch(comps)
    if comps.scheme == "ipfs":
        return ipfs_fetch(comps)
    if comps.scheme == "file":
        return file_fetch(comps)
    if comps.scheme == "twitter":
        return twitter_fetch(comps)

    raise NotImplementedError(f"unknown fetch scheme {comps.scheme}")
