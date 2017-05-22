import re
import random
from . import BaseSource
from hymusic.utils import build_date, alternative_get
from hymusic._compat import json
from hymusic.models import Album, Artist, Song, PlayList, User


class QQMusic(BaseSource):
    """https://y.qq.com"""
    API_ROOT = 'https://c.y.qq.com'
    REFERER = 'https://y.qq.com/portal/search.html'
    SEARCH_URL = API_ROOT + '/soso/fcgi-bin/search_cp'
    SEARCH_PLAYLIST_URL = (API_ROOT + '/soso/fcgi-bin/'
                           'client_music_search_songlist')

    SONG_URL = API_ROOT + '/v8/fcg-bin/fcg_play_single_song.fcg'
    ALBUM_URL = API_ROOT + '/v8/fcg-bin/fcg_v8_album_info_cp.fcg'
    PLAYLIST_URL = API_ROOT + '/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg'

    def get_identifier(self, object):
        return object.mid

    def set_session(self):
        self.session.headers = {'Host': 'c.y.qq.com'}

    def search(self, target, type='song', maxresults=None, **kwargs):
        """Search song by target string.

        :param target: the target string
        :param type: song/album/artist/playlist/user
        :param maxresults: the max return number of results
        """
        url = self.SEARCH_PLAYLIST_URL if type == 'playlist' else \
            self.SEARCH_URL
        payload = self._build_payload(target, type, maxresults)
        r = self.session.get(url, params=payload,
                             headers={'Referer': self.REFERER})
        try:
            data = r.json()
        except Exception:
            data = json.loads(re.findall(r'.*?(\{.*\}).*', r.text)[0])
        if type == 'playlist':
            data = data['data']['list']
        else:
            data = data['data'][type]['list']
        # return data
        rv = []
        builder = getattr(self, '_build_%s_from_json' % type)
        for result in data:
            item = builder(result)
            if item.match_fields(kwargs):
                rv.append(item)
        return rv

    def get_song(self, song_mid, _bind):
        r = self.session.get(self.SONG_URL, params={'songmid': song_mid,
                                                    'format': 'json'})
        rv = r.json()['data'][0]
        obj = self._build_playlist_from_json(rv)
        if _bind is None:
            return obj
        _bind.__dict__.update(obj.__dict__)
        return _bind

    def get_album(self, album_mid, _bind=None):
        """Get album detailed information by ID"""
        payload = {
            'albummid': album_mid,
            'format': 'json',
            'inCharset': 'utf-8',
            'outCharset': 'utf-8',
            'platform': 'yqq'
        }
        r = self.session.get(self.ALBUM_URL, params=payload,
                             headers={'Referer': self.REFERER})
        rv = r.json()['data']
        obj = self._build_album_from_json(rv)
        if _bind is None:
            return obj
        _bind.__dict__.update(obj.__dict__)
        return _bind

    def get_playlist(self, playlist_id, _bind=None):
        """Get playlist detailed information by ID"""
        payload = dict(
            type=1, json=1, utf8=1, onlysong=1,
            disstid=playlist_id, format='json',
            inCharset='utf-8', outCharset='utf-8', platform='yqq'
        )
        r = self.session.get(self.PLAYLIST_URL, params=payload,
                             headers={'Referer': self.REFERER})
        rv = json.loads(re.findall(r'.*?(\{.*\}).*', r.text)[0])
        obj = self._build_playlist_from_json(rv)
        _bind.__dict__.update(obj.__dict__)
        return _bind

    def _build_payload(self, target, type, maxresults):
        if type == 'song':
            return {'n': maxresults,
                    'w': target,
                    'aggr': 1,
                    'lossless': 1,
                    'cr': 1}
        elif type == 'album':
            return {'remoteplace': 'txt.yqq.album',
                    'searchid': int(random.random()*9655134513451),
                    'lossless': 0,
                    'n': maxresults or 5,
                    'w': target,
                    't': 8,
                    'format': 'json',
                    'inCharset': 'utf-8',
                    'outCharset': 'utf-8',
                    'platform': 'yqq'}
        elif type == 'playlist':
            return {'remoteplace': 'txt.yqq.center',
                    'searchid': int(random.random()*9655134513451),
                    'num_per_page': maxresults,
                    'query': target,
                    'format': 'json',
                    'inCharset': 'utf-8',
                    'outCharset': 'utf-8',
                    'platform': 'yqq'}
        else:
            raise NotImplementedError

    def _build_song_from_json(self, json, **kwargs):
        artist = self._build_artist_from_json(json['singer'])
        if 'album' in json:
            album = self._build_album_from_json(json['album'], artist=artist)
        else:
            album = self._build_album_from_json(json, artist=artist)
        publish_time = json.get('time_public', build_date(json.get('pubtime')))
        fields = {'id': alternative_get(json, 'id', 'songid'),
                  'mid': alternative_get(json, 'mid', 'songmid'),
                  'name': alternative_get(json, 'name', 'songname'),
                  'duration': json['interval'],
                  'publish_time': publish_time,
                  'album': album,
                  'artist': artist}
        fields.update(kwargs)
        return Song(self, **fields)

    def _build_album_from_json(self, json, **kwargs):
        mid = alternative_get(json, 'mid', 'albummid', 'albumMID')
        fields = dict(
            id=alternative_get(json, 'id', 'albumid', 'albumID'),
            mid=mid,
            name=alternative_get(json, 'name', 'albumname', 'albumName'),
            publish_time=build_date(json.get('pubtime')),
            company=json.get('company'),
            cover_url=('https://y.gtimg.cn/music/photo_new/'
                       'T002R500x500M000$%s.jpg' % mid)
        )
        if 'singerID' in json or 'singerid' in json:
            fields['artist'] = self._build_artist_from_json(json)
        if 'list' in json:
            fields['songs'] = [self._build_song_from_json(item)
                               for item in json['list']]
        fields.update(kwargs)
        return Album(self, **fields)

    def _build_artist_from_json(self, json, **kwargs):
        if isinstance(json, list):
            json = json[0]
        fields = dict(
            id=alternative_get(json, 'id', 'singerid', 'singerID'),
            mid=alternative_get(json, 'mid', 'singermid', 'singerMID'),
            name=alternative_get(json, 'name', 'singername', 'singerName')
        )
        fields.update(kwargs)
        return Artist(self, **fields)

    def _build_playlist_from_json(self, json, **kwargs):
        fields = dict(
            id=json['dissid'],
            name=json['dissname'],
            cover_url=json['imgurl'],
            song_count=json['song_count'],
            play_count=json['listennum'],
            creator=self._build_user_from_json(json['creator']))
        fields.update(kwargs)
        if 'songlist' in json:
            fields['songs'] = [self._build_song_from_json(item)
                               for item in json['songlist']]
        return PlayList(self, **fields)

    def _build_user_from_json(self, json, **kwargs):
        fields = dict(id=json['creator_uin'],
                      name=json['name'],
                      avatar_url=json.get('avatarUrl')
                      )
        fields.update(kwargs)
        return User(self, **fields)
