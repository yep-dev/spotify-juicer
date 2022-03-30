import os
from datetime import datetime
from time import sleep

import spotipy
from spotipy import SpotifyOAuth
from tinydb import TinyDB, Query

auth = SpotifyOAuth(username=os.getenv('SPOTIPY_USERNAME'),
                    client_id=os.getenv('SPOTIPY_CLIENT_ID'),
                    client_secret=os.getenv('SPOTIPY_CLIENT_SECRET'),
                    redirect_uri="http://localhost/",
                    scope="user-read-playback-state,user-modify-playback-state")
token = auth.get_access_token()

s = spotipy.Spotify(auth=token['access_token'])

db = TinyDB('./db.json')
skipped = db.table('skipped')
Skippped = Query()
listened = db.table('listened')

current = last = s.current_playback().get('item')
last_left = 0
ticker = 0

while True:
    current = s.current_playback()
    song = None

    if current:
        song = current.get('item')
        print('------------')
        if (skipped.search(Skippped.id == song['id'])):
            print(f"auto skip {song['artists'][0]['name']} - {song['name']}")
            song = None
            s.next_track()

        elif last and song['id'] != last['id']:
            if last_left > 2000:
                skipped.insert({"id": last['id'], "date": int(datetime.now().timestamp())})
                print(f"skipped {last['artists'][0]['name']} - {last['name']}")
                # todo: don't skip on plating something outide playlist
                # todo: don't skip if liked song
                pass

        else:
            last_left = song['duration_ms'] - current['progress_ms']
            if last_left < 1000:
                listened.insert({"id": song['id'], "date": int(datetime.now().timestamp())})
                print(f"listened {song['artists'][0]['name']} - {song['name']}")
                # todo: fix duplciating listened sometimes

    last = song
    ticker += 1
    sleep(1)

# todo: auto skip short tracks
# todo: auto skip polish tracks from playlists that aren't liked
