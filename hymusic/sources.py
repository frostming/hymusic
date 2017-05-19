# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from ._compat import string_types
from .models import Album, Artist, Music, PlayList, Artist


class BaseSource:
    """The base class for musicbox sources.
    It may be subclasseed to create anther source.
    """
    def __init__(self):
        self.session = requests.session()

    def get_top_list(self):
        """Get the top list of popular music, returns a playlist object.
        """
        r = self.session.get(self.TOPLIST_URL)
        if not r.ok:
            return None
        return self.build_playlist(r.text)

    def build_playlist(self, body):
        """Build a playlist from given body.
        """
        raise NotImplementedError


class NeteaseCloud(BaseSource):
    """http://music.163.com"""

    WEB_ROOT = 'http://music.163.com'
    API_ROOT = WEB_ROOT + '/api'
    TOPLIST_URL = WEB_ROOT + '/discover/toplist'

    def _build_playlist_html(self, body):
        # TODO: Analyze the HTTP requests to get a firm method to get top list.
        soup = BeautifulSoup(body, 'lxml')
        payload = {}
        payload['name'] = soup.select('.cnt .hd .f-ff2').string
        payload['cover'] = soup.find('div', class_='cover').img['src']
        payload['creater'] = u'网易云音乐'
        rv = PlayList(self, **payload)

    def _build_playlist_json(self, body):
        pass

    def build_playlist(self, body):
        if isinstance(body, string_types):
            return self._build_playlist_html(body)
        else:
            return self._build_playlist_json(body)
