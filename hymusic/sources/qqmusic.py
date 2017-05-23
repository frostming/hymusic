# -*- coding: utf-8 -*-
import random

from . import BaseSource
from hymusic.utils import build_date, alternative_get, strip_json
from hymusic.models import Album, Artist, Song, PlayList, User


class QQMusic(BaseSource):
    """https://y.qq.com"""
    API_ROOT = 'https://c.y.qq.com'
    REFERER = 'https://y.qq.com/portal/search.html'
    SEARCH_URL = API_ROOT + '/soso/fcgi-bin/search_cp'
    SEARCH_PLAYLIST_URL = (API_ROOT + '/soso/fcgi-bin/'
                           'client_music_search_songlist')

    PLAYLIST_HUB_URL = API_ROOT + '/splcloud/fcgi-bin/fcg_get_diss_by_tag.fcg'
    SONG_URL = API_ROOT + '/v8/fcg-bin/fcg_play_single_song.fcg'
    ALBUM_URL = API_ROOT + '/v8/fcg-bin/fcg_v8_album_info_cp.fcg'
    PLAYLIST_URL = API_ROOT + '/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg'
    ARTIST_URL = API_ROOT + '/v8/fcg-bin/fcg_v8_singer_album.fcg'
    CATEGORY_URL = API_ROOT + '/splcloud/fcgi-bin/fcg_get_diss_tag_conf.fcg'

    def get_identifier(self, object):
        if isinstance(object, PlayList):
            return object.id
        return object.mid

    def set_session(self):
        self.session.headers = {'Host': 'c.y.qq.com',
                                'Referer': self.REFERER}

    def get_playlists(self, maxresults=None, cat=None, order=None):
        """Get playlists

        :param maxresults: the max return number, if given None, returns
                            all items.
        :param cat: the playlist category
        :param order: hot/new
        :returns: a generator
        """
        cat_id = self._get_category_id(cat)
        order_id = 5
        if order == 'new':
            order_id = 2
        payload = {'rnd': random.random(), 'format': 'json', 'platform': 'yqq',
                   'sortId': order_id, 'categoryId': cat_id,
                   'sin': 0, 'ein': 29}
        i = 0
        while maxresults is None or i < maxresults:
            r = self.session.get(self.PLAYLIST_HUB_URL, params=payload)
            data = r.json()['data']['list']
            for item in data:
                yield self._build_playlist_from_json(item)
                i += 1
                if maxresults and i >= maxresults:
                    return
            payload['rnd'] = random.random()
            payload['sin'] += 30
            payload['ein'] += 30

    def search(self, target, type='song', maxresults=None, **kwargs):
        """Search song by target string.

        :param target: the target string
        :param type: song/album/artist/playlist/user
        :param maxresults: the max return number of results
        """
        url = self.SEARCH_PLAYLIST_URL if type == 'playlist' else \
            self.SEARCH_URL
        payload = self._build_payload(target, type, maxresults)
        r = self.session.get(url, params=payload)
        try:
            data = r.json()
        except Exception:
            data = strip_json(r.text)
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
        r = self.session.get(self.ALBUM_URL, params=payload)
        rv = r.json()['data']
        obj = self._build_album_from_json(rv)
        if _bind is None:
            return obj
        _bind.__dict__.update(obj.__dict__)
        return _bind

    def get_playlist(self, playlist_id, _bind=None):
        """Get playlist detailed information by ID"""
        payload = dict(
            type=1, json=1, utf8=1, onlysong=0,
            disstid=playlist_id, format='json',
            inCharset='utf-8', outCharset='utf-8', platform='yqq'
        )
        r = self.session.get(self.PLAYLIST_URL, params=payload)
        rv = strip_json(r.text)['cdlist'][0]
        obj = self._build_playlist_from_json(rv)
        if _bind is None:
            return obj
        _bind.__dict__.update(obj.__dict__)
        return _bind

    def get_artist(self, artist_id, _bind=None):
        """Get playlist detailed information by ID"""
        payload = dict(
            singermid=artist_id, order='time', format='json',
            platform='yqq', inCharset='utf-8', outCharset='utf-8'
        )
        r = self.session.get(self.ARTIST_URL, params=payload)
        rv = strip_json(r.text)['data']
        obj = self._build_artist_from_json(rv)
        if _bind is None:
            return obj
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
                    'num_per_page': maxresults or 5,
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
        mid=alternative_get(json, 'mid', 'singermid', 'singerMID', 'singer_mid')
        fields = dict(
            id=alternative_get(json, 'id', 'singerid', 'singerID', 'singer_id'),
            mid=mid,
            name=alternative_get(json, 'name', 'singername',
                                 'singerName', 'singer_name'),
            cover_url=('https://y.gtimg.cn/music/photo_new/'
                       'T001R300x300M000%s.jpg' % mid)
        )
        if 'list' in json:
            json['hot_albums'] = [self._build_album_from_json(item)
                                  for item in json['list']]
        fields.update(kwargs)
        return Artist(self, **fields)

    def _build_playlist_from_json(self, json, **kwargs):
        if 'creator' in json:
            creator = self._build_user_from_json(json['creator'])
        else:
            creator = self._build_user_from_json(json)
        fields = dict(
            id=int(alternative_get(json, 'disstid', 'dissid')),
            name=json['dissname'],
            cover_url=alternative_get(json, 'logo', 'imgurl'),
            song_count=alternative_get(json, 'total_song_num', 'song_count'),
            play_count=alternative_get(json, 'visitnum', 'listennum'),
            creator=creator)
        fields.update(kwargs)
        if 'songlist' in json:
            fields['songs'] = [self._build_song_from_json(item)
                               for item in json['songlist']]
        return PlayList(self, **fields)

    def _build_user_from_json(self, json, **kwargs):
        fields = dict(id=alternative_get(json, 'uin', 'creator_uin'),
                      name=alternative_get(json, 'name', 'nickname'),
                      avatar_url=json.get('avatarUrl')
                      )
        fields.update(kwargs)
        return User(self, **fields)

    def _get_category_id(self, catname):
        if catname is None:
            return 10000000
        payload = {'format': 'json', 'inCharset': 'utf-8',
                   'outCharset': 'utf-8', 'platform': 'yqq'}
        r = self.session.get(self.CATEGORY_URL, params=payload)
        cats = r.json()['data']['categories']
        for cat in cats:
            for item in cat['items']:
                if catname == item['categoryName']:
                    return item['categoryId']
        raise RuntimeError('Cannot find category "%s"' % catname)
