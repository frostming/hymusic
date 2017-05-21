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
        meth = getattr(source, '_%s' % self.__class__.__name__.lower())
        meth(self.id, self)


class Album(Model):

    def __repr__(self):
        return '<Album(%d): %s - %s>' % (self.id, self.name, self.artist.name)


class Artist(Model):

    def __repr__(self):
        return '<Artist(%d): %s>' % (self.id, self.name)


class Music(Model):

    def __repr__(self):
        return '<Music(%d): %s - %s>' % (self.id, self.name, self.artist.name)


class PlayList(Model):

    def __repr__(self):
        return '<Playlist(%d): %s>' % (self.id, self.title)


class User:
    pass
