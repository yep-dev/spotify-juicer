import os
import random
from datetime import datetime
from time import sleep

import spotipy
from spotipy import SpotifyOAuth
import redis

auth = SpotifyOAuth(
    username=os.getenv("SPOTIPY_USERNAME"),
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri="http://localhost/",
    scope="user-read-playback-state,user-modify-playback-state",
)
token = auth.get_access_token()

s = spotipy.Spotify(auth=token["access_token"])

r = redis.Redis(host="redis", port=6379, decode_responses=True)

SONG = "song:"
LOG = "log:"

SKIPPED = "skipped"
LISTENED = "listened"


class Ticker:
    def __init__(self):
        self.current = None
        self.song = None
        self.poll()

        self.last = self.song
        self.last_left = None
        self.ticker = 0

    def poll(self):
        self.current = s.current_playback()
        self.song = self.current["item"] if self.current else None

    def tick(self):
        self.poll()
        if self.song and self.song["id"] != self.last["id"]:
            if song_data := r.hgetall(SONG + self.song["id"]):
                skipped = int(song_data["skipped"])
                listened = int(song_data["listened"])
                if random.random() < skipped / (listened + skipped + 1):
                    self.skip()
            else:
                r.hset(
                    SONG + self.song["id"],
                    mapping={"name": self.name(self.song), "listened": 0, "skipped": 0},
                )
                r.json().set(LOG + self.song["id"], ".", {LISTENED: [], SKIPPED: []})

            if self.last_left is not None:
                if self.last_left > 3000:
                    self.log_skipped()
                elif self.last_left < 1000:
                    self.log_listened()

            self.last = self.song

        # store data for the next tick
        self.last_left = (
            self.song and self.song["duration_ms"] - self.current["progress_ms"]
        )
        self.ticker += 1

    def skip(self):
        print(f"auto skip {self.name(self.song)}")
        s.next_track()
        self.tick()

    def log_skipped(self):
        r.json().arrappend(
            LOG + self.last["id"],
            SKIPPED,
            {"id": self.last["id"], "date": int(datetime.now().timestamp())},
        )
        self.recalculate(self.last["id"])
        print(f"skipped {self.name(self.last)}")
        # todo: don't skip on plating something outide playlist
        # todo: don't skip if liked song

    def log_listened(self):
        r.json().arrappend(
            LOG + self.last["id"],
            LISTENED,
            {"id": self.last["id"], "date": int(datetime.now().timestamp())},
        )
        self.recalculate(self.last["id"])
        print(f"listened {self.name(self.last)}")
        # todo: fix duplciating listened sometimes

    def recalculate(self, song_id):
        logs = r.json().get(LOG + song_id)
        r.hset(
            SONG + song_id,
            mapping={
                "listened": str(len(logs["listened"])),
                "skipped": str(len(logs["skipped"])),
            },
        )

    def name(self, song):
        return f"{song['artists'][0]['name']} - {song['name']}"


ticker = Ticker()

while True:
    print("------------")  # todo: print timing between ticks
    ticker.tick()
    sleep(1)

# todo: auto skip short tracks
# todo: auto skip polish tracks from playlists that aren't liked
