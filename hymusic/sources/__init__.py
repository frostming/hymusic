import requests


class BaseSource:
    """The base class for songbox sources.
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

    def get_song(self, id, _bind=None):
        """Get song by song id

        :param id: the song id
        :param _bind: the binding object to return, create new if is None
        """
        raise NotImplementedError
