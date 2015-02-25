import tempfile


class Config(object):
    DEBUG = False
    TESTING = False
    THUMBNAIL_STORAGE = tempfile.gettempdir()
