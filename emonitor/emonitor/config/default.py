import tempfile


class Config(object):
    DEBUG = False
    TESTING = False
    THUMBNAIL_STORAGE = tempfile.gettempdir()
    SERVER_EMAIL = ''
    DEMO_RENDERS = ['']
    E404_RENDERS = ['']
    DONATION_BITCOIN_ADDRESS = ''
    BLENDER_BITCOIN_ADDRESS = '17orEh51ab8HoU7g8Ezwcp76jCpeL7PabJ'
    DONATION_PAYPAL_ADDRESS = ''
    BLENDER_PAYPAL_ADDRESS = 'donations@blender.org'
    DONATION_DAY = 4
    DEVHOUR_BITCOIN = 0.02
    DEVHOUR_PAYPAL = 5
