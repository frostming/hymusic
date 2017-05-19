# -*- coding: utf-8 -*-
"""The ORM models for musicbox objects mapping"""
from .utils import lazy_property


class Model(object):
    def __init__(self, source, **kwargs):
        self.source = source
        for k, v in kwargs.items():
            setattr(self, k, v)


class Album(Model):
    pass


class Artist(Model):
    pass


class Music(Model):
    pass


class PlayList(Model):
    pass


class User:
    pass
