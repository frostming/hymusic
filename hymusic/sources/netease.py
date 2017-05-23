# -*- coding: utf-8 -*-
import random
from bs4 import BeautifulSoup
from . import BaseSource
from hymusic._compat import string_types
from hymusic.utils import build_date, encrypted_id
from hymusic.models import Album, Artist, Song, PlayList, User


class NeteaseCloud(BaseSource):
    """http://music.163.com"""

    WEB_ROOT = 'http://music.163.com'
    API_ROOT = WEB_ROOT + '/api'

    PLAYLIST_HUB_URL = WEB_ROOT + '/discover/playlist/'

    SEARCH_URL = API_ROOT + '/search/get/'
    SEARCH_TYPE_MAP = {'song': (1, 'songs'),
                       'album': (10, 'albums'),
                       'artist': (100, 'artists'),
                       'playlist': (1000, 'playlists'),
                       'user': (1002, 'userprofiles')}

    SONG_URL = API_ROOT + '/song/detail/'
    PLAYLIST_URL = API_ROOT + '/playlist/detail'
    ALBUM_URL = API_ROOT + '/album/'
    ARTIST_URL = API_ROOT + '/artist/album/'
    LYRIC_URL = API_ROOT + '/song/lyric'

    def get_identifier(self, object):
        return object.id

    def set_session(self):
        self.session.headers = {'referer': self.WEB_ROOT}

    def get_playlists(self, maxresults=None, cat=None, order=None):
        """Get playlists

        :param maxresults: the max return number, if given None, returns
                            all items.
        :param cat: the playlist category
        :param order: hot/new
        :returns: a generator
        """
        i = 0
        payload = {'cat': cat, 'order': order,
                   'limit': 35, 'offset': 0}
        while maxresults is None or i < maxresults:
            r = self.session.get(self.PLAYLIST_HUB_URL, params=payload)
            soup = BeautifulSoup(r.text, 'lxml')
            results = soup.select('#m-pl-container > li')
            for pl in results:
                cover_url = pl.div.img['src'].split('?')[0]
                title = pl.div.a['title']
                id = pl.div.a['href'].split('id=')[1]
                creator = pl.find('a', class_='nm')
                creator_id = int(creator['href'].split('id=')[1])
                creator_name = creator.string
                yield PlayList(self, id=int(id), title=title,
                               cover_url=cover_url,
                               creator=User(self, name=creator_name,
                                            id=creator_id))
                i += 1
                if maxresults and i >= maxresults:
                    return
            payload['offset'] += 35

    def search(self, target, type='song', maxresults=None, **kwargs):
        """Search song by target string.

        :param target: the target string
        :param type: song/album/artist/playlist/user
        :param maxresults: the max return number of results
        """
        type_code, result_key = self.SEARCH_TYPE_MAP[type]
        payload = {'s': target, 'limit': maxresults,
                   'type': type_code}
        r = self.session.post(self.SEARCH_URL, data=payload)
        rv = []
        builder = getattr(self, '_build_%s_from_json' % type)
        for result in r.json()['result'][result_key]:
            item = builder(result)
            if item.match_fields(kwargs):
                rv.append(item)
        return rv

    def get_song(self, song_id, _bind=None):
        """Get song detailed information by ID"""
        payload = {'id': song_id, 'ids': '[%s]' % song_id}
        r = self.session.get(self.SONG_URL, params=payload)
        rv = r.json()[self.SEARCH_TYPE_MAP['song'][1]][0]
        obj = self._build_song_from_json(rv)
        if _bind is None:
            return obj
        _bind.__dict__.update(obj.__dict__)
        return _bind

    def get_playlist(self, playlist_id, _bind=None):
        """Get playlist detailed information by ID"""
        r = self.session.get(self.PLAYLIST_URL, params={'id': playlist_id})
        rv = r.json()['result']
        obj = self._build_playlist_from_json(rv)
        if _bind is None:
            return obj
        _bind.__dict__.update(obj.__dict__)
        return _bind

    def get_album(self, album_id, _bind=None):
        """Get album detailed information by ID"""
        r = self.session.get(self.ALBUM_URL + str(album_id))
        rv = r.json()['album']
        obj = self._build_album_from_json(rv)
        if _bind is None:
            return obj
        _bind.__dict__.update(obj.__dict__)
        return _bind

    def get_artist(self, artist_id, _bind=None):
        """Get artist detailed information by ID"""
        r = self.session.get(self.ARTIST_URL + str(artist_id))
        rv = r.json()
        obj = self._build_artist_from_json(rv['artist'])
        obj.hot_albums = []
        for album in rv['hotAlbums']:
            obj.hot_albums.append(self._build_album_from_json(album))
        if _bind is None:
            return obj
        _bind.__dict__.update(obj.__dict__)
        return _bind

    # From https://github.com/darknessomi/musicbox/blob/master/NEMbox/api.py#L132
    def get_song_url(self, song_id, quality='high'):
        """Get song url by ID"""
        payload = {'id': song_id, 'ids': '[%s]' % song_id}
        r = self.session.get(self.SONG_URL, params=payload)
        rv = r.json()[self.SEARCH_TYPE_MAP['song'][1]][0]
        if quality == 'high' and rv.get('hMusic'):
            music = rv['hMusic']
        elif quality == 'medium' and rv.get('mMusic'):
            music = rv['mMusic']
        elif quality == 'low' and rv.get('lMusic'):
            music = rv['lMusic']
        else:
            return rv['mp3Url']

        quality = quality + ' {0}k'.format(music['bitrate'] // 1000)
        song_id = str(music['dfsId'])
        enc_id = encrypted_id(song_id)
        url = 'http://m%s.music.126.net/%s/%s.mp3' % (random.randrange(1, 3),
                                                      enc_id, song_id)
        return url

    def get_song_lyric(self, song_id, type='lyric'):
        """Get song lyrics by ID"""
        payload = {'id': song_id, 'lv': -1, 'kv': -1, 'tv': -1}
        rv = self.session.get(self.LYRIC_URL, params=payload).json()
        if type == 'lyric':
            return rv['lrc']['lyric']
        elif type == 'klyric':
            return rv['klyric']['lyric']
        elif type == 'tlyric':
            return rv['tlyric']['lyric']

    def _build_song_from_json(self, json, **kwargs):
        artist = self._build_artist_from_json(json['artists'][0])
        fields = dict(
            artist=artist,
            album=self._build_album_from_json(json['album'], artist=artist),
            id=int(json['id']), name=json['name'],
            duration=json['duration']/1000,
            publish_time=json['album']['publishTime']/1000)
        return Song(self, **fields)

    def _build_album_from_json(self, json, **kwargs):
        fields = dict(
            artist=self._build_artist_from_json(json['artist']),
            company=json.get('company'),
            cover_url=json.get('picUrl'),
            publish_time=build_date(json.get('publishTime')),
            name=json['name'],
            id=int(json['id'])
        )
        if json.get('songs'):
            fields['songs'] = [self._build_song_from_json(item)
                               for item in json['songs']]
        # Enable pass artist from caller
        fields.update(kwargs)
        return Album(self, **fields)

    def _build_artist_from_json(self, json, **kwargs):
        fields = dict(
            id=json['id'],
            name=json['name'],
            cover_url=json.get('picUrl')
        )
        fields.update(kwargs)
        return Artist(self, **fields)

    def _build_playlist_from_json(self, json, **kwargs):
        fields = dict(id=json['id'],
                      name=json['name'],
                      cover_url=json['coverImgUrl'],
                      song_count=json['trackCount'],
                      play_count=json['playCount'],
                      book_count=json.get('bookCount'),
                      shared_count=json.get('sharedCount'),
                      creator=self._build_user_from_json(json['creator']))
        if 'tracks' in json:
            fields['songs'] = [self._build_song_from_json(item)
                               for item in json['tracks']]
        fields.update(kwargs)
        return PlayList(self, **fields)

    def _build_user_from_json(self, json, **kwargs):
        if json.get('gender') is None:
            gender = None
        elif json.get('gender') == 1:
            gender = u'男'
        else:
            gender = u'女'
        fields = dict(id=json['userId'],
                      name=json['nickname'],
                      gender=gender,
                      avatar_url=json.get('avatarUrl'),
                      signature=json.get('signature')
                      )
        fields.update(kwargs)
        return User(self, **fields)
