# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from ._compat import string_types
from .models import Album, Artist, Music, PlayList, User


class BaseSource:
    """The base class for musicbox sources.
    It may be subclasseed to create anther source.
    """
    def __init__(self):
        self.session = requests.session()
        self.set_session()

    def set_session(self):
        """Set additional information on requests session"""

    def get_playlists(self, *args, **kwargs):
        """Get playlists from playlist hub.
        To be implemented in subclass.
        """
        raise NotImplementedError

    def get_music(self, id, bind=None):
        """Get music by music id

        :param id: the music id
        :param bind: the binding object to return, create new if is None
        """
        raise NotImplementedError


class NeteaseCloud(BaseSource):
    """http://music.163.com"""

    WEB_ROOT = 'http://music.163.com'
    API_ROOT = WEB_ROOT + '/api'

    PLAYLIST_HUB_URL = WEB_ROOT + '/discover/playlist/'

    SEARCH_URL = API_ROOT + '/search/get/'
    SEARCH_TYPE_MAP = {'music': (1, 'songs'),
                       'album': (10, 'albums'),
                       'artist': (100, 'artists'),
                       'playlist': (1000, 'playlists'),
                       'user': (1002, 'users')}

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
                creator = pl.find('a', class_='nm').string
                yield PlayList(self, id=int(id), title=title,
                               cover_url=cover_url,
                               creator=User(self, creator=creator))
                i += 1
                if i >= maxresults:
                    return
            payload['offset'] += 35

    def search(self, target, type='music', maxresults=None, **kwargs):
        """Search music by target string.

        :param target: the target string
        :param type: music/album/artist/playlist/user
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

    def _build_music_from_json(self, json, **kwargs):
        fields = dict(
            artist=self._build_artist_from_json(json['artists']),
            album=self._build_album_from_json(json['album'], artist=artist),
            id=int(json['id']), name=json['name'],
            duration=json['duration']/1000)
        return Music(self, **fields)

    def _build_album_from_json(self, json, **kwargs):
        fields = dict(
            artist=self._build_artist_from_json(json['artist']),
            company=json.get('company'),
            cover_url=json.get('picUrl'),
            publish_time=build_date(json.get('publishTime')),
            name=json['name'],
            id=int(json['id'])
        )
        # Enable pass artist from caller
        fields.update(kwargs)
        return Album(self, **fields)

    def _build_artist_from_json(self, json, **kwargs):
        if not isinstance(json, list):
            json = [json]
        rv = []
        for item in json:
            cover_url = item.get('picUrl')
            rv .append(Artist(self, id=item['id'], name=item['name'],
                       cover_url=cover_url))
        if len(rv) == 1:
            rv = rv[0]
        return rv
