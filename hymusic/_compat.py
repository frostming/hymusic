import sys


IS_PY3 = sys.version_info[0] == 3

if IS_PY3:
    string_types = str
else:
    string_types = (str, unicode)
