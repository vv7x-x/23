"""
services/instagram_service.py

Instagram DM polling service using instagrapi with session persistence,
safe polling, anti-ban measures, retry logic and file-based persistence.

Design principles:
- Use instagrapi Client and session dump/load to persist login.
- Poll with randomized intervals and human-like reply delays.
- Persist processed message IDs and reply timestamps in `data/instagram_store.json`.
- Limit replies per user per hour using `RateLimiter`.
- Send incoming messages to local Flask API endpoint and post replies back.
"""
from __future__ import annotations
import json
import logging
import os
import random
import signal
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests
from instagrapi import Client

from services.rate_limiter import RateLimiter
from config import get_instagram_credentials

# Logging
logger = logging.getLogger("n0x.instagram_service")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


@dataclass
class InstagramServiceConfig:
    data_dir: str = "data"
    settings_file: str = "data/ig_settings.json"
    store_file: str = "data/instagram_store.json"
    api_endpoint: str = "http://127.0.0.1:5000/receive_message"
    min_poll: int = 8
    max_poll: int = 18
    min_reply_delay: int = 4
    max_reply_delay: int = 12
    max_replies_per_hour: int = 5
    request_timeout: int = 10
    max_retries: int = 3


class InstagramService:
    def __init__(self, cfg: InstagramServiceConfig):
        self.cfg = cfg
        self.client = Client()
        self.stop_event = threading.Event()
        os.makedirs(self.cfg.data_dir, exist_ok=True)
        self._load_store()
        self.rate_limiter = RateLimiter(max_per_hour=self.cfg.max_replies_per_hour)
        self.cooldown = False

    # ---------------- persistence -----------------
    def _load_store(self) -> None:
        path = self.cfg.store_file
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.store: Dict[str, Any] = json.load(f)
            except Exception:
                logger.exception("Failed to read store file, starting fresh")
                self.store = {"processed_ids": [], "replies": {}}
        else:
            self.store = {"processed_ids": [], "replies": {}}

    def _save_store(self) -> None:
        path = self.cfg.store_file
        tmp = path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.store, f, ensure_ascii=False, indent=1)
            os.replace(tmp, path)
        except Exception:
            logger.exception("Failed to write store file")

    def _mark_processed(self, msg_id: str) -> None:
        if msg_id not in self.store["processed_ids"]:
            self.store["processed_ids"].append(msg_id)
            # bound the size to keep file small
            if len(self.store["processed_ids"]) > 10000:
                self.store["processed_ids"] = self.store["processed_ids"][-8000:]
            self._save_store()

    def _record_reply(self, user_id: str) -> None:
        lst = self.store.setdefault("replies", {}).setdefault(str(user_id), [])
        lst.append(time.time())
        # prune older than 24h (keep file small)
        cutoff = time.time() - 24 * 3600
        self.store["replies"][str(user_id)] = [t for t in lst if t >= cutoff]
        self._save_store()

    # ---------------- login & session -----------------
    def login(self) -> None:
        try:
            username, password = get_instagram_credentials()
        except Exception as exc:
            logger.error("Missing Instagram credentials: %s", exc)
            raise

        # Try to load settings
        try:
            if os.path.exists(self.cfg.settings_file):
                logger.info("Loading IG session settings from %s", self.cfg.settings_file)
                self.client.load_settings(self.cfg.settings_file)
                # try to re-login using loaded session
                self.client.get_timeline_feed()  # lightweight call to ensure session valid
                logger.info("Loaded existing session OK")
                return
        except Exception:
            logger.warning("Existing session invalid, will perform fresh login", exc_info=True)

        # Fresh login
        try:
            logger.info("Logging in as %s", username)
            self.client.login(username, password)
            # dump settings
            try:
                self.client.dump_settings(self.cfg.settings_file)
                logger.info("Saved IG session settings to %s", self.cfg.settings_file)
            except Exception:
                logger.exception("Failed to dump IG settings")
        except Exception as exc:
            # handle challenge_required / checkpoint
            logger.exception("Login failed: %s", exc)
            self.cooldown = True
            raise

    # ---------------- helpers -----------------
    def _random_sleep(self, low: int, high: int) -> None:
        t = random.uniform(low, high)
        logger.debug("Sleeping for %.2fs", t)
        time.sleep(t)

    def _post_to_api(self, from_id: str, text: str) -> Optional[str]:
        payload = {"user_id": self.client.username or "owner", "from_id": str(from_id), "text": text}
        url = os.environ.get("N0X_API_ENDPOINT", self.cfg.api_endpoint)
        logger.debug("Posting incoming message to API %s: %s", url, payload)
        for attempt in range(1, self.cfg.max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=self.cfg.request_timeout)
                resp.raise_for_status()
                data = resp.json()
                reply = data.get("reply")
                logger.debug("Received reply from API: %s", reply)
                return reply
            except requests.RequestException:
                logger.exception("Network error posting to API (attempt %s)", attempt)
                time.sleep(1.5 * attempt)
        return None

    # ---------------- polling loop -----------------
    def _process_thread_message(self, thread: Any, msg: Any) -> None:
        # Attempt to extract needed fields with defensive checks
        try:
            msg_id = str(getattr(msg, "id", getattr(msg, "pk", None) or getattr(msg, "item_id", None)))
            text = getattr(msg, "text", None)
            user_id = getattr(msg, "user_id", getattr(msg, "user_pk", None) or getattr(msg, "user", None))
            if not msg_id or not text or not user_id:
                return
        except Exception:
            logger.exception("Failed to parse message object")
            return

        if msg_id in self.store.get("processed_ids", []):
            logger.debug("Message %s already processed", msg_id)
            return

        # Mark processed early to avoid duplicates
        self._mark_processed(msg_id)

        # Rate limit per user
        if not self.rate_limiter.allow(str(user_id), self.store.get("replies", {})):
            logger.info("Rate limit reached for user %s, skipping reply", user_id)
            return

        # Send to local API to generate reply
        reply = self._post_to_api(user_id, text)
        if not reply:
            logger.warning("No reply generated for message %s", msg_id)
            return

        # Delay before replying (human-like)
        self._random_sleep(self.cfg.min_reply_delay, self.cfg.max_reply_delay)

        # Send reply via Instagram
        try:
            # prefer using thread id
            thread_id = getattr(thread, "id", getattr(thread, "pk", None) or getattr(thread, "thread_id", None))
            if thread_id:
                logger.info("Sending reply to thread %s", thread_id)
                try:
                    self.client.direct_send(reply, thread_id=thread_id)
                except TypeError:
                    # fallback to user-based send
                    self.client.direct_send(reply, [int(user_id)])
            else:
                logger.info("Sending reply to user %s", user_id)
                self.client.direct_send(reply, [int(user_id)])
            # record reply timestamp
            self._record_reply(str(user_id))
        except Exception:
            logger.exception("Failed to send reply for message %s", msg_id)

    def poll_once(self) -> None:
        try:
            threads = self.client.direct_threads()  # may raise
            logger.debug("Fetched %d threads", len(threads))
            for thread in threads:
                # attempt to get items/messages list
                items = getattr(thread, "items", None) or getattr(thread, "messages", None) or getattr(thread, "items_list", None)
                if not items:
                    continue
                # iterate messages newest first
                for msg in items[:10]:
                    # only consider messages from others
                    owner = getattr(msg, "user_id", getattr(msg, "user_pk", None) or getattr(msg, "user", None))
                    # owner id equals client.user_id? defensive check
                    if str(owner) == str(self.client.user_id):
                        continue
                    self._process_thread_message(thread, msg)
                    if self.stop_event.is_set():
                        return
        except Exception as exc:
            logger.exception("Error during poll: %s", exc)
            # set cooldown for safety on certain errors
            self.cooldown = True

    def run(self) -> None:
        # login first
        try:
            self.login()
        except Exception:
            logger.error("Login failed, entering cooldown mode")
            # Don't continue if we can't login
            return

        logger.info("Starting Instagram polling service")
        # handle signals
        def _handle(signum, frame):
            logger.info("Received signal %s, shutting down", signum)
            self.stop_event.set()

        signal.signal(signal.SIGINT, _handle)
        signal.signal(signal.SIGTERM, _handle)

        while not self.stop_event.is_set():
            if self.cooldown:
                logger.warning("In cooldown mode — sleeping longer")
                time.sleep(60)
                # try to recover by re-login
                try:
                    self.login()
                    self.cooldown = False
                except Exception:
                    logger.warning("Still in cooldown after login attempt")
                    continue

            try:
                self.poll_once()
            except Exception:
                logger.exception("Unexpected error in poll loop")

            # sleep randomized interval
            interval = random.uniform(self.cfg.min_poll, self.cfg.max_poll)
            logger.debug("Sleeping between polls: %.2fs", interval)
            # jittered sleep but check stop_event periodically
            end = time.time() + interval
            while time.time() < end and not self.stop_event.is_set():
                time.sleep(0.5)

        logger.info("InstagramService stopped")


def main() -> None:
    cfg = InstagramServiceConfig()
    # allow override via env vars
    cfg.api_endpoint = os.environ.get("N0X_API_ENDPOINT", cfg.api_endpoint)
    cfg.min_poll = int(os.environ.get("N0X_MIN_POLL", cfg.min_poll))
    cfg.max_poll = int(os.environ.get("N0X_MAX_POLL", cfg.max_poll))
    cfg.min_reply_delay = int(os.environ.get("N0X_MIN_REPLY_DELAY", cfg.min_reply_delay))
    cfg.max_reply_delay = int(os.environ.get("N0X_MAX_REPLY_DELAY", cfg.max_reply_delay))
    cfg.max_replies_per_hour = int(os.environ.get("N0X_MAX_REPLIES_PER_HOUR", cfg.max_replies_per_hour))

    service = InstagramService(cfg)
    service.run()


if __name__ == "__main__":
    main()
