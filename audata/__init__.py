__VERSION_MAJOR__ = '20'
__VERSION_MINOR__ = '03'.lstrip('0')
__VERSION_BUILD__ = '30'.lstrip('0')
__VERSION_TAGS__  = '2217'.lstrip('0')

__VERSION_LIST__ = [
    __VERSION_MAJOR__,
    __VERSION_MINOR__,
    __VERSION_BUILD__,
    __VERSION_TAGS__]

__VERSION__ = '{}.{}.{}b{}'.format(*__VERSION_LIST__)

__DATA_VERSION__ = 1

from .AUFile import AUFile
