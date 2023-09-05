import json

import requests
from fake_useragent import UserAgent

from aiohttp import ClientSession
from aiohttp_proxy import ProxyConnector

from core.utils import str_to_file, logger

from inputs.config import (
    MOBILE_PROXY,
    MOBILE_PROXY_CHANGE_IP_LINK
)


class Twitter:
    reply_query_id = "PIZtQLRIYtSa9AtW_fI2Mw"

    def __init__(self, twitter: dict, proxy: str | None):
        self.cookies = twitter

        self.proxy = proxy

        self.headers = {
            'authority': 'twitter.com',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
            'content-type': 'application/json',
            'origin': 'https://twitter.com',
            'referer': 'https://twitter.com',
            'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': UserAgent().random,
            'x-csrf-token': twitter['ct0'],
            'x-twitter-active-user': 'yes',
            'x-twitter-auth-type': 'OAuth2Session',
            'x-twitter-client-language': 'en',
        }

        self.session = ClientSession(headers=self.headers, trust_env=True,
                                     connector=self.proxy and ProxyConnector.from_url("http://" + self.proxy))

    async def reply(self, text: str, tweet_id: str):
        url = f'https://twitter.com/i/api/graphql/{Twitter.reply_query_id}/CreateTweet'

        json_data = {
            'variables': {
                'tweet_text': text,
                'reply': {
                    'in_reply_to_tweet_id': tweet_id,
                    'exclude_reply_user_ids': [],
                },
                'dark_request': False,
                'media': {
                    'media_entities': [],
                    'possibly_sensitive': False,
                },
                'semantic_annotation_ids': [],
            },
            'features': {
                'tweetypie_unmention_optimization_enabled': True,
                'responsive_web_edit_tweet_api_enabled': True,
                'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
                'view_counts_everywhere_api_enabled': True,
                'longform_notetweets_consumption_enabled': True,
                'responsive_web_twitter_article_tweet_consumption_enabled': False,
                'tweet_awards_web_tipping_enabled': False,
                'longform_notetweets_rich_text_read_enabled': True,
                'longform_notetweets_inline_media_enabled': True,
                'responsive_web_graphql_exclude_directive_enabled': True,
                'verified_phone_label_enabled': False,
                'freedom_of_speech_not_reach_fetch_enabled': True,
                'standardized_nudges_misinfo': True,
                'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': True,
                'responsive_web_media_download_video_enabled': False,
                'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
                'responsive_web_graphql_timeline_navigation_enabled': True,
                'responsive_web_enhance_cards_enabled': False,
            },
            'queryId': Twitter.reply_query_id,
        }

        async with self.session.post(url, cookies=self.cookies, json=json_data) as resp:
            return Twitter.parse_resp_json(await resp.text())

    @staticmethod
    def parse_resp_json(text: str):
        try:
            return json.loads(text)
        except Exception as e:
            logger.info(f"Can't make post!")

    @staticmethod
    def get_proxy(proxy: str):
        if MOBILE_PROXY:
            Twitter.change_ip()
            proxy = MOBILE_PROXY

        if proxy is not None:
            return f"http://{proxy}"

    @staticmethod
    def change_ip():
        requests.get(MOBILE_PROXY_CHANGE_IP_LINK)

    def logs(self, file_name: str, log_msg: str):
        file_msg = f"{self.proxy}"
        str_to_file(f"./logs/{file_name}.txt", file_msg)
        if file_name == "success":
            logger.success(log_msg)
        else:
            logger.error(log_msg)
