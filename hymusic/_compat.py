import sys


IS_PY3 = sys.version_info[0] == 3

if IS_PY3:
    from urllib.parse import urlparse
    string_types = str
else:
    from urlparse import urlparse
    string_types = (str, unicode)

try:
    import simplejson as json
except ImportError:
    import json
