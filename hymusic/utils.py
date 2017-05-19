# -*- coding: utf-8 -*-


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
        self.getter(obj)
        return obj.__dict__[self.name]

    def __set__(self, obj, val):
        if obj is None:
            return
        obj.__dict__[self.name] = val
