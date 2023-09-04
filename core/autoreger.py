import asyncio
import random

from asyncio import create_task, sleep, Semaphore

from core.utils import logger
from core.utils.cookies_manager import CookiesManager
from core.utils.file_to_list import file_to_list
from core.twitter import Twitter

from inputs.config import (
    THREADS, CUSTOM_DELAY, COOKIES_FILE_PATH, PROXIES_FILE_PATH, TWEETS_URLS_PATH, TWEETS_PHRASES_PATH
)


class AutoReger:
    def __init__(self):
        self.success = 0
        self.custom_user_delay = None

    @staticmethod
    def get_accounts():
        twitter_cookies = CookiesManager(COOKIES_FILE_PATH).get_cookies()
        proxies = file_to_list(PROXIES_FILE_PATH)
        tweets_urls = file_to_list(TWEETS_URLS_PATH)
        phrases = file_to_list(TWEETS_PHRASES_PATH)

        random.shuffle(phrases)

        accounts = []

        for i, tweets_url in enumerate(tweets_urls):
            for cookies in twitter_cookies:
                accounts.append((cookies, tweets_url, phrases[i], proxies[i] if len(proxies) > i else None))

        return accounts

    async def start(self):
        self.custom_user_delay = CUSTOM_DELAY

        accounts = AutoReger.get_accounts()

        logger.info(f"I will make {len(accounts)} replies")

        semaphore = Semaphore(THREADS)

        tasks = []
        for account in accounts:
            task = create_task(self.register(account, semaphore))
            tasks.append(task)

        await asyncio.gather(* tasks)

        if self.success:
            logger.success(f"Successfully registered {self.success} accounts :)")
        else:
            logger.warning(f"No accounts registered :(")

    async def register(self, account: tuple, semaphore: Semaphore):
        cookies, tweet_url, phrase, proxy = account

        twitter = Twitter(cookies, proxy)

        is_ok = False
        logs_file_name = "fail"
        log_msg = "Failed to make reply :("

        try:
            async with semaphore:
                if self.custom_user_delay > 0:
                    sleep_time = self.custom_user_delay * random.uniform(1, 1.3)
                    logger.info(f"Sleep for {int(sleep_time)} seconds")
                    await sleep(sleep_time)

                words = ["@tipcoineth", "$tip", phrase]
                random.shuffle(words)

                msg_text = random.choice(['\n', '\n\n', " "]).join(words)
                tweet_id = tweet_url.split("/")[-1]
                resp_json = await twitter.reply(msg_text, tweet_id)

                if resp_json is not None:
                    reply_url = AutoReger.parse_comment_url(resp_json)
                    if reply_url:
                        is_ok = True
                        msg_text = msg_text.replace('\n', '\\n')
                        log_msg = f"Text: {msg_text} | Reply url: {reply_url}"
        except Exception as e:
            logger.error(f"Error {e}")

        await twitter.session.close()

        # AutoReger.remove_account()

        if is_ok:
            logs_file_name = "success"
            self.success += 1

        twitter.logs(logs_file_name, log_msg)

    @staticmethod
    def parse_comment_url(resp_json: dict):
        reply_result = resp_json.get("data", {}).get("create_tweet", {}).get("tweet_results", {}).get("result")

        if reply_result is None:
            return

        reply_id = reply_result.get("rest_id")
        user_name = (reply_result.get("core", {}).get("user_results", {}).get("result", {})
                     .get("legacy", {}).get("screen_name"))

        return f"https://twitter.com/{user_name}/status/{reply_id}"

    @staticmethod
    def is_file_empty(path: str):
        return not open(path).read().strip()
