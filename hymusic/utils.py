# -*- coding: utf-8 -*-
import re
import datetime
import hashlib
import base64
from ._compat import json


class lazy_property(object):
    """A property which is evaluated when first access its value, or manually
    set values to it. This is to save the cost of requests.
    """
    def __init__(self, getter, name=None):
        self.getter = getter
        self.name = name or getter.__name__

    def __get__(self, obj, cls):
        if obj is None:
            return self
        if self.name not in obj.__dict__:
            self.getter(obj)
        return obj.__dict__[self.name]

    def __set__(self, obj, val):
        if obj is None:
            return
        obj.__dict__[self.name] = val


def build_date(timeval):
    """Convert a milisecond epic time to human readable format"""
    if not timeval:
        return None
    dtime = datetime.datetime.fromtimestamp(timeval / 1000)
    return dtime.strftime('%Y-%m-%d')


# 歌曲加密算法, 基于https://github.com/yanunon/NeteaseCloudMusic脚本实现
def encrypted_id(id):
    magic = bytearray('3go8&$8*3*3h0k(2)2', 'u8')
    song_id = bytearray(id, 'u8')
    magic_len = len(magic)
    for i, sid in enumerate(song_id):
        song_id[i] = sid ^ magic[i % magic_len]
    m = hashlib.md5(song_id)
    result = m.digest()
    result = base64.b64encode(result)
    result = result.replace(b'/', b'_')
    result = result.replace(b'+', b'-')
    return result.decode('utf-8')


def alternative_get(obj, *keys):
    assert len(keys) > 0
    for key in keys:
        if key in obj:
            return obj.get(key)


def strip_json(text):
    return json.loads(re.findall(r'.*?(\{.*\}).*', text)[0])
