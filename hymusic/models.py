# -*- coding: utf-8 -*-
"""The ORM models for musicbox objects mapping"""
from __future__ import unicode_literals
from .utils import lazy_property, build_date


class Model(object):
    def __init__(self, source, **kwargs):
        self.source = source
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)

    def match_fields(self, fields):
        """Check if the object match the fields restrictions.
        Only check if the corresponding attribute's name matches.
        """
        for k, v in fields.items():
            if getattr(self, k).name != v:
                return False
        return True

    def parse(self):
        """Parse info from main API"""
        meth = getattr(self.source, 'get_%s' % self.__class__.__name__.lower())
        id = self.source.get_identifier(self)
        meth(id, self)


class Album(Model):

    def __repr__(self):
        return '<Album(%d): %s - %s>' % (self.id, self.name, self.artist.name)

    songs = lazy_property(Model.parse, 'songs')
    cover_url = lazy_property(Model, 'cover_url')


class Artist(Model):

    def __repr__(self):
        return '<Artist(%d): %s>' % (self.id, self.name)

    hot_albums = lazy_property(Model.parse, 'hot_albums')
    cover_url = lazy_property(Model, 'cover_url')


class Song(Model):

    def __repr__(self):
        return '<Song(%d): %s - %s>' % (self.id,
                                        self.name, self.artist.name)

    def download(self, filepath, quality='high'):
        url = self.source.get_song_url(self.id, quality)
        with open(filepath, 'wb') as f:
            f.write(self.source.session.get(url).content)
        print "Download song successfully to %s" % filepath

    def get_lyric(self, type='lyric'):
        return self.source.get_song_lyric(self.id, type)

    @lazy_property
    def comment_count(self):
        self.comment_count = self.source.get_comment_count(self.mid)


class PlayList(Model):

    def __repr__(self):
        return '<Playlist(%d): %s>' % (self.id, self.name)

    songs = lazy_property(Model.parse, 'songs')
    song_count = lazy_property(Model.parse, 'song_count')
    play_count = lazy_property(Model.parse, 'play_count')


class User(Model):

    def __repr__(self):
        return '<User(%d): %s' % (self.id, self.name)
