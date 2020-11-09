"""Define version and import high-level objects."""
__VERSION_MAJOR__ = '1'
__VERSION_MINOR__ = '0'
__VERSION_BUILD__ = '3'

__DEBUG = False
if __DEBUG:
    import datetime as dt
    __VERSION_TAGS__ = f"d{dt.datetime.now().strftime('%Y%m%d_%H%M')}"
else:
    __VERSION_TAGS__ = ''

__VERSION__ = f'{__VERSION_MAJOR__}.{__VERSION_MINOR__}.{__VERSION_BUILD__}{__VERSION_TAGS__}'

__DATA_VERSION__ = '1.1'

try:
    from audata.file import File
except ImportError:
    print("Unable to import audata.file.File. If this occurs during initial setup, you may ignore this.")